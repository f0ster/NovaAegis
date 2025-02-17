"""
Browser pilot for executing DSL operations.
Provides low-level browser automation capabilities.
"""
from typing import Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import chromedriver_autoinstaller
from functools import wraps
import logging

class BrowserPilot:
    """Browser automation for DSL operations."""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.driver = None
        self.logger = logging.getLogger(__name__)
        
    def __enter__(self):
        """Initialize browser."""
        chromedriver_autoinstaller.install()
        
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
            
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
        self.wait = WebDriverWait(self.driver, 10)
        
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up browser."""
        if self.driver:
            self.driver.quit()
            
    def requires_browser(f):
        """Ensure browser is initialized."""
        @wraps(f)
        def wrapper(self, *args, **kwargs):
            if not self.driver:
                raise RuntimeError("Browser not initialized")
            return f(self, *args, **kwargs)
        return wrapper

    @requires_browser
    def execute(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Execute browser command."""
        try:
            cmd_type = command["type"]
            
            # Core navigation
            if cmd_type == "navigate":
                return self.navigate(command["url"])
            elif cmd_type == "back":
                self.driver.back()
                return {"success": True}
            elif cmd_type == "forward":
                self.driver.forward()
                return {"success": True}
            elif cmd_type == "refresh":
                self.driver.refresh()
                return {"success": True}
                
            # Element interaction
            elif cmd_type == "click":
                return self.click(command["selector"])
            elif cmd_type == "type":
                return self.type_text(
                    command["selector"],
                    command["text"]
                )
            elif cmd_type == "submit":
                return self.submit(command["selector"])
            elif cmd_type == "hover":
                return self.hover(command["selector"])
            elif cmd_type == "focus":
                return self.focus(command["selector"])
            elif cmd_type == "blur":
                return self.blur(command["selector"])
                
            # Content extraction
            elif cmd_type == "extract":
                return self.extract_content(
                    command["selector"],
                    command.get("extract", "text"),
                    command.get("attribute")
                )
                
            # Element state
            elif cmd_type == "check":
                return self.check_element(
                    command["selector"],
                    command["check"]
                )
                
            # Page state
            elif cmd_type == "url":
                return {
                    "success": True,
                    "result": self.driver.current_url
                }
            elif cmd_type == "title":
                return {
                    "success": True,
                    "result": self.driver.title
                }
            elif cmd_type == "ready":
                return {
                    "success": True,
                    "result": self.driver.execute_script(
                        "return document.readyState"
                    ) == "complete"
                }
                
            # Waiting
            elif cmd_type == "wait":
                return self.wait_for(
                    command["selector"],
                    command.get("wait_type", "present")
                )
                
            # Screenshots
            elif cmd_type == "screenshot":
                return self.take_screenshot(
                    command.get("selector")
                )
                
            else:
                return {
                    "success": False,
                    "error": f"Unknown command type: {cmd_type}"
                }
                
        except Exception as e:
            self.logger.error(f"Command failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @requires_browser
    def navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to URL."""
        try:
            self.driver.get(url)
            self.wait.until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            return {
                "success": True,
                "result": self.driver.current_url
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @requires_browser
    def click(self, selector: str) -> Dict[str, Any]:
        """Click element."""
        try:
            element = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            ActionChains(self.driver).move_to_element(element).click().perform()
            return {
                "success": True
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @requires_browser
    def type_text(self, selector: str, text: str) -> Dict[str, Any]:
        """Type text into element."""
        try:
            element = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            element.clear()
            element.send_keys(text)
            return {
                "success": True
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @requires_browser
    def submit(self, selector: str) -> Dict[str, Any]:
        """Submit form element."""
        try:
            element = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            element.submit()
            return {
                "success": True
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @requires_browser
    def hover(self, selector: str) -> Dict[str, Any]:
        """Hover over element."""
        try:
            element = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            ActionChains(self.driver).move_to_element(element).perform()
            return {
                "success": True
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @requires_browser
    def focus(self, selector: str) -> Dict[str, Any]:
        """Focus element."""
        try:
            element = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            self.driver.execute_script("arguments[0].focus();", element)
            return {
                "success": True
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @requires_browser
    def blur(self, selector: str) -> Dict[str, Any]:
        """Remove focus from element."""
        try:
            element = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            self.driver.execute_script("arguments[0].blur();", element)
            return {
                "success": True
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @requires_browser
    def extract_content(
        self,
        selector: str,
        extract_type: str = "text",
        attribute: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract content from elements."""
        try:
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            
            if extract_type == "text":
                content = [e.text for e in elements]
            elif extract_type == "html":
                content = [e.get_attribute("outerHTML") for e in elements]
            elif extract_type == "attribute":
                content = [e.get_attribute(attribute) for e in elements]
            else:
                return {
                    "success": False,
                    "error": f"Unknown extract type: {extract_type}"
                }
                
            return {
                "success": True,
                "result": content[0] if len(content) == 1 else content
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @requires_browser
    def check_element(self, selector: str, check_type: str) -> Dict[str, Any]:
        """Check element state."""
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            
            if check_type == "exists":
                result = True
            elif check_type == "visible":
                result = element.is_displayed()
            elif check_type == "enabled":
                result = element.is_enabled()
            elif check_type == "selected":
                result = element.is_selected()
            else:
                return {
                    "success": False,
                    "error": f"Unknown check type: {check_type}"
                }
                
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            if check_type == "exists":
                return {
                    "success": True,
                    "result": False
                }
            return {
                "success": False,
                "error": str(e)
            }

    @requires_browser
    def wait_for(self, selector: str, wait_type: str) -> Dict[str, Any]:
        """Wait for element state."""
        try:
            if wait_type == "present":
                self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
            elif wait_type == "gone":
                self.wait.until_not(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
            elif wait_type == "visible":
                self.wait.until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
                )
            else:
                return {
                    "success": False,
                    "error": f"Unknown wait type: {wait_type}"
                }
                
            return {
                "success": True
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @requires_browser
    def take_screenshot(self, selector: Optional[str] = None) -> Dict[str, Any]:
        """Take screenshot."""
        try:
            if selector:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                image = element.screenshot_as_base64
            else:
                image = self.driver.get_screenshot_as_base64
                
            return {
                "success": True,
                "result": image
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }