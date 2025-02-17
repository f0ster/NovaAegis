"""
Test browser DSL operations.
Verifies browser pilot executes DSL commands correctly.
"""
import pytest
from unittest.mock import Mock, patch
from selenium.webdriver.common.by import By

from nova_aegis.browser_pilot import BrowserPilot
from nova_aegis.core.tools.browser_tool import BrowserTool

class MockDriver:
    """Mock Selenium WebDriver"""
    def __init__(self):
        self.current_url = "https://test.com"
        self.title = "Test Page"
        self.ready_state = "complete"
        self.actions = []
        
    def get(self, url):
        self.current_url = url
        self.actions.append(f"Navigate to {url}")
        
    def find_element(self, by, value):
        return MockElement()
        
    def find_elements(self, by, value):
        return [MockElement(), MockElement()]
        
    def execute_script(self, script, *args):
        self.actions.append(f"Execute: {script[:50]}")
        if "return document.readyState" in script:
            return self.ready_state
        return None
        
    def back(self):
        self.actions.append("Back")
        
    def forward(self):
        self.actions.append("Forward")
        
    def refresh(self):
        self.actions.append("Refresh")
        
    def get_screenshot_as_base64(self):
        return "base64_screenshot"
        
    def quit(self):
        self.actions.append("Quit")

class MockElement:
    """Mock Selenium WebElement"""
    def __init__(self):
        self.text = "Test content"
        self.is_displayed = True
        self.is_enabled = True
        self.is_selected = False
        self.attributes = {
            "class": "test-class",
            "href": "https://test.com"
        }
        
    def clear(self):
        pass
        
    def send_keys(self, *args):
        pass
        
    def click(self):
        pass
        
    def submit(self):
        pass
        
    def get_attribute(self, name):
        return self.attributes.get(name)
        
    def screenshot_as_base64(self):
        return "base64_element_screenshot"

def test_browser_dsl():
    """Test browser DSL execution."""
    tool = BrowserTool()
    
    with patch('selenium.webdriver.Chrome') as mock_chrome:
        mock_driver = MockDriver()
        mock_chrome.return_value = mock_driver
        
        with tool:
            # Test navigation
            result = tool._run('goto("https://test.com")')
            assert result == "https://test.com"
            
            result = tool._run('back()')
            assert result == "Success"
            
            result = tool._run('forward()')
            assert result == "Success"
            
            result = tool._run('refresh()')
            assert result == "Success"
            
            # Test interaction
            result = tool._run('click("#button")')
            assert result == "Success"
            
            result = tool._run('type("#input", "test text")')
            assert result == "Success"
            
            result = tool._run('submit("#form")')
            assert result == "Success"
            
            result = tool._run('hover("#menu")')
            assert result == "Success"
            
            # Test content extraction
            result = tool._run('read("#content")')
            assert result == "Test content"
            
            result = tool._run('attr("#link", "href")')
            assert result == "https://test.com"
            
            # Test element state
            result = tool._run('exists("#element")')
            assert result == "True"
            
            result = tool._run('visible("#element")')
            assert result == "True"
            
            result = tool._run('enabled("#element")')
            assert result == "True"
            
            result = tool._run('selected("#element")')
            assert result == "False"
            
            # Test page state
            result = tool._run('url()')
            assert result == "https://test.com"
            
            result = tool._run('title()')
            assert result == "Test Page"
            
            result = tool._run('ready()')
            assert result == "True"
            
            # Test waiting
            result = tool._run('wait("#element")')
            assert result == "Success"
            
            result = tool._run('wait_visible("#element")')
            assert result == "Success"
            
            # Test screenshots
            result = tool._run('screenshot()')
            assert result == "base64_screenshot"
            
            result = tool._run('screenshot("#element")')
            assert result == "base64_element_screenshot"

def test_error_handling():
    """Test DSL error handling."""
    tool = BrowserTool()
    
    with patch('selenium.webdriver.Chrome') as mock_chrome:
        mock_driver = MockDriver()
        mock_driver.ready_state = "loading"  # Simulate loading error
        mock_chrome.return_value = mock_driver
        
        with tool:
            # Test navigation error
            result = tool._run('goto("https://test.com")')
            assert "Failed" in result
            
            # Test invalid command
            result = tool._run('invalid_command()')
            assert "Unknown DSL command" in result
            
            # Test invalid selector
            mock_driver.find_element = lambda by, value: exec('raise Exception("No such element")')
            result = tool._run('click("#nonexistent")')
            assert "Failed" in result

def test_async_execution():
    """Test async DSL execution."""
    tool = BrowserTool()
    
    with patch('selenium.webdriver.Chrome') as mock_chrome:
        mock_driver = MockDriver()
        mock_chrome.return_value = mock_driver
        
        with tool:
            # Test async navigation
            async def test_async():
                result = await tool._arun('goto("https://test.com")')
                assert result == "https://test.com"
                
            import asyncio
            asyncio.run(test_async())