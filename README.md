# Crypto Gift Card System

A comprehensive blockchain-based gift card system built with Ethereum smart contracts, featuring gift card expiration and advanced wallet management capabilities.

### Features
### Core Functionality
- Buy Gift Cards: Purchase gift cards with unique codes using ETH
- Redeem Gift Cards: Redeem gift cards to receive ETH value
- MetaMask Integration: Seamless wallet connection and transaction handling
- Minimum Value Protection: 0.001 ETH minimum gift card value
- One-time Redemption: Each gift card can only be redeemed once

### Bonus Features
- Gift Card Expiration: Auto-expire after 30 days with comprehensive status tracking
- Wallet Management: Switch accounts and disconnect wallet functionality

## Prerequisites
- Node.js (v16 or higher)
- Python (v3.7 or higher)
- MetaMask browser extension
- Chrome browser (for Selenium tests)

## Setup Instructions

1. Install dependencies: `npm install`
2. Install Python Dependencies: `pip install web3 selenium webdriver-manager pytest`
3. Compile contracts: `npx hardhat compile`
4. Run tests: `npx hardhat test`
5. (Terminal 1) Start local network: `npx hardhat node`
6. (Terminal 2) Deploy Smart Contract: `npx hardhat run scripts/deploy.js --network localhost`
7. (Terminal 3) Start Web Server: `cd webpage`, `python -m http.server 8005`

## Configure MetaMask
### Add Hardhat Local Network:
- Network Name: Hardhat Local
- RPC URL: http://127.0.0.1:8545
- Chain ID: 31337
- Currency Symbol: ETH

### Import Test Account:
- Copy a private key from Hardhat terminal output
- In MetaMask: Account menu → "Import Account"
- Paste the private key
- Verify balance shows ~10,000 ETH

### Manual Contract Address Configuration:
Important: After each contract deployment, you must manually update the contract address in the following files:
- webpage/app.js
- tests/giftcard_test.py
- tests/selenium_tests.py

## Project Structure
- `contracts/` - Smart contracts
- `webpage/` - Frontend application
- `tests/` - Test files
- `scripts/` - Deployment scripts

## Testing
### Smart Contract Tests:
Run all contract tests:
`pytest tests/giftcard_test.py -v`
Run specific test:
`pytest tests/giftcard_test.py::test_buy_and_redeem_success -v`

### Selenium UI Tests:
Run UI tests:
`pytest tests/selenium_tests.py -v`
Run with detailed output:
`pytest tests/selenium_tests.py -v -s`