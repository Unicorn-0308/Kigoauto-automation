from selenium import webdriver
from selenium.common import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import undetected_chromedriver as uc
import time
import json
import os
import tempfile
import sys
import random

class KigoAutoLogin:
    def __init__(self, headless=False):
        self.headless = headless
        self.install(headless=headless)

    def install(self, headless=False):
        # Setup Chrome options
        chrome_options = webdriver.ChromeOptions()
        if headless:
            chrome_options.add_argument("--headless=new")  # Use new headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1080,720")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Better user agent to avoid detection
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Create a unique user data directory to avoid conflicts
        self.user_data_dir = tempfile.mkdtemp(prefix="chrome_user_data_")
        chrome_options.add_argument(f"--user-data-dir={self.user_data_dir}")
        
        # Initialize driver with better error handling
        self.driver = None
        initialization_methods = [
            ("WebDriver Manager", self._init_with_manager, chrome_options),
            ("System Chrome", self._init_system_chrome, chrome_options),
            ("Direct Chrome", self._init_direct_chrome, chrome_options)
        ]
        
        for method_name, method, options in initialization_methods:
            try:
                print(f"Trying to initialize Chrome with: {method_name}")
                self.driver = method(options)
                if self.driver:
                    print(f"Successfully initialized Chrome with: {method_name}")
                    break
            except Exception as e:
                print(f"Failed with {method_name}: {str(e)}")
                continue
        
        if not self.driver:
            raise WebDriverException(
                "Failed to initialize Chrome WebDriver. Please ensure Chrome and ChromeDriver are installed.\n"
                "You can install ChromeDriver manually or let webdriver-manager handle it automatically."
            )
        
        self.wait = WebDriverWait(self.driver, 180)
    
    def _init_with_manager(self, options):
        """Initialize Chrome using webdriver-manager to auto-download the driver"""
        try:
            service = Service(ChromeDriverManager().install())
            return webdriver.Chrome(service=service, options=options)
        except Exception as e:
            print(f"WebDriver Manager error: {e}")
            raise
    
    def _init_system_chrome(self, options):
        """Try to use Chrome from system PATH"""
        return webdriver.Chrome(options=options)
    
    def _init_direct_chrome(self, options):
        """Try common Chrome installation paths on Windows"""
        common_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
        ]
        
        for chrome_path in common_paths:
            if os.path.exists(chrome_path):
                options.binary_location = chrome_path
                # Try to find or download ChromeDriver
                try:
                    service = Service(ChromeDriverManager().install())
                    return webdriver.Chrome(service=service, options=options)
                except:
                    return webdriver.Chrome(options=options)
        
        raise FileNotFoundError("Chrome not found in common installation paths")
    
    def human_like_delay(self, min_seconds=0.5, max_seconds=2.0):
        """Add random human-like delay"""
        time.sleep(random.uniform(min_seconds, max_seconds))
    
    def human_like_typing(self, element, text):
        """Type text with human-like delays between keystrokes"""
        element.clear()
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.2))
    
    def move_mouse_naturally(self, element):
        """Move mouse to element in a natural way"""
        try:
            # Check if element is visible before moving to it
            if element.is_displayed():
                action = ActionChains(self.driver)
                action.move_to_element(element).perform()
                self.human_like_delay(0.2, 0.5)
        except Exception:
            # If element is not interactable, skip the mouse movement
            pass
    
    def login(self, email, password):
        """
        Login to Kigoauto.com
        """
        try:
            # Close any existing session and start fresh
            self.close()
            self.install(self.headless)
            
            # Navigate to the main page first
            print("Navigating to Kigoauto.com...")
            self.driver.get("http://kigoauto.com")
            self.human_like_delay(3, 5)
            
            # Check if Cloudflare challenge appears
            print("Checking for Cloudflare challenge...")
            time.sleep(5)  # Give time for Cloudflare to load
            
            # Look for sign in link
            print("Looking for Sign In link...")
            sign_in_selectors = [
                "a[href*='account']",
                "a[href*='login']",
                "a[href*='signin']",
                "a:contains('Sign In')",
                "a:contains('Sign Up')",
                "a:contains('Account')",
                ".account-link",
                ".sign-in-link",
                "//a[contains(text(), 'Sign In')]",
                "//a[contains(text(), 'Sign Up')]"
            ]
            
            sign_in_link = None
            for selector in sign_in_selectors:
                try:
                    if selector.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    elif ":contains" in selector:
                        text = selector.split("'")[1]
                        elements = self.driver.find_elements(By.XPATH, f"//a[contains(text(), '{text}')]")
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    if elements:
                        sign_in_link = elements[0]
                        print(f"Found sign in link with selector: {selector}")
                        break
                except Exception as e:
                    continue
            
            if sign_in_link:
                try:
                    # Try to click normally first
                    if sign_in_link.is_displayed() and sign_in_link.is_enabled():
                        self.move_mouse_naturally(sign_in_link)
                        sign_in_link.click()
                    else:
                        # Use JavaScript click as fallback
                        self.driver.execute_script("arguments[0].click();", sign_in_link)
                    self.human_like_delay(2, 3)
                except Exception as e:
                    print(f"Could not click sign in link: {e}")
                    # Try JavaScript navigation
                    href = sign_in_link.get_attribute("href")
                    if href:
                        print(f"Navigating directly to: {href}")
                        self.driver.get(href)
                        self.human_like_delay(2, 3)
            else:
                # Try direct navigation to common login URLs
                print("Sign in link not found, trying direct navigation...")
                login_urls = [
                    "http://kigoauto.com/account/login",
                    "http://kigoauto.com/customer/account/login",
                    "http://kigoauto.com/account",
                    "http://kigoauto.com/login"
                ]
                
                for url in login_urls:
                    print(f"Trying: {url}")
                    self.driver.get(url)
                    self.human_like_delay(2, 3)
                    
                    if "login" in self.driver.current_url.lower() or "account" in self.driver.current_url.lower():
                        print(f"Successfully navigated to: {self.driver.current_url}")
                        break
            
            print(f"Current URL: {self.driver.current_url}")
            
            # Find and fill email field
            print("Looking for email field...")
            # Use the exact selector based on the HTML provided
            email_selectors = [
                "input[name='Email']",  # Exact match with capital E
                "input.input_box_txt[name='Email']",  # More specific
                "input[placeholder='you@domain.com']",  # By placeholder
                "input[name='email' i]",  # Case insensitive fallback
                "input[type='text'][name='Email']"
            ]
            
            email_field = None
            for selector in email_selectors:
                try:
                    email_field = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    if email_field.is_displayed():
                        print(f"Found email field with selector: {selector}")
                        break
                    else:
                        email_field = None
                except:
                    continue
            
            if not email_field:
                raise Exception("Could not find email field")
            
            # Find password field
            print("Looking for password field...")
            # Use the exact selector based on the HTML provided
            password_selectors = [
                "input[name='Password']",  # Exact match with capital P
                "input.input_box_txt[name='Password']",  # More specific
                "input[placeholder='at least 6 characters']",  # By placeholder
                "input[type='password'][name='Password']",  # Most specific
                "input[type='password']"  # Generic fallback
            ]
            
            password_field = None
            for selector in password_selectors:
                try:
                    password_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if password_field.is_displayed():
                        print(f"Found password field with selector: {selector}")
                        break
                    else:
                        password_field = None
                except:
                    continue
            
            if not password_field:
                raise Exception("Could not find password field")
            
            # Fill in credentials with human-like behavior
            print("Entering credentials...")
            self.move_mouse_naturally(email_field)
            email_field.click()
            self.human_like_typing(email_field, email)
            
            self.move_mouse_naturally(password_field)
            password_field.click()
            self.human_like_typing(password_field, password)
            
            # Find and click submit button
            print("Looking for submit button...")
            submit_selectors = [
                "button.signbtn.signin",  # Based on the class we saw in exploration
                "button[type='submit']:contains('Sign In')",
                "//button[text()='Sign In']",  # Exact text match
                "//button[contains(text(), 'Sign In')]",
                "button[type='submit']",
                "input[type='submit']",
                ".signbtn.signin",
                "//button[contains(@class, 'signbtn')]"
            ]
            
            submit_button = None
            for selector in submit_selectors:
                try:
                    if selector.startswith("//"):
                        submit_button = self.driver.find_element(By.XPATH, selector)
                    elif ":contains" in selector:
                        text = selector.split("'")[1]
                        submit_button = self.driver.find_element(By.XPATH, f"//button[contains(text(), '{text}')]")
                    else:
                        submit_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if submit_button and submit_button.is_displayed():
                        print(f"Found submit button with selector: {selector}")
                        break
                    else:
                        submit_button = None
                except:
                    continue
            
            if submit_button:
                self.move_mouse_naturally(submit_button)
                submit_button.click()
            else:
                # Try pressing Enter as fallback
                print("Submit button not found, pressing Enter...")
                password_field.send_keys(Keys.RETURN)
            
            # Wait for login to complete
            self.human_like_delay(3, 5)
            
            # Check if login was successful
            current_url = self.driver.current_url
            page_source = self.driver.page_source.lower()
            
            print(f"Current URL after login: {current_url}")
            
            success_indicators = [
                "account" in current_url and "login" not in current_url,
                "dashboard" in current_url,
                "logout" in page_source,
                "log out" in page_source,
                "sign out" in page_source,
                "my account" in page_source,
                "welcome" in page_source and email.lower() in page_source
            ]
            
            if any(success_indicators):
                print("Login successful!")
                # Navigate to a product page or cart
                self.driver.get("http://kigoauto.com/cart")
                self.human_like_delay(2, 3)
                return True
            else:
                print("Login may have failed or requires additional verification")
                return False
                
        except Exception as e:
            print(f"Login error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def add_products(self, product_url, quantity):
        """
        Add products to the cart on Kigoauto.com
        """
        try:
            # Navigate to product page
            print(f"Navigating to product: {product_url}")
            self.driver.get(product_url)
            self.human_like_delay(3, 5)  # Give more time for product page to load
            
            # Look for quantity input using the exact selectors provided
            print("Looking for quantity field...")
            qty_selectors = [
                "#quantity",  # Exact ID provided
                "input#quantity.qty_num",  # More specific selector
                "input[name='Qty']",  # By name attribute
                "input.qty_num",  # By class
                "input[id='quantity']"  # Alternative ID selector
            ]
            
            qty_field = None
            for selector in qty_selectors:
                try:
                    qty_field = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    if qty_field.is_displayed():
                        print(f"Found quantity field with selector: {selector}")
                        break
                    else:
                        qty_field = None
                except:
                    continue
            
            if qty_field:
                # Clear and set quantity
                self.move_mouse_naturally(qty_field)
                qty_field.click()
                
                # Clear the field using multiple methods to ensure it's empty
                qty_field.clear()
                qty_field.send_keys(Keys.CONTROL + "a")  # Select all
                qty_field.send_keys(Keys.DELETE)  # Delete
                
                # Type the new quantity
                self.human_like_typing(qty_field, str(quantity))
                print(f"Set quantity to: {quantity}")
            else:
                print("Warning: Quantity field not found, will try to add with default quantity")
            
            # Look for add to cart button using the exact selector provided
            print("Looking for add to cart button...")
            add_cart_selectors = [
                "#addtocart_button",  # Exact ID provided
                "button#addtocart_button",  # More specific
                "button[type='submit']#addtocart_button",  # Most specific
                "//button[@id='addtocart_button']",  # XPath by ID
                "//button[text()='ADD TO CART']",  # XPath by text
                "button.button.trans3",  # By classes
                "button[type='submit']"  # Generic fallback
            ]
            
            add_button = None
            for selector in add_cart_selectors:
                try:
                    if selector.startswith("//"):
                        add_button = self.driver.find_element(By.XPATH, selector)
                    else:
                        add_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if add_button and add_button.is_displayed() and add_button.is_enabled():
                        print(f"Found add to cart button with selector: {selector}")
                        break
                    else:
                        add_button = None
                except:
                    continue
            
            if add_button:
                # Click the add to cart button
                self.move_mouse_naturally(add_button)
                
                # Try multiple click methods
                try:
                    add_button.click()
                except:
                    # If regular click fails, try JavaScript click
                    self.driver.execute_script("arguments[0].click();", add_button)
                
                print(f"✓ Successfully added {quantity} item(s) to cart")
                self.human_like_delay(2, 3)
                
                # Check if we were redirected to cart or if a success message appeared
                current_url = self.driver.current_url
                if "cart" in current_url.lower():
                    print("✓ Redirected to cart page - item added successfully")
                else:
                    # Look for success notification
                    try:
                        # Common selectors for success messages
                        success_selectors = [
                            ".success-message",
                            ".alert-success",
                            ".notification-success",
                            "[class*='success']",
                            "[class*='added-to-cart']"
                        ]
                        
                        for selector in success_selectors:
                            try:
                                success_msg = self.driver.find_element(By.CSS_SELECTOR, selector)
                                if success_msg.is_displayed():
                                    print(f"✓ Success message found: {success_msg.text[:50]}...")
                                    break
                            except:
                                pass
                    except:
                        pass
                
                # Wait a moment to ensure the action completes
                self.human_like_delay(2, 3)
                
                return True
            else:
                print("❌ Could not find add to cart button")
                return False
                
        except Exception as e:
            print(f"❌ Error adding product: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_cookies(self):
        """Get all cookies from the current session"""
        try:
            cookies = self.driver.get_cookies()
            return cookies
        except Exception as e:
            print(f"Error getting cookies: {str(e)}")
            return []
    
    def save_cookies_to_file(self, filename="kigoauto_cookies.json"):
        """Save cookies to a JSON file"""
        cookies = self.get_cookies()
        try:
            with open(filename, 'w') as f:
                json.dump(cookies, f, indent=4)
            print(f"Cookies saved to {filename}")
            return True
        except Exception as e:
            print(f"Error saving cookies: {str(e)}")
            return False
    
    def load_cookies_from_file(self, filename="kigoauto_cookies.json"):
        """Load cookies from a JSON file"""
        try:
            with open(filename, 'r') as f:
                cookies = json.load(f)
            
            for cookie in cookies:
                self.driver.add_cookie(cookie)
            
            print(f"Cookies loaded from {filename}")
            return True
        except Exception as e:
            print(f"Error loading cookies: {str(e)}")
            return False
    
    def close(self):
        """Close the browser and cleanup"""
        try:
            if self.driver:
                self.driver.quit()
                
            # Cleanup temporary user data directory
            if hasattr(self, 'user_data_dir') and os.path.exists(self.user_data_dir):
                import shutil
                shutil.rmtree(self.user_data_dir)
                print(f"Cleaned up temporary directory: {self.user_data_dir}")
        except Exception as e:
            print(f"Warning: Could not cleanup properly: {e}")


# Test the implementation
if __name__ == "__main__":
    # Initialize the automation class
    kigo = KigoAutoLogin(headless=False)  # Set to True for headless mode
    
    # Credentials
    EMAIL = "ja@autokey.ca"
    PASSWORD = "pSbMC4q^M0"
    
    try:
        # Login to the store
        if kigo.login(EMAIL, PASSWORD):
            print("Login successful!")
            
            # Save cookies
            kigo.save_cookies_to_file("kigoauto_cookies.json")
            
            # Example: Add a product to cart
            # product_url = "http://kigoauto.com/products/example-product"
            # kigo.add_products(product_url, 2)
            
            print("Automation completed successfully")
        else:
            print("Login failed")
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        # Keep browser open for inspection
        input("Press Enter to close the browser...")
        kigo.close()
