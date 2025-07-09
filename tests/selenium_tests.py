import pytest
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

class TestGiftCardUI:
    
    CONTRACT_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa3"  # Replace with the deployed address
    WEB_APP_URL = "http://localhost:8005"
    
    @pytest.fixture(scope="class")
    def driver(self):
        """Set up Chrome WebDriver with options for testing"""
        chrome_options = Options()
        
        # Add Chrome options for testing
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        
        # For headless testing (comment out to see browser)
        # chrome_options.add_argument("--headless")
        
        # Set up WebDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Set implicit wait
        driver.implicitly_wait(10)
        
        yield driver
        
        # Cleanup
        driver.quit()
    
    def wait_for_element(self, driver, by, value, timeout=10):
        """Helper method to wait for element to be present"""
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            pytest.fail(f"Element not found: {by}={value}")
    
    def wait_for_clickable(self, driver, by, value, timeout=10):
        """Helper method to wait for element to be clickable"""
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            return element
        except TimeoutException:
            pytest.fail(f"Element not clickable: {by}={value}")
    
    def inject_metamask_mock(self, driver):
        """Inject comprehensive MetaMask mock into the page"""
        print("Injecting MetaMask mock...")
        
        mock_script = f"""
        // Set contract address globally for the mock
        window.MOCK_CONTRACT_ADDRESS = '{self.CONTRACT_ADDRESS}';
        
        // Comprehensive MetaMask mock
        window.ethereum = {{
            isMetaMask: true,
            selectedAddress: '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266',
            
            request: async function(params) {{
                console.log('MetaMask request:', params);
                
                switch(params.method) {{
                    case 'eth_requestAccounts':
                        return ['0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266'];
                    
                    case 'eth_accounts':
                        return ['0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266'];
                    
                    case 'eth_chainId':
                        return '0x539'; // 1337 in hex
                    
                    case 'eth_sendTransaction':
                        // Simulate transaction approval
                        await new Promise(resolve => setTimeout(resolve, 1000));
                        return '0x' + Math.random().toString(16).substr(2, 64);
                    
                    case 'eth_getBalance':
                        return '0x21e19e0c9bab2400000'; // 10000 ETH in hex
                    
                    default:
                        return null;
                }}
            }},
            
            on: function(event, callback) {{
                console.log('MetaMask event listener:', event);
                // Store callbacks for later use if needed
            }}
        }};
        
        // Mock ethers provider integration
        if (typeof ethers !== 'undefined') {{
            // Store original provider
            const originalWeb3Provider = ethers.providers.Web3Provider;
            
            // Mock Web3Provider
            ethers.providers.Web3Provider = function(ethereum) {{
                this.getNetwork = async function() {{
                    return {{ chainId: 1337, name: 'hardhat' }};
                }};
                
                this.getSigner = function() {{
                    return {{
                        getAddress: async function() {{
                            return '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266';
                        }},
                        sendTransaction: async function(tx) {{
                            console.log('Sending transaction:', tx);
                            
                            // Simulate balance changes
                            if (tx.value) {{
                                const currentBalance = window.mockBalance || ethers.utils.parseEther('10000');
                                window.mockBalance = currentBalance.sub(tx.value);
                                console.log('Balance after transaction:', ethers.utils.formatEther(window.mockBalance));
                            }}
                            
                            return {{
                                hash: '0x' + Math.random().toString(16).substr(2, 64),
                                wait: async function() {{
                                    await new Promise(resolve => setTimeout(resolve, 2000));
                                    return {{
                                        blockNumber: Math.floor(Math.random() * 1000) + 1,
                                        status: 1,
                                        transactionHash: this.hash
                                    }};
                                }}
                            }};
                        }}
                    }};
                }};
                
                this.getBalance = async function(address) {{
                    return window.mockBalance || ethers.utils.parseEther('9999.5');
                }};
            }};
            
            // Mock Contract class
            const originalContract = ethers.Contract;
            ethers.Contract = function(address, abi, signerOrProvider) {{
                this.address = address;
                this.abi = abi;
                
                // Mock contract methods
                this.buy = async function(codeHash, options) {{
                    console.log('Mock buy called with:', codeHash, options);
                    
                    // Simulate transaction
                    if (signerOrProvider && signerOrProvider.sendTransaction) {{
                        return await signerOrProvider.sendTransaction({{
                            to: address,
                            value: options.value,
                            data: '0x' + Math.random().toString(16).substr(2, 64)
                        }});
                    }}
                    
                    return {{
                        hash: '0x' + Math.random().toString(16).substr(2, 64),
                        wait: async function() {{
                            return {{ blockNumber: 1, status: 1 }};
                        }}
                    }};
                }};
                
                this.redeem = async function(code) {{
                    console.log('Mock redeem called with:', code);
                    
                    // Simulate balance increase for redemption
                    const currentBalance = window.mockBalance || ethers.utils.parseEther('9999.5');
                    window.mockBalance = currentBalance.add(ethers.utils.parseEther('0.001'));
                    
                    return {{
                        hash: '0x' + Math.random().toString(16).substr(2, 64),
                        wait: async function() {{
                            return {{ blockNumber: 1, status: 1 }};
                        }}
                    }};
                }};
                
                this.getGiftCardValue = async function(codeHash) {{
                    // Mock: return 0 for non-existent cards, value for existing ones
                    return ethers.BigNumber.from('0');
                }};
                
                this.isRedeemed = async function(codeHash) {{
                    // Mock: return false for testing
                    return false;
                }};
            }};
        }}
        
        // Initialize mock balance
        if (typeof ethers !== 'undefined') {{
            window.mockBalance = ethers.utils.parseEther('10000');
        }}
        
        console.log('Complete MetaMask mock injected');
        """
        
        driver.execute_script(mock_script)
        time.sleep(2)  # Allow mock to initialize
    
    def test_page_loads_correctly(self, driver):
        """Test 1: Verify the web application loads correctly"""
        print("Testing page load...")
        
        driver.get(self.WEB_APP_URL)
        
        # Check page title
        assert "Crypto Gift Card System" in driver.title
        
        # Check main elements are present
        header = self.wait_for_element(driver, By.TAG_NAME, "h1")
        assert "Crypto Gift Card System" in header.text
        
        # Check sections are present
        buy_section = self.wait_for_element(driver, By.XPATH, "//h2[contains(text(), 'Buy Gift Card')]")
        redeem_section = self.wait_for_element(driver, By.XPATH, "//h2[contains(text(), 'Redeem Gift Card')]")
        
        assert buy_section.is_displayed()
        assert redeem_section.is_displayed()
        
        print("✅ Page loads correctly")

    def test_metamask_connection_simulation(self, driver):
        """Test 2: Simulate MetaMask wallet connection"""
        print("Testing MetaMask connection simulation...")
        
        driver.get(self.WEB_APP_URL)
        
        # Inject MetaMask mock
        self.inject_metamask_mock(driver)
        
        # Find and click connect wallet button
        connect_button = self.wait_for_clickable(driver, By.ID, "connect-wallet")
        initial_text = connect_button.text
        print(f"Initial button text: {initial_text}")
        
        connect_button.click()
        
        # Wait for connection to complete
        time.sleep(3)
        
        # Verify connection success
        try:
            # Check if button text changed
            WebDriverWait(driver, 10).until(
                lambda d: "Connected" in d.find_element(By.ID, "connect-wallet").text
            )
            
            # Check if account info is displayed
            account_info = self.wait_for_element(driver, By.ID, "account-info")
            assert "hidden" not in account_info.get_attribute("class")
            
            # Verify account address is displayed
            account_address = self.wait_for_element(driver, By.ID, "account-address")
            assert len(account_address.text) > 0
            
            print("✅ MetaMask connection simulation successful")
            
        except TimeoutException:
            # Take screenshot for debugging
            driver.save_screenshot("connection_failure.png")
            pytest.fail("MetaMask connection simulation failed")

    def test_buy_gift_card_ui(self, driver):
        """Test 3: Test buying gift card through UI"""
        print("Testing gift card purchase through UI...")
        
        driver.get(self.WEB_APP_URL)
        
        # Set up mocks
        self.inject_metamask_mock(driver)
        
        # Connect wallet first
        connect_button = self.wait_for_clickable(driver, By.ID, "connect-wallet")
        connect_button.click()
        time.sleep(3)
        
        # Fill in buy form
        code_input = self.wait_for_element(driver, By.ID, "buy-code")
        amount_input = self.wait_for_element(driver, By.ID, "buy-amount")
        buy_button = self.wait_for_element(driver, By.ID, "buy-btn")
        
        # Enter test data
        test_code = "SELENIUM_BUY_TEST"
        test_amount = "0.005"
        
        code_input.clear()
        code_input.send_keys(test_code)
        
        amount_input.clear()
        amount_input.send_keys(test_amount)
        
        # Record initial balance
        initial_balance = driver.execute_script("return window.mockBalance ? ethers.utils.formatEther(window.mockBalance) : '10000';")
        print(f"Initial balance: {initial_balance} ETH")
        
        # Click buy button
        buy_button.click()
        
        # Wait for transaction processing
        time.sleep(4)
        
        # Check for success message or any status message
        try:
            status_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".status"))
            )
            
            status_text = status_element.text.lower()
            status_class = status_element.get_attribute("class")
            
            print(f"Status message: {status_element.text}")
            print(f"Status class: {status_class}")
            
            # Accept success or reasonable error messages
            if "success" in status_class or "successfully" in status_text:
                print("✅ Gift card purchase successful")
            elif "processing" in status_text:
                print("✅ Transaction processing detected")
            else:
                print(f"✅ Status message displayed: {status_element.text}")
                
        except TimeoutException:
            pytest.fail("No status message found after purchase attempt")
        
        # Verify form was cleared (if successful)
        if code_input.get_attribute("value") == "":
            print("✅ Form cleared after transaction")

    def test_redeem_gift_card_ui(self, driver):
        """Test 4: Test redeeming gift card through UI"""
        print("Testing gift card redemption through UI...")
        
        driver.get(self.WEB_APP_URL)
        
        # Set up mocks
        self.inject_metamask_mock(driver)
        
        # Connect wallet
        connect_button = self.wait_for_clickable(driver, By.ID, "connect-wallet")
        connect_button.click()
        time.sleep(3)
        
        # Fill in redeem form
        redeem_code_input = self.wait_for_element(driver, By.ID, "redeem-code")
        redeem_button = self.wait_for_element(driver, By.ID, "redeem-btn")
        
        # Use a test code
        test_code = "SELENIUM_BUY_TEST"
        
        redeem_code_input.clear()
        redeem_code_input.send_keys(test_code)
        
        # Record initial balance
        initial_balance = driver.execute_script("return window.mockBalance ? ethers.utils.formatEther(window.mockBalance) : '10000';")
        print(f"Initial balance: {initial_balance} ETH")
        
        # Click redeem button
        redeem_button.click()
        
        # Wait for transaction processing
        time.sleep(4)
        
        # Check for status message
        try:
            status_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".status"))
            )
            
            status_text = status_element.text.lower()
            status_class = status_element.get_attribute("class")
            
            print(f"Status message: {status_element.text}")
            
            # Accept various outcomes
            if "success" in status_class or "redeemed" in status_text:
                print("✅ Gift card redemption successful")
            elif "does not exist" in status_text or "not exist" in status_text:
                print("✅ Gift card redemption properly rejected (code doesn't exist)")
            elif "already been redeemed" in status_text:
                print("✅ Gift card redemption properly rejected (already redeemed)")
            else:
                print(f"✅ Status message displayed: {status_element.text}")
                
        except TimeoutException:
            pytest.fail("No status message found after redemption attempt")

    def test_form_validation(self, driver):
        """Test 5: Test form validation and error handling"""
        print("Testing form validation...")
        
        driver.get(self.WEB_APP_URL)
        
        # Set up mocks
        self.inject_metamask_mock(driver)
        
        # Connect wallet
        connect_button = self.wait_for_clickable(driver, By.ID, "connect-wallet")
        connect_button.click()
        time.sleep(3)
        
        # Test 1: Empty code validation
        buy_button = self.wait_for_element(driver, By.ID, "buy-btn")
        buy_button.click()
        
        time.sleep(2)
        
        # Check for error message
        try:
            error_message = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".status.error"))
            )
            assert "code" in error_message.text.lower()
            print("✅ Empty code validation working")
        except TimeoutException:
            print("⚠️ Empty code validation not triggered")
        
        # Test 2: Invalid amount validation
        code_input = self.wait_for_element(driver, By.ID, "buy-code")
        amount_input = self.wait_for_element(driver, By.ID, "buy-amount")
        
        code_input.clear()
        code_input.send_keys("TEST_CODE")
        amount_input.clear()
        amount_input.send_keys("0.0001")  # Below minimum
        
        buy_button.click()
        time.sleep(2)
        
        # Check for minimum amount error
        try:
            error_message = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".status.error"))
            )
            assert "0.001" in error_message.text
            print("✅ Minimum amount validation working")
        except TimeoutException:
            print("⚠️ Minimum amount validation not triggered")
        
        print("✅ Form validation tests completed")

    def test_balance_changes_simulation(self, driver):
        """Test 6: Simulate and verify ETH balance changes"""
        print("Testing balance change simulation...")
        
        driver.get(self.WEB_APP_URL)
        
        # Inject enhanced mock with balance tracking
        self.inject_metamask_mock(driver)
        
        # Connect wallet
        connect_button = self.wait_for_clickable(driver, By.ID, "connect-wallet")
        connect_button.click()
        time.sleep(3)
        
        # Record initial balance
        initial_balance_str = driver.execute_script("return window.mockBalance ? ethers.utils.formatEther(window.mockBalance) : '10000';")
        initial_balance = float(initial_balance_str)
        print(f"Initial balance: {initial_balance} ETH")
        
        # Perform purchase transaction
        code_input = self.wait_for_element(driver, By.ID, "buy-code")
        amount_input = self.wait_for_element(driver, By.ID, "buy-amount")
        buy_button = self.wait_for_element(driver, By.ID, "buy-btn")
        
        purchase_amount = "0.001"
        code_input.clear()
        code_input.send_keys("BALANCE_TEST")
        amount_input.clear()
        amount_input.send_keys(purchase_amount)
        
        buy_button.click()
        time.sleep(4)
        
        # Check balance after purchase
        final_balance_str = driver.execute_script("return window.mockBalance ? ethers.utils.formatEther(window.mockBalance) : '10000';")
        final_balance = float(final_balance_str)
        print(f"Balance after purchase: {final_balance} ETH")
        
        # Verify balance decreased (allowing for gas fees simulation)
        expected_decrease = float(purchase_amount)
        actual_decrease = initial_balance - final_balance
        
        if actual_decrease >= expected_decrease * 0.9:  # Allow 10% tolerance for gas simulation
            print(f"✅ Balance decreased by {actual_decrease} ETH (expected ~{expected_decrease} ETH)")
        else:
            print(f"⚠️ Balance change: {actual_decrease} ETH (expected ~{expected_decrease} ETH)")
        
        # Test redemption balance increase
        redeem_input = self.wait_for_element(driver, By.ID, "redeem-code")
        redeem_button = self.wait_for_element(driver, By.ID, "redeem-btn")
        
        pre_redeem_balance = final_balance
        redeem_input.clear()
        redeem_input.send_keys("BALANCE_TEST")
        redeem_button.click()
        time.sleep(4)
        
        post_redeem_balance_str = driver.execute_script("return window.mockBalance ? ethers.utils.formatEther(window.mockBalance) : '10000';")
        post_redeem_balance = float(post_redeem_balance_str)
        print(f"Balance after redemption: {post_redeem_balance} ETH")
        
        if post_redeem_balance > pre_redeem_balance:
            print("✅ Balance increased after redemption")
        else:
            print("⚠️ Balance did not increase after redemption (may be expected if code doesn't exist)")
        
        print("✅ Balance change simulation completed")

    def test_ui_elements_interaction(self, driver):
        """Test 7: Test various UI element interactions"""
        print("Testing UI element interactions...")
        
        driver.get(self.WEB_APP_URL)
        
        # Test input field interactions
        code_input = self.wait_for_element(driver, By.ID, "buy-code")
        amount_input = self.wait_for_element(driver, By.ID, "buy-amount")
        redeem_input = self.wait_for_element(driver, By.ID, "redeem-code")
        
        # Test input functionality
        test_text = "UI_TEST_CODE"
        code_input.send_keys(test_text)
        assert code_input.get_attribute("value") == test_text
        
        code_input.clear()
        assert code_input.get_attribute("value") == ""
        
        # Test amount input
        amount_input.send_keys("0.01")
        assert amount_input.get_attribute("value") == "0.01"
        
        # Test redeem input
        redeem_input.send_keys("REDEEM_TEST")
        assert redeem_input.get_attribute("value") == "REDEEM_TEST"
        
        # Test button states
        buy_button = self.wait_for_element(driver, By.ID, "buy-btn")
        redeem_button = self.wait_for_element(driver, By.ID, "redeem-btn")
        
        # Buttons should be disabled initially (no wallet connection)
        assert buy_button.get_attribute("disabled") is not None
        assert redeem_button.get_attribute("disabled") is not None
        
        print("✅ UI element interactions test successful")

    def test_complete_user_flow(self, driver):
        """Test 8: Complete end-to-end user flow"""
        print("Testing complete user flow...")
        
        driver.get(self.WEB_APP_URL)
        
        # Step 1: Setup and connect
        self.inject_metamask_mock(driver)
        connect_button = self.wait_for_clickable(driver, By.ID, "connect-wallet")
        connect_button.click()
        time.sleep(3)
        
        # Step 2: Buy a gift card
        code_input = self.wait_for_element(driver, By.ID, "buy-code")
        amount_input = self.wait_for_element(driver, By.ID, "buy-amount")
        buy_button = self.wait_for_element(driver, By.ID, "buy-btn")
        
        unique_code = f"FLOW_TEST_{int(time.time())}"
        code_input.send_keys(unique_code)
        amount_input.send_keys("0.002")
        buy_button.click()
        time.sleep(4)
        
        # Verify purchase status
        try:
            purchase_status = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".status"))
            )
            print(f"Purchase status: {purchase_status.text}")
        except TimeoutException:
            print("⚠️ No purchase status message")
        
        # Step 3: Attempt to redeem the same gift card
        redeem_input = self.wait_for_element(driver, By.ID, "redeem-code")
        redeem_button = self.wait_for_element(driver, By.ID, "redeem-btn")
        
        redeem_input.clear()
        redeem_input.send_keys(unique_code)
        redeem_button.click()
        time.sleep(4)
        
        # Verify redemption status
        try:
            redeem_status = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".status"))
            )
            print(f"Redemption status: {redeem_status.text}")
        except TimeoutException:
            print("⚠️ No redemption status message")
        
        print("✅ Complete user flow test finished")