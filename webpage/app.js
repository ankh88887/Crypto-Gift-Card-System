// Contract configuration
const CONTRACT_ADDRESS = '0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512';
const CONTRACT_ABI = [
    "function buy(bytes32 codeHash) public payable",
    "function redeem(string memory code) public",
    "function getGiftCardValue(bytes32 codeHash) public view returns (uint256)",
    "function isRedeemed(bytes32 codeHash) public view returns (bool)",
    "event GiftCardPurchased(bytes32 indexed codeHash, uint256 value, address buyer)",
    "event GiftCardRedeemed(bytes32 indexed codeHash, uint256 value, address redeemer)"
];

// Global variables
let provider;
let signer;
let contract;
let userAccount;

// DOM elements
const connectWalletBtn = document.getElementById('connect-wallet');
const accountInfo = document.getElementById('account-info');
const accountAddress = document.getElementById('account-address');
const accountBalance = document.getElementById('account-balance');
const statusMessages = document.getElementById('status-messages');
const buyBtn = document.getElementById('buy-btn');
const redeemBtn = document.getElementById('redeem-btn');

// Utility functions
function showStatus(message, type = 'info') {
    const statusDiv = document.createElement('div');
    statusDiv.className = `status ${type}`;
    statusDiv.textContent = message;
    statusMessages.innerHTML = '';
    statusMessages.appendChild(statusDiv);
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        statusDiv.remove();
    }, 5000);
}

function hashCode(code) {
    return ethers.utils.keccak256(ethers.utils.toUtf8Bytes(code));
}

// Wallet connection functions
async function connectWallet() {
    try {
        // Check if MetaMask is installed
        if (typeof window.ethereum === 'undefined') {
            showStatus('MetaMask is not installed. Please install MetaMask to use this app.', 'error');
            return;
        }

        // Request account access
        await window.ethereum.request({ method: 'eth_requestAccounts' });
        
        // Create provider and signer
        provider = new ethers.providers.Web3Provider(window.ethereum);
        signer = provider.getSigner();
        userAccount = await signer.getAddress();

        // Create contract instance
        contract = new ethers.Contract(CONTRACT_ADDRESS, CONTRACT_ABI, signer);

        // Update UI
        await updateAccountInfo();
        connectWalletBtn.textContent = 'Wallet Connected';
        connectWalletBtn.disabled = true;
        accountInfo.classList.remove('hidden');
        buyBtn.disabled = false;
        redeemBtn.disabled = false;

        showStatus('Wallet connected successfully!', 'success');

        // Listen for account changes
        window.ethereum.on('accountsChanged', handleAccountsChanged);
        window.ethereum.on('chainChanged', handleChainChanged);

    } catch (error) {
        console.error('Error connecting wallet:', error);
        showStatus('Failed to connect wallet. Please try again.', 'error');
    }
}

async function updateAccountInfo() {
    try {
        const balance = await provider.getBalance(userAccount);
        const balanceInEth = ethers.utils.formatEther(balance);
        
        accountAddress.textContent = `${userAccount.substring(0, 6)}...${userAccount.substring(38)}`;
        accountBalance.textContent = parseFloat(balanceInEth).toFixed(4);
    } catch (error) {
        console.error('Error updating account info:', error);
    }
}

function handleAccountsChanged(accounts) {
    if (accounts.length === 0) {
        // User disconnected wallet
        resetWalletConnection();
    } else {
        // User switched accounts
        location.reload();
    }
}

function handleChainChanged(chainId) {
    // Reload the page when chain changes
    location.reload();
}

function resetWalletConnection() {
    provider = null;
    signer = null;
    contract = null;
    userAccount = null;
    
    connectWalletBtn.textContent = 'Connect MetaMask Wallet';
    connectWalletBtn.disabled = false;
    accountInfo.classList.add('hidden');
    buyBtn.disabled = true;
    redeemBtn.disabled = true;
    
    showStatus('Wallet disconnected', 'info');
}

// Gift card functions
async function buyGiftCard() {
    try {
        const code = document.getElementById('buy-code').value.trim();
        const amount = document.getElementById('buy-amount').value;

        if (!code) {
            showStatus('Please enter a gift card code', 'error');
            return;
        }

        if (!amount || parseFloat(amount) < 0.001) {
            showStatus('Please enter an amount of at least 0.001 ETH', 'error');
            return;
        }

        showStatus('Processing purchase...', 'info');
        buyBtn.disabled = true;
        buyBtn.textContent = 'Processing...';

        const codeHash = hashCode(code);
        const value = ethers.utils.parseEther(amount);

        // Check if gift card already exists
        const existingValue = await contract.getGiftCardValue(codeHash);
        if (existingValue.gt(0)) {
            showStatus('A gift card with this code already exists', 'error');
            buyBtn.disabled = false;
            buyBtn.textContent = 'Buy Gift Card';
            return;
        }

        // Send transaction
        const tx = await contract.buy(codeHash, { value: value });
        showStatus(`Transaction sent! Hash: ${tx.hash}`, 'info');

        // Wait for confirmation
        const receipt = await tx.wait();
        showStatus(`Gift card purchased successfully! Transaction confirmed in block ${receipt.blockNumber}`, 'success');

        // Clear form
        document.getElementById('buy-code').value = '';
        document.getElementById('buy-amount').value = '';

        // Update balance
        await updateAccountInfo();

    } catch (error) {
        console.error('Error buying gift card:', error);
        if (error.code === 4001) {
            showStatus('Transaction cancelled by user', 'error');
        } else if (error.message.includes('insufficient funds')) {
            showStatus('Insufficient funds for this transaction', 'error');
        } else {
            showStatus('Failed to buy gift card. Please try again.', 'error');
        }
    } finally {
        buyBtn.disabled = false;
        buyBtn.textContent = 'Buy Gift Card';
    }
}

async function redeemGiftCard() {
    try {
        const code = document.getElementById('redeem-code').value.trim();

        if (!code) {
            showStatus('Please enter a gift card code', 'error');
            return;
        }

        showStatus('Processing redemption...', 'info');
        redeemBtn.disabled = true;
        redeemBtn.textContent = 'Processing...';

        const codeHash = hashCode(code);

        // Check if gift card exists
        const giftCardValue = await contract.getGiftCardValue(codeHash);
        if (giftCardValue.eq(0)) {
            showStatus('Gift card does not exist', 'error');
            redeemBtn.disabled = false;
            redeemBtn.textContent = 'Redeem Gift Card';
            return;
        }

        // Check if already redeemed
        const isRedeemed = await contract.isRedeemed(codeHash);
        if (isRedeemed) {
            showStatus('This gift card has already been redeemed', 'error');
            redeemBtn.disabled = false;
            redeemBtn.textContent = 'Redeem Gift Card';
            return;
        }

        // Send transaction
        const tx = await contract.redeem(code);
        showStatus(`Transaction sent! Hash: ${tx.hash}`, 'info');

        // Wait for confirmation
        const receipt = await tx.wait();
        const valueInEth = ethers.utils.formatEther(giftCardValue);
        showStatus(`Gift card redeemed successfully! You received ${valueInEth} ETH. Transaction confirmed in block ${receipt.blockNumber}`, 'success');

        // Clear form
        document.getElementById('redeem-code').value = '';

        // Update balance
        await updateAccountInfo();

    } catch (error) {
        console.error('Error redeeming gift card:', error);
        if (error.code === 4001) {
            showStatus('Transaction cancelled by user', 'error');
        } else {
            showStatus('Failed to redeem gift card. Please try again.', 'error');
        }
    } finally {
        redeemBtn.disabled = false;
        redeemBtn.textContent = 'Redeem Gift Card';
    }
}

// Event listeners
connectWalletBtn.addEventListener('click', connectWallet);
buyBtn.addEventListener('click', buyGiftCard);
redeemBtn.addEventListener('click', redeemGiftCard);

// Initialize app
window.addEventListener('load', async () => {
    // Check if already connected
    if (typeof window.ethereum !== 'undefined') {
        try {
            const accounts = await window.ethereum.request({ method: 'eth_accounts' });
            if (accounts.length > 0) {
                await connectWallet();
            }
        } catch (error) {
            console.error('Error checking existing connection:', error);
        }
    }
});