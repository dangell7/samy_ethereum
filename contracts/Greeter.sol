pragma solidity ^0.4.18;

contract Greeter {
    string public greeting;
    event Test(address greeter, string greeting);

    function Greeter() {
        greeting = "Hello";
    }

    function setGreeting(string _greeting) public {
        greeting = _greeting;
        Test(msg.sender, greeting);
    }

    function greet() constant returns (string) {
        return greeting;
    }
}