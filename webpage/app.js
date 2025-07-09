// Contract configuration
const CONTRACT_ADDRESS = '0x5FbDB2315678afecb367f032d93F642f64180aa3'; // Replace with the deployed contract address
const CONTRACT_ABI = [
    "function buy(bytes32 codeHash) public payable",
    "function redeem(string memory code) public",
    "function getGiftCardValue(bytes32 codeHash) public view returns (uint256)",
    "function isRedeemed(bytes32 codeHash) public view returns (bool)",
    "function isExpired(bytes32 codeHash) public view returns (bool)", // Bonus: Gift card expiration
    "function getPurchaseTime(bytes32 codeHash) public view returns (uint256)", // Bonus: Gift card expiration
    "function getExpirationTime(bytes32 codeHash) public view returns (uint256)", // Bonus: Gift card expiration
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
const checkBtn = document.getElementById('check-btn'); // Bonus: Gift card expiration
const cardStatus = document.getElementById('card-status'); // Bonus: Gift card expiration

// Wallet management DOM elements
const switchAccountBtn = document.getElementById('switch-account-btn');
const disconnectBtn = document.getElementById('disconnect-btn');

// Switch account function
async function switchAccount() {
    try {
        showStatus('Opening account selection...', 'info');
        
        // Request permission to connect different accounts
        await window.ethereum.request({
            method: 'wallet_requestPermissions',
            params: [{
                eth_accounts: {}
            }]
        });
        
        // Reconnect with the newly selected account
        await connectWallet();
        
        showStatus('Account switched successfully!', 'success');
        
    } catch (error) {
        console.error('Error switching account:', error);
        if (error.code === 4001) {
            showStatus('Account switch cancelled by user', 'info');
        } else {
            showStatus('Failed to switch account. Please try again.', 'error');
        }
    }
}

// Disconnect function
async function disconnectWallet() {
    try {
        // Reset the connection state
        resetWalletConnection();
        showStatus('Wallet disconnected successfully', 'success');
    } catch (error) {
        console.error('Error disconnecting wallet:', error);
        showStatus('Error disconnecting wallet', 'error');
    }
}

// Bonus: Utility functions for expiration handling
function formatExpirationDate(timestamp) {
    const date = new Date(timestamp * 1000); // Convert from seconds to milliseconds
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function getDaysUntilExpiration(expirationTimestamp) {
    const now = Math.floor(Date.now() / 1000); // Current timestamp in seconds
    const secondsUntilExpiration = expirationTimestamp - now;
    return Math.ceil(secondsUntilExpiration / (24 * 60 * 60)); // Convert to days
}

function getTimeUntilExpiration(expirationTimestamp) {
    const now = Math.floor(Date.now() / 1000);
    const secondsUntilExpiration = expirationTimestamp - now;
    
    if (secondsUntilExpiration <= 0) {
        return "Expired";
    }
    
    const days = Math.floor(secondsUntilExpiration / (24 * 60 * 60));
    const hours = Math.floor((secondsUntilExpiration % (24 * 60 * 60)) / (60 * 60));
    const minutes = Math.floor((secondsUntilExpiration % (60 * 60)) / 60);
    
    if (days > 0) {
        return `${days} day(s), ${hours} hour(s)`;
    } else if (hours > 0) {
        return `${hours} hour(s), ${minutes} minute(s)`;
    } else {
        return `${minutes} minute(s)`;
    }
}

// Existing utility functions
function showStatus(message, type = 'info') {
    const statusDiv = document.createElement('div');
    statusDiv.className = `status ${type}`;
    statusDiv.textContent = message;
    statusMessages.innerHTML = '';
    statusMessages.appendChild(statusDiv);
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        if (statusDiv.parentNode) {
            statusDiv.remove();
        }
    }, 5000);
}

function hashCode(code) {
    return ethers.utils.keccak256(ethers.utils.toUtf8Bytes(code));
}

// ENHANCED: Wallet connection functions with button management
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
        
        // Bonus: Enable check button if it exists
        if (checkBtn) {
            checkBtn.disabled = false;
        }

        // Show wallet action buttons
        if (switchAccountBtn) {
            switchAccountBtn.style.display = 'inline-block';
        }
        if (disconnectBtn) {
            disconnectBtn.style.display = 'inline-block';
        }

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

// ENHANCED: Reset wallet connection with button management
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
    
    // Bonus: Disable check button if it exists
    if (checkBtn) {
        checkBtn.disabled = true;
    }
    
    // Hide wallet action buttons
    if (switchAccountBtn) {
        switchAccountBtn.style.display = 'none';
    }
    if (disconnectBtn) {
        disconnectBtn.style.display = 'none';
    }
    
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
        
        // Bonus: Show expiration information in success message
        const expirationTime = await contract.getExpirationTime(codeHash);
        const expirationDate = formatExpirationDate(expirationTime);
        
        showStatus(`Gift card purchased successfully! Transaction confirmed in block ${receipt.blockNumber}. Expires on: ${expirationDate}`, 'success');

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

// Bonus: Enhanced redeem function with expiration checks
async function redeemGiftCard() {
    try {
        const code = document.getElementById('redeem-code').value.trim();

        if (!code) {
            showStatus('Please enter a gift card code', 'error');
            return;
        }

        if (!contract) {
            showStatus('Contract not initialized. Please connect your wallet first.', 'error');
            return;
        }

        showStatus('Checking gift card status...', 'info');
        
        const codeHash = hashCode(code);

        // Check if gift card exists
        const giftCardValue = await contract.getGiftCardValue(codeHash);
        if (giftCardValue.eq(0)) {
            showStatus('Gift card does not exist', 'error');
            return;
        }

        // Check if already redeemed
        const isRedeemed = await contract.isRedeemed(codeHash);
        if (isRedeemed) {
            showStatus('This gift card has already been redeemed', 'error');
            return;
        }

        // Bonus: Check if expired
        const isExpired = await contract.isExpired(codeHash);
        if (isExpired) {
            const expirationTime = await contract.getExpirationTime(codeHash);
            const expirationDate = formatExpirationDate(expirationTime);
            showStatus(`This gift card expired on ${expirationDate}`, 'error');
            return;
        }

        // Bonus: Show expiration warning if close to expiring
        const expirationTime = await contract.getExpirationTime(codeHash);
        const daysUntilExpiration = getDaysUntilExpiration(expirationTime);
        
        if (daysUntilExpiration <= 3 && daysUntilExpiration > 0) {
            const timeRemaining = getTimeUntilExpiration(expirationTime);
            showStatus(`Warning: This gift card expires in ${timeRemaining}`, 'info');
        }

        showStatus('Processing redemption...', 'info');
        redeemBtn.disabled = true;
        redeemBtn.textContent = 'Processing...';

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
        } else if (error.message.includes('expired')) {
            showStatus('This gift card has expired and cannot be redeemed', 'error');
        } else {
            showStatus('Failed to redeem gift card. Please try again.', 'error');
        }
    } finally {
        redeemBtn.disabled = false;
        redeemBtn.textContent = 'Redeem Gift Card';
    }
}

// Bonus: Function to check gift card status
async function checkGiftCardStatus() {
    try {
        const code = document.getElementById('check-code').value.trim();

        if (!code) {
            showStatus('Please enter a gift card code', 'error');
            return;
        }

        if (!contract) {
            showStatus('Contract not initialized. Please connect your wallet first.', 'error');
            return;
        }

        const codeHash = hashCode(code);

        // Get gift card info
        const giftCardValue = await contract.getGiftCardValue(codeHash);
        const isRedeemed = await contract.isRedeemed(codeHash);
        const isExpired = await contract.isExpired(codeHash);
        const purchaseTime = await contract.getPurchaseTime(codeHash);
        const expirationTime = await contract.getExpirationTime(codeHash);

        // Display status
        if (cardStatus) {
            cardStatus.classList.remove('hidden', 'expired', 'expiring-soon', 'valid');

            if (giftCardValue.eq(0)) {
                cardStatus.innerHTML = '<strong>Status:</strong> Gift card does not exist';
                cardStatus.classList.add('expired');
            } else if (isRedeemed) {
                cardStatus.innerHTML = '<strong>Status:</strong> Already redeemed';
                cardStatus.classList.add('expired');
            } else if (isExpired) {
                const expirationDate = formatExpirationDate(expirationTime);
                cardStatus.innerHTML = `
                    <strong>Status:</strong> Expired<br>
                    <strong>Value:</strong> ${ethers.utils.formatEther(giftCardValue)} ETH<br>
                    <strong>Expired on:</strong> ${expirationDate}
                `;
                cardStatus.classList.add('expired');
            } else {
                const valueInEth = ethers.utils.formatEther(giftCardValue);
                const purchaseDate = formatExpirationDate(purchaseTime);
                const expirationDate = formatExpirationDate(expirationTime);
                const timeRemaining = getTimeUntilExpiration(expirationTime);
                const daysUntilExpiration = getDaysUntilExpiration(expirationTime);

                cardStatus.innerHTML = `
                    <strong>Status:</strong> Valid${daysUntilExpiration <= 3 ? ' (Expiring Soon!)' : ''}<br>
                    <strong>Value:</strong> ${valueInEth} ETH<br>
                    <strong>Purchased:</strong> ${purchaseDate}<br>
                    <strong>Expires:</strong> ${expirationDate}<br>
                    <strong>Time remaining:</strong> ${timeRemaining}
                `;
                
                if (daysUntilExpiration <= 3) {
                    cardStatus.classList.add('expiring-soon');
                } else {
                    cardStatus.classList.add('valid');
                }
            }

            cardStatus.classList.remove('hidden');
        }

    } catch (error) {
        console.error('Error checking gift card status:', error);
        showStatus('Failed to check gift card status. Please try again.', 'error');
    }
}

// Event listeners
connectWalletBtn.addEventListener('click', connectWallet);
buyBtn.addEventListener('click', buyGiftCard);
redeemBtn.addEventListener('click', redeemGiftCard);

// Bonus: Add event listener for check button if it exists
if (checkBtn) {
    checkBtn.addEventListener('click', checkGiftCardStatus);
}

// Add event listeners for wallet management buttons
if (switchAccountBtn) {
    switchAccountBtn.addEventListener('click', switchAccount);
}

if (disconnectBtn) {
    disconnectBtn.addEventListener('click', disconnectWallet);
}

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
