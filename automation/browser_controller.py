# automation/browser_controller.py
# WebFlow Automator - Browser Controller
# This module handles browser automation using Selenium

import os
import time
import logging
import random
from typing import Dict, Any, List, Optional, Union, Tuple

# Try to import Selenium
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import (
        TimeoutException, NoSuchElementException, StaleElementReferenceException,
        ElementNotVisibleException, ElementNotInteractableException
    )
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

from core.message_bus import MessageBus, MessageTypes

logger = logging.getLogger("WebFlowAutomator.Automation.BrowserController")

class BrowserController:
    """
    Controls browser automation using Selenium
    """
    
    def __init__(self, message_bus: MessageBus):
        """
        Initialize the browser controller
        
        Args:
            message_bus: Message bus for communication
        """
        self.message_bus = message_bus
        self.driver = None
        self.max_wait_time = 30  # Default max wait time in seconds
        
        # Register with message bus
        self.subscribe_to_messages()
    
    def subscribe_to_messages(self):
        """Subscribe to relevant messages"""
        self.message_bus.subscribe(MessageTypes.UI_CLOSING, self.on_ui_closing)
    
    def initialize(self, browser_type: str = "chrome") -> bool:
        """
        Initialize the browser driver
        
        Args:
            browser_type: Type of browser to use (chrome, firefox, edge)
        
        Returns:
            bool: Success status
        """
        if not SELENIUM_AVAILABLE:
            logger.error("Selenium is not available. Please install it with 'pip install selenium'")
            return False
        
        try:
            if browser_type.lower() == "chrome":
                self.driver = self.create_chrome_driver()
            elif browser_type.lower() == "firefox":
                self.driver = self.create_firefox_driver()
            elif browser_type.lower() == "edge":
                self.driver = self.create_edge_driver()
            else:
                logger.error(f"Unsupported browser type: {browser_type}")
                return False
            
            if self.driver:
                # Maximize window
                self.driver.maximize_window()
                
                # Set implicit wait
                self.driver.implicitly_wait(5)
                
                # Navigate to blank page
                self.driver.get("about:blank")
                
                # Publish ready message
                self.message_bus.publish(MessageTypes.BROWSER_READY, {
                    "browser_type": browser_type
                })
                
                logger.info(f"Browser initialized: {browser_type}")
                return True
            else:
                logger.error("Failed to create browser driver")
                return False
        except Exception as e:
            logger.error(f"Error initializing browser: {e}")
            return False
    
    def create_chrome_driver(self):
        """
        Create Chrome WebDriver
        
        Returns:
            WebDriver: Chrome WebDriver instance
        """
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-notifications")
        
        # Create driver
        try:
            driver = webdriver.Chrome(options=options)
            return driver
        except Exception as e:
            logger.error(f"Error creating Chrome driver: {e}")
            return None
    
    def create_firefox_driver(self):
        """
        Create Firefox WebDriver
        
        Returns:
            WebDriver: Firefox WebDriver instance
        """
        from selenium.webdriver.firefox.service import Service
        from selenium.webdriver.firefox.options import Options
        
        options = Options()
        
        # Create driver
        try:
            driver = webdriver.Firefox(options=options)
            return driver
        except Exception as e:
            logger.error(f"Error creating Firefox driver: {e}")
            return None
    
    def create_edge_driver(self):
        """
        Create Edge WebDriver
        
        Returns:
            WebDriver: Edge WebDriver instance
        """
        from selenium.webdriver.edge.service import Service
        from selenium.webdriver.edge.options import Options
        
        options = Options()
        options.add_argument("--start-maximized")
        
        # Create driver
        try:
            driver = webdriver.Edge(options=options)
            return driver
        except Exception as e:
            logger.error(f"Error creating Edge driver: {e}")
            return None
    
    def close(self) -> None:
        """Close the browser"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser closed")
            except Exception as e:
                logger.error(f"Error closing browser: {e}")
            finally:
                self.driver = None
    
    def navigate(self, url: str) -> bool:
        """
        Navigate to a URL
        
        Args:
            url: URL to navigate to
        
        Returns:
            bool: Success status
        """
        if not self.driver:
            logger.error("Browser not initialized")
            return False
        
        try:
            self.driver.get(url)
            logger.info(f"Navigated to: {url}")
            return True
        except Exception as e:
            logger.error(f"Error navigating to {url}: {e}")
            return False
    
    def find_element(self, element_info: Dict[str, Any], timeout: int = 10) -> Optional[Any]:
        """
        Find an element based on element info
        
        Args:
            element_info: Element information
            timeout: Timeout in seconds
        
        Returns:
            WebElement or None: Found element or None if not found
        """
        if not self.driver:
            logger.error("Browser not initialized")
            return None
        
        try:
            # Extract element selectors
            element_id = element_info.get("id", "")
            css_selector = element_info.get("cssSelector", "")
            xpath = element_info.get("xpath", "")
            tag_name = element_info.get("tagName", "").lower()
            element_text = element_info.get("text", "")
            
            # Try selectors in order of reliability
            if element_id:
                logger.debug(f"Finding element by ID: {element_id}")
                return WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.ID, element_id))
                )
            
            if css_selector:
                logger.debug(f"Finding element by CSS selector: {css_selector}")
                return WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
                )
            
            if xpath:
                logger.debug(f"Finding element by XPath: {xpath}")
                return WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )
            
            # Fall back to tag name + text content if available
            if tag_name and element_text:
                logger.debug(f"Finding element by tag name and text: {tag_name}, {element_text}")
                elements = self.driver.find_elements(By.TAG_NAME, tag_name)
                for element in elements:
                    if element.text == element_text:
                        return element
            
            logger.error("No suitable selector found in element info")
            return None
        except TimeoutException:
            logger.error(f"Timeout finding element: {element_info}")
            return None
        except Exception as e:
            logger.error(f"Error finding element: {e}")
            return None
    
    def click_element(self, element_info: Dict[str, Any]) -> bool:
        """
        Click an element
        
        Args:
            element_info: Element information
        
        Returns:
            bool: Success status
        """
        element = self.find_element(element_info)
        if not element:
            return False
        
        try:
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            
            # Wait for element to be clickable
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, element.get_attribute("xpath")))
            )
            
            # Click element
            element.click()
            logger.info("Element clicked")
            return True
        except Exception as e:
            # Retry with JavaScript click
            try:
                logger.warning(f"Standard click failed, trying JavaScript click: {e}")
                self.driver.execute_script("arguments[0].click();", element)
                logger.info("Element clicked with JavaScript")
                return True
            except Exception as js_e:
                logger.error(f"Error clicking element with JavaScript: {js_e}")
                return False
    
    def input_text(self, element_info: Dict[str, Any], text: str) -> bool:
        """
        Input text into an element
        
        Args:
            element_info: Element information
            text: Text to input
        
        Returns:
            bool: Success status
        """
        element = self.find_element(element_info)
        if not element:
            return False
        
        try:
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            
            # Clear field first
            element.clear()
            
            # Send keys
            element.send_keys(text)
            logger.info(f"Text entered: {text}")
            return True
        except Exception as e:
            # Retry with JavaScript
            try:
                logger.warning(f"Standard input failed, trying JavaScript: {e}")
                self.driver.execute_script(f"arguments[0].value = '{text.replace("'", "\\'")}';", element)
                logger.info("Text entered with JavaScript")
                return True
            except Exception as js_e:
                logger.error(f"Error entering text with JavaScript: {js_e}")
                return False
    
    def clear_field(self, element_info: Dict[str, Any]) -> bool:
        """
        Clear a text field
        
        Args:
            element_info: Element information
        
        Returns:
            bool: Success status
        """
        element = self.find_element(element_info)
        if not element:
            return False
        
        try:
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            
            # Clear field
            element.clear()
            logger.info("Field cleared")
            return True
        except Exception as e:
            # Retry with JavaScript
            try:
                logger.warning(f"Standard clear failed, trying JavaScript: {e}")
                self.driver.execute_script("arguments[0].value = '';", element)
                logger.info("Field cleared with JavaScript")
                return True
            except Exception as js_e:
                logger.error(f"Error clearing field with JavaScript: {js_e}")
                return False
    
    def check_checkbox(self, element_info: Dict[str, Any]) -> bool:
        """
        Check a checkbox
        
        Args:
            element_info: Element information
        
        Returns:
            bool: Success status
        """
        element = self.find_element(element_info)
        if not element:
            return False
        
        try:
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            
            # Check if already checked
            if not element.is_selected():
                element.click()
                logger.info("Checkbox checked")
            else:
                logger.info("Checkbox was already checked")
            
            return True
        except Exception as e:
            # Retry with JavaScript
            try:
                logger.warning(f"Standard check failed, trying JavaScript: {e}")
                self.driver.execute_script("arguments[0].checked = true;", element)
                logger.info("Checkbox checked with JavaScript")
                return True
            except Exception as js_e:
                logger.error(f"Error checking checkbox with JavaScript: {js_e}")
                return False
    
    def uncheck_checkbox(self, element_info: Dict[str, Any]) -> bool:
        """
        Uncheck a checkbox
        
        Args:
            element_info: Element information
        
        Returns:
            bool: Success status
        """
        element = self.find_element(element_info)
        if not element:
            return False
        
        try:
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            
            # Check if already unchecked
            if element.is_selected():
                element.click()
                logger.info("Checkbox unchecked")
            else:
                logger.info("Checkbox was already unchecked")
            
            return True
        except Exception as e:
            # Retry with JavaScript
            try:
                logger.warning(f"Standard uncheck failed, trying JavaScript: {e}")
                self.driver.execute_script("arguments[0].checked = false;", element)
                logger.info("Checkbox unchecked with JavaScript")
                return True
            except Exception as js_e:
                logger.error(f"Error unchecking checkbox with JavaScript: {js_e}")
                return False
    
    def select_radio(self, element_info: Dict[str, Any]) -> bool:
        """
        Select a radio button
        
        Args:
            element_info: Element information
        
        Returns:
            bool: Success status
        """
        element = self.find_element(element_info)
        if not element:
            return False
        
        try:
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            
            # Click the radio button
            element.click()
            logger.info("Radio button selected")
            return True
        except Exception as e:
            # Retry with JavaScript
            try:
                logger.warning(f"Standard radio select failed, trying JavaScript: {e}")
                self.driver.execute_script("arguments[0].checked = true;", element)
                logger.info("Radio button selected with JavaScript")
                return True
            except Exception as js_e:
                logger.error(f"Error selecting radio button with JavaScript: {js_e}")
                return False
    
    def select_option(self, element_info: Dict[str, Any], option_text: str) -> bool:
        """
        Select an option from a dropdown
        
        Args:
            element_info: Element information
            option_text: Text of option to select
        
        Returns:
            bool: Success status
        """
        element = self.find_element(element_info)
        if not element:
            return False
        
        try:
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            
            # Create Select object
            select = Select(element)
            
            # Try to select by visible text
            select.select_by_visible_text(option_text)
            logger.info(f"Option selected: {option_text}")
            return True
        except Exception as e:
            # Try alternative methods
            try:
                logger.warning(f"Select by visible text failed, trying alternatives: {e}")
                
                # Try to select by value
                select = Select(element)
                select.select_by_value(option_text)
                logger.info(f"Option selected by value: {option_text}")
                return True
            except Exception as value_e:
                try:
                    # Try to select using JavaScript
                    option_value = None
                    options = element.find_elements(By.TAG_NAME, "option")
                    for option in options:
                        if option.text == option_text:
                            option_value = option.get_attribute("value")
                            break
                    
                    if option_value:
                        self.driver.execute_script(
                            f"arguments[0].value = '{option_value}';", element
                        )
                        logger.info(f"Option selected with JavaScript: {option_text}")
                        return True
                    else:
                        logger.error(f"Option not found: {option_text}")
                        return False
                except Exception as js_e:
                    logger.error(f"Error selecting option with JavaScript: {js_e}")
                    return False
    
    def select_random_option(self, element_info: Dict[str, Any]) -> bool:
        """
        Select a random option from a dropdown
        
        Args:
            element_info: Element information
        
        Returns:
            bool: Success status
        """
        element = self.find_element(element_info)
        if not element:
            return False
        
        try:
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            
            # Create Select object
            select = Select(element)
            
            # Get all options
            options = select.options
            
            # Skip first option if it's a placeholder (empty value)
            start_index = 1 if options[0].get_attribute("value") == "" else 0
            
            if len(options) <= start_index:
                logger.error("No valid options found in dropdown")
                return False
            
            # Select random option
            random_option = random.choice(options[start_index:])
            select.select_by_visible_text(random_option.text)
            
            logger.info(f"Random option selected: {random_option.text}")
            return True
        except Exception as e:
            logger.error(f"Error selecting random option: {e}")
            return False
    
    def get_element_text(self, element_info: Dict[str, Any]) -> Optional[str]:
        """
        Get text from an element
        
        Args:
            element_info: Element information
        
        Returns:
            str or None: Element text or None if error
        """
        element = self.find_element(element_info)
        if not element:
            return None
        
        try:
            # Get text
            text = element.text
            
            # If empty, try value attribute (for input elements)
            if not text and element.tag_name.lower() in ["input", "textarea"]:
                text = element.get_attribute("value")
            
            logger.info(f"Element text: {text}")
            return text
        except Exception as e:
            logger.error(f"Error getting element text: {e}")
            return None
    
    def wait_for_element(self, element_info: Dict[str, Any], timeout: int = 10) -> bool:
        """
        Wait for an element to be present
        
        Args:
            element_info: Element information
            timeout: Timeout in seconds
        
        Returns:
            bool: Success status
        """
        element = self.find_element(element_info, timeout)
        return element is not None
    
    def element_exists(self, element_info: Dict[str, Any]) -> bool:
        """
        Check if an element exists
        
        Args:
            element_info: Element information
        
        Returns:
            bool: Whether element exists
        """
        try:
            element = self.find_element(element_info, timeout=5)
            return element is not None
        except Exception as e:
            logger.error(f"Error checking if element exists: {e}")
            return False
    
    def take_screenshot(self, file_path: str) -> bool:
        """
        Take a screenshot
        
        Args:
            file_path: Path to save screenshot
        
        Returns:
            bool: Success status
        """
        if not self.driver:
            logger.error("Browser not initialized")
            return False
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Take screenshot
            self.driver.save_screenshot(file_path)
            
            # Publish message
            self.message_bus.publish(MessageTypes.BROWSER_SCREENSHOT_TAKEN, {
                "file_path": file_path
            })
            
            logger.info(f"Screenshot saved: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return False
    
    def on_ui_closing(self, data):
        """
        Handle UI closing event
        
        Args:
            data: Event data
        """
        # Close browser
        self.close()