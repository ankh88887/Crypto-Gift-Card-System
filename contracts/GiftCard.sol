// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

contract GiftCard {
    // Mapping from code hash to gift card value
    mapping(bytes32 => uint256) private giftCards;
    
    // Mapping to track redeemed codes
    mapping(bytes32 => bool) private redeemed;
    
    // Events for logging
    event GiftCardPurchased(bytes32 indexed codeHash, uint256 value, address buyer);
    event GiftCardRedeemed(bytes32 indexed codeHash, uint256 value, address redeemer);
    
    // Minimum gift card value (0.001 ETH)
    uint256 public constant MIN_VALUE = 0.001 ether;
    
    /**
     * @dev Buy a gift card with a unique code hash
     * @param codeHash The hash of the gift card code
     */
    function buy(bytes32 codeHash) public payable {
        require(msg.value >= MIN_VALUE, "Gift card value must be at least 0.001 ETH");
        require(giftCards[codeHash] == 0, "Gift card with this code already exists");
        
        giftCards[codeHash] = msg.value;
        emit GiftCardPurchased(codeHash, msg.value, msg.sender);
    }
    
    /**
     * @dev Redeem a gift card using the original code
     * @param code The original gift card code (not hashed)
     */
    function redeem(string memory code) public {
        bytes32 codeHash = keccak256(abi.encodePacked(code));
        
        require(giftCards[codeHash] > 0, "Gift card does not exist");
        require(!redeemed[codeHash], "Gift card has already been redeemed");
        
        uint256 value = giftCards[codeHash];
        redeemed[codeHash] = true;
        
        // Transfer the gift card value to the redeemer
        payable(msg.sender).transfer(value);
        
        emit GiftCardRedeemed(codeHash, value, msg.sender);
    }
    
    /**
     * @dev Check if a gift card exists and its value
     * @param codeHash The hash of the gift card code
     * @return The value of the gift card (0 if doesn't exist)
     */
    function getGiftCardValue(bytes32 codeHash) public view returns (uint256) {
        return giftCards[codeHash];
    }
    
    /**
     * @dev Check if a gift card has been redeemed
     * @param codeHash The hash of the gift card code
     * @return True if redeemed, false otherwise
     */
    function isRedeemed(bytes32 codeHash) public view returns (bool) {
        return redeemed[codeHash];
    }
}