pragma solidity ^0.4.18;


import "./ERC20Basic.sol";
import "./SafeERC20.sol";
import "./SafeMath.sol";
import "./Ownable.sol";


/**
 * @title Samy Campaign Contract
 * @dev Samy Campaign Contract
 */
contract SamyCampaign is Ownable {

    using SafeERC20 for ERC20Basic;
    using SafeMath for uint256;

    enum State {
        Pending,
        Approved,
        Denied,
        Scheduled,
        Published,
        Completed
    }

    bool public isDisbursed = false;
    bool public isRefunded = false;
    bool public reviewChoice = false;

    ERC20Basic public token;

    address public ambassador;
    address public brand;


    modifier onlyAmbassador() {
        require(msg.sender == ambassador);
        _;
    }

    modifier onlyBrand() {
        if (!reviewChoice) {
            require(msg.sender == brand);
            _;
        }
    }

    function SamyCampaign(ERC20Basic _token, address _ambassador, address _brand, bool _reviewChoice) public {
        token = _token;
        ambassador = _ambassador;
        brand = _brand;
        reviewChoice = _reviewChoice;
        State = Pending;
    }

    function approved() onlyBrand {
        require(State == Pending);
        State = Approved;
    }

    function scheduled() public {
        require(State == Approved);
        State = Scheduled;
    }

    function published() onlyAmbassador {
        require(State == Approved || State == Scheduled);
        State = Published;
    }

    function completed() onlyOwner {
        require(State == Published);
        State = Completed;
        releaseFunds();
    }

    function releaseFunds() onlyOwner {
        require(State == Completed);
        require(!isDisbursed);
        uint256 amount = token.balanceOf(this);
        token.safeTransfer(ambassador, amount);
        isDisbursed = true;
    }

    function refundFunds() onlyBrand {
        require(State == Pending);
        require(!isRefunded);
        uint256 amount = token.balanceOf(this);
        token.safeTransfer(brand, amount);
        isRefunded = true;
    }


}