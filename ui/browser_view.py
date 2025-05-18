# ui/browser_view.py
# WebFlow Automator - Browser View
# This module contains the embedded browser and element interaction functionality

import os
import logging
import json
from typing import Dict, Any, Optional, Callable

# Dynamically import the correct UI framework
try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QLineEdit, QPushButton, QHBoxLayout,
        QLabel, QFrame, QMenu, QApplication
    )
    from PyQt6.QtCore import Qt, QUrl, QSize, QPoint, pyqtSignal
    from PyQt6.QtGui import QIcon, QAction, QKeySequence, QCursor
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEngineSettings, QWebEnginePage
    USE_PYQT6 = True
except ImportError:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QLineEdit, QPushButton, QHBoxLayout,
        QLabel, QFrame, QMenu, QApplication
    )
    from PySide6.QtCore import Qt, QUrl, QSize, QPoint, Signal as pyqtSignal
    from PySide6.QtGui import QIcon, QAction, QKeySequence, QCursor
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWebEngineCore import QWebEngineSettings, QWebEnginePage
    USE_PYQT6 = False

from core.message_bus import MessageBus, MessageTypes

logger = logging.getLogger("WebFlowAutomator.UI.BrowserView")

class CustomWebEnginePage(QWebEnginePage):
    """
    Custom web engine page class to handle JavaScript alerts and other dialogs
    """
    
    def javaScriptAlert(self, url, msg):
        """Handle JavaScript alerts by logging them instead of showing dialogs"""
        logger.info(f"JavaScript Alert: {msg}")
        return True
    
    def javaScriptConfirm(self, url, msg):
        """Handle JavaScript confirms by always returning True"""
        logger.info(f"JavaScript Confirm: {msg}")
        return True
    
    def javaScriptPrompt(self, url, msg, default):
        """Handle JavaScript prompts by returning the default value"""
        logger.info(f"JavaScript Prompt: {msg} (default: {default})")
        return True, default


class BrowserView(QWidget):
    """
    Browser view component for displaying web pages and interacting with elements
    """
    
    element_selected = pyqtSignal(dict)
    
    def __init__(self, modules: Dict[str, Any]):
        """
        Initialize the browser view
        
        Args:
            modules: Dictionary containing application modules
        """
        super().__init__()
        
        self.modules = modules
        self.message_bus = modules["message_bus"]
        
        # Element detection state
        self.element_detection_active = False
        self.selected_element = None
        
        # Initialize UI
        self.setup_ui()
        
        # Subscribe to messages
        self.message_bus.subscribe(MessageTypes.WORKFLOW_STEP_STARTED, self.on_workflow_step_started)
    
    def setup_ui(self):
        """Set up the user interface"""
        # Create layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Create address bar
        self.address_bar = QLineEdit()
        self.address_bar.setPlaceholderText("Enter URL")
        self.address_bar.returnPressed.connect(self.navigate_to_url)
        
        # Create navigation buttons
        self.button_layout = QHBoxLayout()
        self.button_layout.setContentsMargins(5, 5, 5, 5)
        self.button_layout.setSpacing(5)
        
        # Add navigation buttons to layout
        self.button_layout.addWidget(self.address_bar)
        
        # Create go button
        self.go_button = QPushButton("Go")
        self.go_button.clicked.connect(self.navigate_to_url)
        self.button_layout.addWidget(self.go_button)
        
        # Create element mode button
        self.element_mode_button = QPushButton("Select Element")
        self.element_mode_button.setCheckable(True)
        self.element_mode_button.clicked.connect(self.toggle_element_detection)
        self.button_layout.addWidget(self.element_mode_button)
        
        # Add button layout to main layout
        self.layout.addLayout(self.button_layout)
        
        # Create browser view
        self.web_view = QWebEngineView()
        self.web_view.setPage(CustomWebEnginePage())
        
        # Configure web view settings
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True)
        
        # Connect web view signals
        self.web_view.loadFinished.connect(self.on_load_finished)
        self.web_view.urlChanged.connect(self.on_url_changed)
        
        # Add web view to layout
        self.layout.addWidget(self.web_view)
        
        # Initialize with a blank page
        self.web_view.setUrl(QUrl("about:blank"))
    
    def navigate_to_url(self):
        """Navigate to the URL in the address bar"""
        url = self.address_bar.text()
        
        # Add http:// if missing
        if not url.startswith(("http://", "https://")):
            url = "http://" + url
        
        self.web_view.setUrl(QUrl(url))
    
    def go_back(self):
        """Navigate back in browser history"""
        if self.web_view.history().canGoBack():
            self.web_view.back()
    
    def go_forward(self):
        """Navigate forward in browser history"""
        if self.web_view.history().canGoForward():
            self.web_view.forward()
    
    def reload(self):
        """Reload the current page"""
        self.web_view.reload()
    
    def on_url_changed(self, url):
        """
        Handle URL change event
        
        Args:
            url: New URL
        """
        self.address_bar.setText(url.toString())
    
    def on_load_finished(self, success):
        """
        Handle page load finished event
        
        Args:
            success: Whether the page loaded successfully
        """
        if success:
            url = self.web_view.url().toString()
            logger.info(f"Page loaded: {url}")
            
            # Publish message
            self.message_bus.publish(MessageTypes.BROWSER_PAGE_LOADED, {
                "url": url
            })
            
            # If element detection is active, inject the detection script
            if self.element_detection_active:
                self.inject_element_detection()
        else:
            logger.error("Page failed to load")
            
            # Publish error message
            self.message_bus.publish(MessageTypes.BROWSER_ERROR, {
                "message": "Page failed to load"
            })
    
    def on_workflow_step_started(self, data):
        """
        Handle workflow step started event
        
        Args:
            data: Step data
        """
        # Check if this is a navigation action
        action_type = data.get("action_type")
        if action_type == "navigate":
            url = data.get("url")
            if url:
                self.web_view.setUrl(QUrl(url))
    
    def toggle_element_detection(self, checked):
        """
        Toggle element detection mode
        
        Args:
            checked: Whether the button is checked
        """
        self.element_detection_active = checked
        
        if checked:
            self.element_mode_button.setText("Cancel Selection")
            self.inject_element_detection()
        else:
            self.element_mode_button.setText("Select Element")
            self.remove_element_detection()
    
    def inject_element_detection(self):
        """Inject element detection JavaScript code into the page"""
        # JavaScript code for element detection
        js_code = """
        (function() {
            // Remove existing highlight if any
            function removeHighlight() {
                const existing = document.getElementById('webflow-highlight');
                if (existing) {
                    existing.remove();
                }
            }
            
            // Create highlight element
            function createHighlight(element) {
                removeHighlight();
                
                const rect = element.getBoundingClientRect();
                const highlight = document.createElement('div');
                highlight.id = 'webflow-highlight';
                highlight.style.position = 'absolute';
                highlight.style.left = (window.scrollX + rect.left) + 'px';
                highlight.style.top = (window.scrollY + rect.top) + 'px';
                highlight.style.width = rect.width + 'px';
                highlight.style.height = rect.height + 'px';
                highlight.style.border = '2px solid #3498db';
                highlight.style.backgroundColor = 'rgba(52, 152, 219, 0.2)';
                highlight.style.zIndex = '9999';
                highlight.style.pointerEvents = 'none';
                
                document.body.appendChild(highlight);
            }
            
            // Get XPath of element
            function getXPath(element) {
                if (element.id !== '') {
                    return '//*[@id="' + element.id + '"]';
                }
                
                if (element === document.body) {
                    return '/html/body';
                }
                
                let ix = 0;
                const siblings = element.parentNode.childNodes;
                
                for (let i = 0; i < siblings.length; i++) {
                    const sibling = siblings[i];
                    
                    if (sibling === element) {
                        return getXPath(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                    }
                    
                    if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
                        ix++;
                    }
                }
            }
            
            // Get CSS selector
            function getCssSelector(element) {
                if (element.id) {
                    return '#' + element.id;
                }
                
                let path = [];
                while (element.nodeType === Node.ELEMENT_NODE) {
                    let selector = element.nodeName.toLowerCase();
                    
                    if (element.id) {
                        selector += '#' + element.id;
                        path.unshift(selector);
                        break;
                    } else {
                        let sibling = element;
                        let index = 1;
                        
                        while (sibling = sibling.previousElementSibling) {
                            if (sibling.nodeName.toLowerCase() === selector) {
                                index++;
                            }
                        }
                        
                        if (index > 1) {
                            selector += ':nth-of-type(' + index + ')';
                        }
                    }
                    
                    path.unshift(selector);
                    element = element.parentNode;
                }
                
                return path.join(' > ');
            }
            
            // Create element info object
            function getElementInfo(element) {
                const rect = element.getBoundingClientRect();
                
                return {
                    tagName: element.tagName,
                    id: element.id,
                    className: element.className,
                    type: element.type,
                    name: element.name,
                    value: element.value,
                    text: element.textContent.trim().substring(0, 100),
                    xpath: getXPath(element),
                    cssSelector: getCssSelector(element),
                    rect: {
                        left: rect.left,
                        top: rect.top,
                        width: rect.width,
                        height: rect.height
                    }
                };
            }
            
            // Mouse move handler
            function handleMouseMove(e) {
                const element = document.elementFromPoint(e.clientX, e.clientY);
                if (element) {
                    createHighlight(element);
                }
            }
            
            // Mouse click handler
            function handleMouseClick(e) {
                e.preventDefault();
                e.stopPropagation();
                
                const element = document.elementFromPoint(e.clientX, e.clientY);
                if (element) {
                    const info = getElementInfo(element);
                    window.qt.elementSelected(JSON.stringify(info));
                }
                
                // Clean up
                document.removeEventListener('mousemove', handleMouseMove);
                document.removeEventListener('click', handleMouseClick);
                removeHighlight();
                
                return false;
            }
            
            // Add event listeners
            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('click', handleMouseClick);
            
            // Add CSS for custom cursor
            const style = document.createElement('style');
            style.textContent = 'body, a, button, input, select { cursor: crosshair !important; }';
            document.head.appendChild(style);
            
            return true;
        })();
        """
        
        # Create JavaScript channel to receive element selection
        if USE_PYQT6:
            from PyQt6.QtWebEngineCore import QWebEngineScript
            
            class ElementSelectionChannel(QObject):
                def __init__(self, callback):
                    super().__init__()
                    self.callback = callback
                
                @pyqtSlot(str)
                def elementSelected(self, json_data):
                    self.callback(json_data)
            
            # Create channel object
            self.channel = ElementSelectionChannel(self.on_element_selected)
            
            # Add the channel to the page
            self.web_view.page().setWebChannel(self.channel)
            
            # Set up the script
            script = QWebEngineScript()
            script.setSourceCode(js_code)
            script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
            script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
            
            # Add the script to the page
            self.web_view.page().scripts().insert(script)
        else:
            # For PySide6, use evaluateJavaScript directly
            self.web_view.page().runJavaScript(js_code, self.on_element_detection_injected)
    
    def on_element_detection_injected(self, result):
        """
        Handle element detection injection result
        
        Args:
            result: JavaScript execution result
        """
        if result:
            logger.debug("Element detection successfully injected")
        else:
            logger.error("Failed to inject element detection")
            self.element_mode_button.setChecked(False)
            self.element_detection_active = False
    
    def remove_element_detection(self):
        """Remove element detection JavaScript code from the page"""
        js_code = """
        (function() {
            // Remove highlight
            const highlight = document.getElementById('webflow-highlight');
            if (highlight) {
                highlight.remove();
            }
            
            // Remove event listeners (recreate them to ensure they're removed)
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('click', handleMouseClick);
            
            // Remove custom cursor style
            const styles = document.head.getElementsByTagName('style');
            for (let i = 0; i < styles.length; i++) {
                if (styles[i].textContent.includes('cursor: crosshair')) {
                    styles[i].remove();
                    break;
                }
            }
            
            return true;
        })();
        """
        
        self.web_view.page().runJavaScript(js_code)
    
    def on_element_selected(self, json_data):
        """
        Handle element selection event
        
        Args:
            json_data: JSON string containing element information
        """
        try:
            # Parse JSON data
            element_info = json.loads(json_data)
            
            # Log element info
            logger.info(f"Element selected: {element_info['tagName']} ({element_info.get('id', 'no id')})")
            
            # Store selected element
            self.selected_element = element_info
            
            # Emit signal
            self.element_selected.emit(element_info)
            
            # Publish message
            self.message_bus.publish(MessageTypes.UI_ELEMENT_SELECTED, element_info)
            
            # Reset element detection mode
            self.element_mode_button.setChecked(False)
            self.element_detection_active = False
            
            # Show context menu with actions
            self.show_element_actions_menu(element_info)
        except Exception as e:
            logger.error(f"Error processing selected element: {e}")
    
    def show_element_actions_menu(self, element_info):
        """
        Show context menu with actions for the selected element
        
        Args:
            element_info: Information about the selected element
        """
        # Create menu
        menu = QMenu(self)
        
        # Element info at the top (disabled item)
        info_text = f"{element_info['tagName']}"
        if element_info.get('id'):
            info_text += f" (id: {element_info['id']})"
        
        info_action = QAction(info_text, self)
        info_action.setEnabled(False)
        menu.addAction(info_action)
        menu.addSeparator()
        
        # Add actions based on element type
        tag_name = element_info['tagName'].lower()
        
        if tag_name in ('input', 'textarea'):
            # Input field actions
            input_type = element_info.get('type', '').lower()
            
            if input_type in ('', 'text', 'email', 'password', 'search', 'tel', 'url'):
                # Text input actions
                menu.addAction("Input Text", lambda: self.action_input_text(element_info))
                menu.addAction("Clear Field", lambda: self.action_clear_field(element_info))
                
                # Add variable submenu
                var_menu = menu.addMenu("Input Variable")
                # This will be populated with variables from the variable storage
                var_menu.addAction("Add New Variable...", lambda: self.action_add_variable(element_info))
                
                # Add generate submenu
                gen_menu = menu.addMenu("Generate Data")
                gen_menu.addAction("Name", lambda: self.action_generate_name(element_info))
                gen_menu.addAction("Email", lambda: self.action_generate_email(element_info))
                gen_menu.addAction("Number", lambda: self.action_generate_number(element_info))
                gen_menu.addAction("Date", lambda: self.action_generate_date(element_info))
                gen_menu.addAction("Custom Format...", lambda: self.action_generate_custom(element_info))
            
            elif input_type == 'checkbox':
                menu.addAction("Check", lambda: self.action_check(element_info))
                menu.addAction("Uncheck", lambda: self.action_uncheck(element_info))
            
            elif input_type == 'radio':
                menu.addAction("Select", lambda: self.action_select_radio(element_info))
            
            elif input_type in ('button', 'submit', 'reset'):
                menu.addAction("Click", lambda: self.action_click(element_info))
        
        elif tag_name == 'select':
            menu.addAction("Select Option...", lambda: self.action_select_option(element_info))
            menu.addAction("Select Random Option", lambda: self.action_select_random_option(element_info))
        
        elif tag_name in ('a', 'button'):
            menu.addAction("Click", lambda: self.action_click(element_info))
        
        elif tag_name in ('div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            menu.addAction("Extract Text", lambda: self.action_extract_text(element_info))
        
        else:
            # Generic actions for any element
            menu.addAction("Click", lambda: self.action_click(element_info))
            menu.addAction("Extract Text", lambda: self.action_extract_text(element_info))
        
        # Common actions for all elements
        menu.addSeparator()
        menu.addAction("Wait For Element", lambda: self.action_wait_for_element(element_info))
        menu.addAction("Verify Exists", lambda: self.action_verify_exists(element_info))
        
        # Show menu at cursor position
        menu.exec(QCursor.pos())
    
    # Element action methods
    def action_click(self, element_info):
        """
        Add click action to workflow
        
        Args:
            element_info: Information about the element
        """
        # Create action data
        action_data = {
            "action_type": "click",
            "element": element_info
        }
        
        # Add action to workflow
        self.add_action_to_workflow("Click", action_data)
    
    def action_input_text(self, element_info):
        """
        Add input text action to workflow
        
        Args:
            element_info: Information about the element
        """
        # TODO: Implement input dialog to get text
        text = "Sample Text"  # This would come from a dialog
        
        # Create action data
        action_data = {
            "action_type": "input_text",
            "element": element_info,
            "text": text
        }
        
        # Add action to workflow
        self.add_action_to_workflow("Input Text", action_data)
    
    def action_clear_field(self, element_info):
        """
        Add clear field action to workflow
        
        Args:
            element_info: Information about the element
        """
        # Create action data
        action_data = {
            "action_type": "clear_field",
            "element": element_info
        }
        
        # Add action to workflow
        self.add_action_to_workflow("Clear Field", action_data)
    
    def action_check(self, element_info):
        """
        Add check action to workflow
        
        Args:
            element_info: Information about the element
        """
        # Create action data
        action_data = {
            "action_type": "check",
            "element": element_info
        }
        
        # Add action to workflow
        self.add_action_to_workflow("Check", action_data)
    
    def action_uncheck(self, element_info):
        """
        Add uncheck action to workflow
        
        Args:
            element_info: Information about the element
        """
        # Create action data
        action_data = {
            "action_type": "uncheck",
            "element": element_info
        }
        
        # Add action to workflow
        self.add_action_to_workflow("Uncheck", action_data)
    
    def action_select_radio(self, element_info):
        """
        Add select radio action to workflow
        
        Args:
            element_info: Information about the element
        """
        # Create action data
        action_data = {
            "action_type": "select_radio",
            "element": element_info
        }
        
        # Add action to workflow
        self.add_action_to_workflow("Select Radio", action_data)
    
    def action_select_option(self, element_info):
        """
        Add select option action to workflow
        
        Args:
            element_info: Information about the element
        """
        # TODO: Implement dialog to select option
        option = "Option 1"  # This would come from a dialog
        
        # Create action data
        action_data = {
            "action_type": "select_option",
            "element": element_info,
            "option": option
        }
        
        # Add action to workflow
        self.add_action_to_workflow("Select Option", action_data)
    
    def action_select_random_option(self, element_info):
        """
        Add select random option action to workflow
        
        Args:
            element_info: Information about the element
        """
        # Create action data
        action_data = {
            "action_type": "select_random_option",
            "element": element_info
        }
        
        # Add action to workflow
        self.add_action_to_workflow("Select Random Option", action_data)
    
    def action_extract_text(self, element_info):
        """
        Add extract text action to workflow
        
        Args:
            element_info: Information about the element
        """
        # TODO: Implement dialog to get variable name
        variable_name = "extractedText"  # This would come from a dialog
        
        # Create action data
        action_data = {
            "action_type": "extract_text",
            "element": element_info,
            "variable_name": variable_name
        }
        
        # Add action to workflow
        self.add_action_to_workflow("Extract Text", action_data)
    
    def action_wait_for_element(self, element_info):
        """
        Add wait for element action to workflow
        
        Args:
            element_info: Information about the element
        """
        # TODO: Implement dialog to get timeout
        timeout = 10  # This would come from a dialog (seconds)
        
        # Create action data
        action_data = {
            "action_type": "wait_for_element",
            "element": element_info,
            "timeout": timeout
        }
        
        # Add action to workflow
        self.add_action_to_workflow("Wait For Element", action_data)
    
    def action_verify_exists(self, element_info):
        """
        Add verify exists action to workflow
        
        Args:
            element_info: Information about the element
        """
        # Create action data
        action_data = {
            "action_type": "verify_exists",
            "element": element_info
        }
        
        # Add action to workflow
        self.add_action_to_workflow("Verify Exists", action_data)
    
    def action_add_variable(self, element_info):
        """
        Add a new variable action to workflow
        
        Args:
            element_info: Information about the element
        """
        # TODO: Implement dialog to get variable details
        variable_name = "newVariable"  # This would come from a dialog
        
        # Create action data
        action_data = {
            "action_type": "input_variable",
            "element": element_info,
            "variable_name": variable_name
        }
        
        # Add action to workflow
        self.add_action_to_workflow("Input Variable", action_data)
    
    def action_generate_name(self, element_info):
        """
        Add generate name action to workflow
        
        Args:
            element_info: Information about the element
        """
        # TODO: Implement dialog to configure name generation
        
        # Create action data
        action_data = {
            "action_type": "generate_name",
            "element": element_info,
            "name_type": "full"  # Options: first, last, full
        }
        
        # Add action to workflow
        self.add_action_to_workflow("Generate Name", action_data)
    
    def action_generate_email(self, element_info):
        """
        Add generate email action to workflow
        
        Args:
            element_info: Information about the element
        """
        # Create action data
        action_data = {
            "action_type": "generate_email",
            "element": element_info
        }
        
        # Add action to workflow
        self.add_action_to_workflow("Generate Email", action_data)
    
    def action_generate_number(self, element_info):
        """
        Add generate number action to workflow
        
        Args:
            element_info: Information about the element
        """
        # TODO: Implement dialog to configure number generation
        
        # Create action data
        action_data = {
            "action_type": "generate_number",
            "element": element_info,
            "min": 1,
            "max": 100
        }
        
        # Add action to workflow
        self.add_action_to_workflow("Generate Number", action_data)
    
    def action_generate_date(self, element_info):
        """
        Add generate date action to workflow
        
        Args:
            element_info: Information about the element
        """
        # TODO: Implement dialog to configure date generation
        
        # Create action data
        action_data = {
            "action_type": "generate_date",
            "element": element_info,
            "format": "YYYY-MM-DD"
        }
        
        # Add action to workflow
        self.add_action_to_workflow("Generate Date", action_data)
    
    def action_generate_custom(self, element_info):
        """
        Add generate custom action to workflow
        
        Args:
            element_info: Information about the element
        """
        # TODO: Implement dialog to configure custom generation
        
        # Create action data
        action_data = {
            "action_type": "generate_custom",
            "element": element_info,
            "format": "###-##-####"  # Example format: 123-45-6789
        }
        
        # Add action to workflow
        self.add_action_to_workflow("Generate Custom", action_data)
    
    def add_action_to_workflow(self, action_name, action_data):
        """
        Add an action to the workflow
        
        Args:
            action_name: Human-readable name of the action
            action_data: Action data to be stored
        """
        # Log action
        logger.info(f"Adding action to workflow: {action_name}")
        
        # Publish message to add action to workflow
        self.message_bus.publish(MessageTypes.UI_REFRESH_WORKFLOW, {
            "action": "add",
            "action_name": action_name,
            "action_data": action_data
        })
