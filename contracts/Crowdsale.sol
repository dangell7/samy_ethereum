pragma solidity ^0.4.18;

import "./SafeMath.sol";
import "./RefundVault.sol";
import "./ERC20Basic.sol";
import "./SafeERC20.sol";



contract Crowdsale is Ownable {

    using SafeERC20 for ERC20Basic;
    using SafeMath for uint256;

    address public beneficiary;
    uint256 public fundingGoal;
    uint256 public cap;
    uint256 public weiAmountRaised;
    uint256 public rate;
    uint256 public startTime;
    uint256 public endTime;
    uint256 public bonusEnd;
    uint256 public bonus;

    ERC20Basic public token;

    RefundVault public vault;
    bool public isFinalized = false;

    event FundContribution(address backer, uint256 weiAmount, bool isContribution);

    event Finalized(bool isFinalized);

    function Crowdsale(
        address _beneficiary,
        uint256 _fundingGoal,
        uint256 _cap,
        uint256 _rate,
        uint256 _startTime,
        uint256 _endTime,
        uint256 _bonusEnd,
        uint256 _bonus,
        ERC20Basic _token
    ) {
        require(_fundingGoal > 0);
        require(_cap > 0);
        beneficiary = _beneficiary;
        fundingGoal = _fundingGoal;
        cap = _cap;
        rate = _rate;
        startTime = _startTime;
        endTime = now + _endTime * 1 minutes;
        bonusEnd = _bonusEnd;
        bonus = _bonus;
        token = _token;
        vault = new RefundVault(beneficiary);
    }

    function makeTransfer(address _to, uint256 tokens) public payable {
        token.safeTransfer(_to, tokens);
        FundContribution(_to, tokens, true);
    }

    function () external payable {
        require(msg.sender != address(0));
        require(validPurchase());
        require(!hasEnded());
        uint256 weiAmount = msg.value;
        if (now >= startTime && now <= bonusEnd) {
            uint256 weiBonus = weiAmount.div(bonus);
            weiAmount = weiAmount.add(weiBonus);
        }
        uint256 tokens = weiAmount.mul(rate);
        address _to = msg.sender;
        weiAmountRaised = weiAmountRaised.add(msg.value);
        makeTransfer(_to, tokens);
        forwardFunds();
    }

    function forwardFunds() internal {
        vault.deposit.value(msg.value)(msg.sender);
    }

    function sendRefunds() onlyOwner {
        require(isFinalized);
        require(!goalReached());
        vault.refund();
    }

    function finalization() onlyOwner public {

        require(!isFinalized);
        require(hasEnded());

        Finalized(isFinalized);

        if (goalReached()) {
          vault.close();
        } else {
          vault.enableRefunds();
        }
        transferRemaining();
        //burnRemaining();
        isFinalized = true;
    }

    function goalReached() public view returns (bool) {
        return weiAmountRaised >= fundingGoal;
    }

    function hasEnded() public view returns (bool) {
        bool capReached = weiAmountRaised >= cap;
        return now >= endTime || capReached;
    }

    function burnRemaining() onlyOwner {
        uint256 amount = token.balanceOf(this);
        token.burn(amount);
    }

    function transferRemaining() onlyOwner {
        address to = msg.sender;
        uint256 amount = token.balanceOf(this);
        token.safeTransfer(to, amount);
    }

    function validPurchase() internal view returns (bool) {
        bool withinCap = weiAmountRaised.add(msg.value) <= cap;
        bool aboveMinimumPurchase = msg.value >= 10000000000000000;
        return withinCap && aboveMinimumPurchase;
    }
}

