import pytest
from web3 import Web3
from web3.exceptions import ContractLogicError
import json
import time

# --- Configurations ---
RPC_URL = "http://127.0.0.1:8545"
CONTRACT_ADDRESS = "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"  # Replace with your deployed address

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
    
    # Check balances (should increase by value for redeemer)
    # Optionally, check events/logs here

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

def test_buy_with_empty_hash_fails(w3, accounts, giftcard):
    buyer = accounts[1]
    empty_hash = b'\x00' * 32  # Empty bytes32
    value = w3.to_wei(0.01, "ether")
    
    with pytest.raises(ContractLogicError):
        tx_hash = giftcard.functions.buy(empty_hash).transact({"from": buyer, "value": value})
        w3.eth.wait_for_transaction_receipt(tx_hash)

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