# ui/element_selector.py
# WebFlow Automator - Element Selector
# This module contains the element selection utilities

import logging
from typing import Dict, Any, List, Optional, Callable

# Dynamically import the correct UI framework
try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QLabel, QFrame
    )
    from PyQt6.QtCore import Qt, QRect, pyqtSignal
    from PyQt6.QtGui import QPainter, QColor, QPen
    USE_PYQT6 = True
except ImportError:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QLabel, QFrame
    )
    from PySide6.QtCore import Qt, QRect, Signal as pyqtSignal
    from PySide6.QtGui import QPainter, QColor, QPen
    USE_PYQT6 = False

logger = logging.getLogger("WebFlowAutomator.UI.ElementSelector")

class ElementHighlight(QWidget):
    """
    Widget overlay for highlighting elements on the page
    """
    
    def __init__(self, parent=None):
        """
        Initialize the element highlight overlay
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Set window flags
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        
        # Set background transparent
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Set widget transparent for mouse events
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        # Element rect
        self.element_rect = QRect()
    
    def set_rect(self, rect):
        """
        Set the element rectangle
        
        Args:
            rect: Element rectangle
        """
        self.element_rect = rect
        self.update()
    
    def paintEvent(self, event):
        """
        Paint the highlight
        
        Args:
            event: Paint event
        """
        painter = QPainter(self)
        
        # Draw semi-transparent blue rectangle
        painter.setPen(QPen(QColor(0, 120, 215), 2))
        painter.setBrush(QColor(0, 120, 215, 40))
        painter.drawRect(self.element_rect)


class ElementSelector:
    """
    Handles element selection in the browser view
    """
    
    def __init__(self, browser_view, message_bus):
        """
        Initialize the element selector
        
        Args:
            browser_view: Browser view widget
            message_bus: Message bus for communication
        """
        self.browser_view = browser_view
        self.message_bus = message_bus
        
        # Create highlight overlay
        self.highlight = ElementHighlight(self.browser_view)
        self.highlight.hide()
    
    def start_selection(self):
        """Start element selection mode"""
        logger.info("Element selection mode started")
        
        # Enable element detection in browser
        self.browser_view.toggle_element_detection(True)
        
        # Show highlight overlay
        self.highlight.show()
    
    def stop_selection(self):
        """Stop element selection mode"""
        logger.info("Element selection mode stopped")
        
        # Disable element detection in browser
        self.browser_view.toggle_element_detection(False)
        
        # Hide highlight overlay
        self.highlight.hide()
    
    def update_highlight(self, element_info):
        """
        Update highlight overlay based on element info
        
        Args:
            element_info: Element information
        """
        if "rect" in element_info:
            rect = element_info["rect"]
            
            # Create QRect
            element_rect = QRect(
                rect["left"],
                rect["top"],
                rect["width"],
                rect["height"]
            )
            
            # Update highlight
            self.highlight.set_rect(element_rect)