// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract DeviceRegistry {
    address public owner;
    mapping(string => bytes32) public deviceHash;

    event DeviceRegistered(string deviceId, bytes32 tokenHash, address who);

    constructor() {
        owner = msg.sender;
    }

    function registerDevice(string calldata deviceId, bytes32 tokenHash) external {
        deviceHash[deviceId] = tokenHash;
        emit DeviceRegistered(deviceId, tokenHash, msg.sender);
    }

    function verify(string calldata deviceId, bytes32 tokenHash) external view returns (bool) {
        return deviceHash[deviceId] == tokenHash;
    }
}
