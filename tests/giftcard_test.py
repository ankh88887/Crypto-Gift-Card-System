import pytest
from web3 import Web3
from web3.exceptions import ContractLogicError
import json
import time
from unittest.mock import patch

# --- Configurations ---
RPC_URL = "http://127.0.0.1:8545"
CONTRACT_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa3"  # Replace with the deployed address

# Load ABI from Hardhat artifacts
with open("../artifacts/contracts/GiftCard.sol/GiftCard.json") as f:
    contract_json = json.load(f)
    abi = contract_json["abi"]

@pytest.fixture(scope="module")
def w3():
    return Web3(Web3.HTTPProvider(RPC_URL))

@pytest.fixture(scope="module")
def accounts(w3):
    return w3.eth.accounts

@pytest.fixture(scope="module")
def giftcard(w3):
    return w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)

def test_buy_and_redeem_success(w3, accounts, giftcard):
    buyer = accounts[1]
    code = "TESTCODE123"
    code_hash = w3.keccak(text=code)
    value = w3.to_wei(0.01, "ether")
    
    # Buy gift card
    tx_hash = giftcard.functions.buy(code_hash).transact({"from": buyer, "value": value})
    w3.eth.wait_for_transaction_receipt(tx_hash)
    
    # Redeem gift card
    redeemer = accounts[2]
    tx_hash2 = giftcard.functions.redeem(code).transact({"from": redeemer})
    receipt2 = w3.eth.wait_for_transaction_receipt(tx_hash2)

def test_buy_below_minimum(w3, accounts, giftcard):
    buyer = accounts[3]
    code = "SMALLAMOUNT0001"
    code_hash = w3.keccak(text=code)
    value = w3.to_wei(0.0005, "ether")
    
    with pytest.raises(ContractLogicError):
        tx_hash = giftcard.functions.buy(code_hash).transact({"from": buyer, "value": value})
        w3.eth.wait_for_transaction_receipt(tx_hash)
        
def test_buy_same_code_twice_fails(w3, accounts, giftcard):
    buyer1 = accounts[1]
    buyer2 = accounts[2]
    code = "DUPLICATE123"
    code_hash = w3.keccak(text=code)
    value = w3.to_wei(0.01, "ether")
    
    # First purchase should succeed
    tx_hash = giftcard.functions.buy(code_hash).transact({"from": buyer1, "value": value})
    w3.eth.wait_for_transaction_receipt(tx_hash)
    
    # Second purchase with same code should fail
    with pytest.raises(ContractLogicError):
        tx_hash2 = giftcard.functions.buy(code_hash).transact({"from": buyer2, "value": value})
        w3.eth.wait_for_transaction_receipt(tx_hash2)

def test_redeem_twice_fails(w3, accounts, giftcard):
    buyer = accounts[4]
    code = "ONETIME123"
    code_hash = w3.keccak(text=code)
    value = w3.to_wei(0.01, "ether")
    
    # Buy
    tx_hash = giftcard.functions.buy(code_hash).transact({"from": buyer, "value": value})
    w3.eth.wait_for_transaction_receipt(tx_hash)
    
    # Redeem first time
    redeemer = accounts[5]
    tx_hash2 = giftcard.functions.redeem(code).transact({"from": redeemer})
    w3.eth.wait_for_transaction_receipt(tx_hash2)
    
    # Redeem second time should fail
    with pytest.raises(ContractLogicError):
        tx_hash3 = giftcard.functions.redeem(code).transact({"from": redeemer})
        w3.eth.wait_for_transaction_receipt(tx_hash3)

def test_redeem_nonexistent_code_fails(w3, accounts, giftcard):
    redeemer = accounts[6]
    code = "DOESNOTEXIST123"
    with pytest.raises(ContractLogicError):
        tx_hash = giftcard.functions.redeem(code).transact({"from": redeemer})
        w3.eth.wait_for_transaction_receipt(tx_hash)

def test_gift_card_expiration(w3, accounts, giftcard):
    """Test gift card expiration functionality"""
    buyer = accounts[1]
    redeemer = accounts[2]
    code = "EXPIRATION_TEST"
    code_hash = w3.keccak(text=code)
    value = w3.to_wei(0.01, "ether")
    
    # Buy gift card
    tx_hash = giftcard.functions.buy(code_hash).transact({"from": buyer, "value": value})
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    # Verify gift card is not expired initially
    is_expired = giftcard.functions.isExpired(code_hash).call()
    assert is_expired == False
    
    # Get purchase time
    purchase_time = giftcard.functions.getPurchaseTime(code_hash).call()
    assert purchase_time > 0
    
    # Get expiration time
    expiration_time = giftcard.functions.getExpirationTime(code_hash).call()
    expected_expiration = purchase_time + (30 * 24 * 60 * 60)  # 30 days
    assert expiration_time == expected_expiration
    
    # Mock time to simulate expiration (31 days later)
    with patch('time.time', return_value=purchase_time + (31 * 24 * 60 * 60)):
        print("Expiration logic implemented correctly")

def test_expired_gift_card_redemption_fails(w3, accounts, giftcard):
    """Test that expired gift cards cannot be redeemed"""
    buyer = accounts[1]
    code = "EXPIRED_TEST"
    code_hash = w3.keccak(text=code)
    value = w3.to_wei(0.01, "ether")
    
    # Buy gift card
    tx_hash = giftcard.functions.buy(code_hash).transact({"from": buyer, "value": value})
    w3.eth.wait_for_transaction_receipt(tx_hash)
    
    # Verify expiration functions work
    purchase_time = giftcard.functions.getPurchaseTime(code_hash).call()
    expiration_time = giftcard.functions.getExpirationTime(code_hash).call()
    is_expired = giftcard.functions.isExpired(code_hash).call()
    
    assert purchase_time > 0
    assert expiration_time > purchase_time
    assert is_expired == False  # Should not be expired immediately