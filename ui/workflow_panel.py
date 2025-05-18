# ui/workflow_panel.py
# WebFlow Automator - Workflow Panel
# This module contains the workflow builder UI component

import os
import logging
import json
from typing import Dict, Any, List, Optional

# Dynamically import the correct UI framework
try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
        QFrame, QMenu, QToolButton, QDialog, QLineEdit, QCheckBox, QComboBox,
        QSpinBox, QDateEdit, QMessageBox, QListWidget, QListWidgetItem, QGroupBox,
        QFormLayout, QSplitter
    )
    from PyQt6.QtCore import Qt, QSize, pyqtSignal, QDateTime
    from PyQt6.QtGui import QIcon, QAction, QDrag, QPixmap
    USE_PYQT6 = True
except ImportError:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
        QFrame, QMenu, QToolButton, QDialog, QLineEdit, QCheckBox, QComboBox,
        QSpinBox, QDateEdit, QMessageBox, QListWidget, QListWidgetItem, QGroupBox,
        QFormLayout, QSplitter
    )
    from PySide6.QtCore import Qt, QSize, Signal as pyqtSignal, QDateTime
    from PySide6.QtGui import QIcon, QAction, QDrag, QPixmap
    USE_PYQT6 = False

from core.message_bus import MessageBus, MessageTypes

logger = logging.getLogger("WebFlowAutomator.UI.WorkflowPanel")

class ActionCard(QFrame):
    """
    Represents a single action step in the workflow
    """
    
    delete_requested = pyqtSignal(object)
    edit_requested = pyqtSignal(object)
    
    def __init__(self, action_name: str, action_data: Dict[str, Any], parent=None):
        """
        Initialize the action card
        
        Args:
            action_name: Human-readable name of the action
            action_data: Action data
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.action_name = action_name
        self.action_data = action_data
        
        # Set up UI
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface"""
        # Set frame style
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setMinimumHeight(80)
        self.setMaximumHeight(200)
        
        # Create layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(8)
        
        # Create header layout
        self.header_layout = QHBoxLayout()
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create action name label
        self.action_label = QLabel(self.action_name)
        self.action_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.header_layout.addWidget(self.action_label)
        
        # Add spacer
        self.header_layout.addStretch()
        
        # Create button layout
        self.button_layout = QHBoxLayout()
        self.button_layout.setSpacing(4)
        
        # Create edit button
        self.edit_button = QToolButton()
        self.edit_button.setText("⚙")
        self.edit_button.setToolTip("Edit Action")
        self.edit_button.clicked.connect(self.on_edit_clicked)
        self.button_layout.addWidget(self.edit_button)
        
        # Create delete button
        self.delete_button = QToolButton()
        self.delete_button.setText("✕")
        self.delete_button.setToolTip("Delete Action")
        self.delete_button.clicked.connect(self.on_delete_clicked)
        self.button_layout.addWidget(self.delete_button)
        
        # Add button layout to header
        self.header_layout.addLayout(self.button_layout)
        
        # Add header layout to main layout
        self.layout.addLayout(self.header_layout)
        
        # Add separator line
        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.Shape.HLine)
        self.separator.setFrameShadow(QFrame.Shadow.Sunken)
        self.layout.addWidget(self.separator)
        
        # Create details layout
        self.details_layout = QFormLayout()
        self.details_layout.setContentsMargins(0, 0, 0, 0)
        self.details_layout.setSpacing(4)
        
        # Add details based on action type
        self.add_action_details()
        
        # Add details layout to main layout
        self.layout.addLayout(self.details_layout)
        
        # Apply stylesheet
        self.setStyleSheet("""
            ActionCard {
                background-color: #ffffff;
                border: 1px solid #d1d1d6;
                border-radius: 6px;
            }
            
            ActionCard:hover {
                border: 1px solid #007aff;
            }
            
            QToolButton {
                border: none;
                background-color: transparent;
                padding: 2px;
                border-radius: 4px;
            }
            
            QToolButton:hover {
                background-color: #f0f0f0;
            }
        """)
    
    def add_action_details(self):
        """Add details to the card based on action type"""
        action_type = self.action_data.get("action_type", "unknown")
        
        if action_type == "navigate":
            url = self.action_data.get("url", "")
            self.details_layout.addRow("URL:", QLabel(url))
        
        elif action_type in ("click", "check", "uncheck", "select_radio"):
            element = self.action_data.get("element", {})
            element_desc = self.get_element_description(element)
            self.details_layout.addRow("Element:", QLabel(element_desc))
        
        elif action_type == "input_text":
            element = self.action_data.get("element", {})
            element_desc = self.get_element_description(element)
            self.details_layout.addRow("Element:", QLabel(element_desc))
            
            text = self.action_data.get("text", "")
            self.details_layout.addRow("Text:", QLabel(text))
        
        elif action_type == "input_variable":
            element = self.action_data.get("element", {})
            element_desc = self.get_element_description(element)
            self.details_layout.addRow("Element:", QLabel(element_desc))
            
            variable_name = self.action_data.get("variable_name", "")
            self.details_layout.addRow("Variable:", QLabel(f"${{{variable_name}}}" if variable_name else ""))
        
        elif action_type == "select_option":
            element = self.action_data.get("element", {})
            element_desc = self.get_element_description(element)
            self.details_layout.addRow("Element:", QLabel(element_desc))
            
            option = self.action_data.get("option", "")
            self.details_layout.addRow("Option:", QLabel(option))
        
        elif action_type == "select_random_option":
            element = self.action_data.get("element", {})
            element_desc = self.get_element_description(element)
            self.details_layout.addRow("Element:", QLabel(element_desc))
            
            self.details_layout.addRow("Option:", QLabel("Random"))
        
        elif action_type == "extract_text":
            element = self.action_data.get("element", {})
            element_desc = self.get_element_description(element)
            self.details_layout.addRow("Element:", QLabel(element_desc))
            
            variable_name = self.action_data.get("variable_name", "")
            self.details_layout.addRow("Store as:", QLabel(variable_name))
        
        elif action_type == "wait_for_element":
            element = self.action_data.get("element", {})
            element_desc = self.get_element_description(element)
            self.details_layout.addRow("Element:", QLabel(element_desc))
            
            timeout = self.action_data.get("timeout", 10)
            self.details_layout.addRow("Timeout:", QLabel(f"{timeout} seconds"))
        
        elif action_type == "verify_exists":
            element = self.action_data.get("element", {})
            element_desc = self.get_element_description(element)
            self.details_layout.addRow("Element:", QLabel(element_desc))
        
        elif action_type.startswith("generate_"):
            element = self.action_data.get("element", {})
            element_desc = self.get_element_description(element)
            self.details_layout.addRow("Element:", QLabel(element_desc))
            
            if action_type == "generate_name":
                name_type = self.action_data.get("name_type", "full")
                self.details_layout.addRow("Type:", QLabel(name_type.capitalize()))
            
            elif action_type == "generate_number":
                min_val = self.action_data.get("min", 1)
                max_val = self.action_data.get("max", 100)
                self.details_layout.addRow("Range:", QLabel(f"{min_val} to {max_val}"))
            
            elif action_type == "generate_date":
                date_format = self.action_data.get("format", "YYYY-MM-DD")
                self.details_layout.addRow("Format:", QLabel(date_format))
            
            elif action_type == "generate_custom":
                custom_format = self.action_data.get("format", "")
                self.details_layout.addRow("Format:", QLabel(custom_format))
    
    def get_element_description(self, element):
        """
        Get a human-readable description of an element
        
        Args:
            element: Element information
        
        Returns:
            str: Human-readable element description
        """
        if not element:
            return "Unknown element"
        
        tag_name = element.get("tagName", "").lower()
        element_id = element.get("id", "")
        
        if element_id:
            return f"<{tag_name} id=\"{element_id}\">"
        
        css_selector = element.get("cssSelector", "")
        if css_selector:
            # Simplify long selectors
            if len(css_selector) > 50:
                css_selector = css_selector[:47] + "..."
            return css_selector
        
        return f"<{tag_name}>"
    
    def on_delete_clicked(self):
        """Handle delete button click"""
        self.delete_requested.emit(self)
    
    def on_edit_clicked(self):
        """Handle edit button click"""
        self.edit_requested.emit(self)


class WorkflowPanel(QWidget):
    """
    Panel for building and managing workflows
    """
    
    def __init__(self, modules: Dict[str, Any]):
        """
        Initialize the workflow panel
        
        Args:
            modules: Dictionary containing application modules
        """
        super().__init__()
        
        self.modules = modules
        self.message_bus = modules["message_bus"]
        
        # Current workflow
        self.current_workflow = {
            "name": "New Workflow",
            "steps": []
        }
        
        # Action cards
        self.action_cards = []
        
        # Initialize UI
        self.setup_ui()
        
        # Connect to message bus
        self.message_bus.subscribe(MessageTypes.UI_REFRESH_WORKFLOW, self.on_workflow_refresh)
    
    def setup_ui(self):
        """Set up the user interface"""
        # Create layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Create header
        self.header = QWidget()
        self.header.setMinimumHeight(40)
        self.header.setMaximumHeight(40)
        self.header.setStyleSheet("""
            background-color: #f5f5f7;
            border-bottom: 1px solid #d1d1d6;
        """)
        
        self.header_layout = QHBoxLayout(self.header)
        self.header_layout.setContentsMargins(10, 0, 10, 0)
        
        self.header_label = QLabel("Workflow Builder")
        self.header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.header_layout.addWidget(self.header_label)
        
        self.layout.addWidget(self.header)
        
        # Create scroll area for actions
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # Create container widget for actions
        self.action_container = QWidget()
        self.action_container.setStyleSheet("background-color: #f5f5f7;")
        
        self.action_layout = QVBoxLayout(self.action_container)
        self.action_layout.setContentsMargins(10, 10, 10, 10)
        self.action_layout.setSpacing(10)
        self.action_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Add new action button
        self.new_action_button = QPushButton("+ Add Action")
        self.new_action_button.clicked.connect(self.show_add_action_menu)
        self.action_layout.addWidget(self.new_action_button)
        
        # Set scroll area widget
        self.scroll_area.setWidget(self.action_container)
        self.layout.addWidget(self.scroll_area)
    
    def new_workflow(self):
        """Create a new workflow"""
        # Check if current workflow has steps
        if self.current_workflow.get("steps"):
            # Ask for confirmation
            reply = QMessageBox.question(
                self,
                "New Workflow",
                "This will clear the current workflow. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        # Clear current workflow
        self.current_workflow = {
            "name": "New Workflow",
            "steps": []
        }
        
        # Clear UI
        self.clear_action_cards()
        
        # Update UI
        self.message_bus.publish(MessageTypes.UI_STATUS_UPDATE, "New workflow created")
    
    def show_add_action_menu(self):
        """Show menu for adding actions"""
        menu = QMenu(self)
        
        # Navigation actions
        navigate_action = QAction("Navigate to URL", self)
        navigate_action.triggered.connect(self.add_navigate_action)
        menu.addAction(navigate_action)
        
        menu.addSeparator()
        
        # Element actions submenu
        element_menu = menu.addMenu("Element Actions")
        
        click_action = QAction("Click Element", self)
        click_action.triggered.connect(self.add_click_action)
        element_menu.addAction(click_action)
        
        input_action = QAction("Input Text", self)
        input_action.triggered.connect(self.add_input_text_action)
        element_menu.addAction(input_action)
        
        clear_action = QAction("Clear Field", self)
        clear_action.triggered.connect(self.add_clear_field_action)
        element_menu.addAction(clear_action)
        
        check_action = QAction("Check/Uncheck", self)
        check_action.triggered.connect(self.add_check_action)
        element_menu.addAction(check_action)
        
        select_action = QAction("Select Option", self)
        select_action.triggered.connect(self.add_select_option_action)
        element_menu.addAction(select_action)
        
        extract_action = QAction("Extract Text", self)
        extract_action.triggered.connect(self.add_extract_text_action)
        element_menu.addAction(extract_action)
        
        # Wait actions submenu
        wait_menu = menu.addMenu("Wait Actions")
        
        wait_element_action = QAction("Wait for Element", self)
        wait_element_action.triggered.connect(self.add_wait_for_element_action)
        wait_menu.addAction(wait_element_action)
        
        wait_time_action = QAction("Wait Time", self)
        wait_time_action.triggered.connect(self.add_wait_time_action)
        wait_menu.addAction(wait_time_action)
        
        # Verification actions submenu
        verify_menu = menu.addMenu("Verification Actions")
        
        verify_exists_action = QAction("Verify Element Exists", self)
        verify_exists_action.triggered.connect(self.add_verify_exists_action)
        verify_menu.addAction(verify_exists_action)
        
        verify_text_action = QAction("Verify Text", self)
        verify_text_action.triggered.connect(self.add_verify_text_action)
        verify_menu.addAction(verify_text_action)
        
        # Data generation actions submenu
        generate_menu = menu.addMenu("Generate Data")
        
        generate_name_action = QAction("Generate Name", self)
        generate_name_action.triggered.connect(self.add_generate_name_action)
        generate_menu.addAction(generate_name_action)
        
        generate_email_action = QAction("Generate Email", self)
        generate_email_action.triggered.connect(self.add_generate_email_action)
        generate_menu.addAction(generate_email_action)
        
        generate_number_action = QAction("Generate Number", self)
        generate_number_action.triggered.connect(self.add_generate_number_action)
        generate_menu.addAction(generate_number_action)
        
        generate_date_action = QAction("Generate Date", self)
        generate_date_action.triggered.connect(self.add_generate_date_action)
        generate_menu.addAction(generate_date_action)
        
        generate_custom_action = QAction("Generate Custom Format", self)
        generate_custom_action.triggered.connect(self.add_generate_custom_action)
        generate_menu.addAction(generate_custom_action)
        
        # Excel actions submenu
        excel_menu = menu.addMenu("Excel Actions")
        
        excel_export_action = QAction("Export to Excel", self)
        excel_export_action.triggered.connect(self.add_excel_export_action)
        excel_menu.addAction(excel_export_action)
        
        excel_import_action = QAction("Import from Excel", self)
        excel_import_action.triggered.connect(self.add_excel_import_action)
        excel_menu.addAction(excel_import_action)
        
        # Show menu
        menu.exec(self.new_action_button.mapToGlobal(self.new_action_button.rect().bottomLeft()))
    
    def add_action_card(self, action_name, action_data):
        """
        Add an action card to the workflow
        
        Args:
            action_name: Human-readable name of the action
            action_data: Action data
        """
        # Create card
        card = ActionCard(action_name, action_data, self)
        
        # Connect signals
        card.delete_requested.connect(self.delete_action_card)
        card.edit_requested.connect(self.edit_action_card)
        
        # Add to layout (before the add button)
        self.action_layout.insertWidget(self.action_layout.count() - 1, card)
        
        # Add to list
        self.action_cards.append(card)
        
        # Add to workflow
        self.current_workflow["steps"].append({
            "name": action_name,
            "data": action_data
        })
    
    def clear_action_cards(self):
        """Clear all action cards from the UI"""
        # Remove all cards
        for card in self.action_cards:
            self.action_layout.removeWidget(card)
            card.deleteLater()
        
        # Clear list
        self.action_cards = []
    
    def delete_action_card(self, card):
        """
        Delete an action card
        
        Args:
            card: ActionCard to delete
        """
        # Get index of card
        index = self.action_cards.index(card)
        
        # Remove from layout
        self.action_layout.removeWidget(card)
        card.deleteLater()
        
        # Remove from list
        self.action_cards.remove(card)
        
        # Remove from workflow
        self.current_workflow["steps"].pop(index)
    
    def edit_action_card(self, card):
        """
        Edit an action card
        
        Args:
            card: ActionCard to edit
        """
        # Get index of card
        index = self.action_cards.index(card)
        
        # Get action data
        action_name = card.action_name
        action_data = card.action_data
        
        # Show dialog based on action type
        action_type = action_data.get("action_type", "unknown")
        
        if action_type == "navigate":
            self.edit_navigate_action(index)
        elif action_type == "click":
            self.edit_click_action(index)
        elif action_type == "input_text":
            self.edit_input_text_action(index)
        elif action_type == "extract_text":
            self.edit_extract_text_action(index)
        else:
            # Generic dialog
            QMessageBox.information(
                self,
                "Edit Action",
                f"Editing for {action_name} is not implemented yet."
            )
    
    def on_workflow_refresh(self, data):
        """
        Handle workflow refresh message
        
        Args:
            data: Refresh data
        """
        action = data.get("action", "")
        
        if action == "add":
            action_name = data.get("action_name", "Unknown Action")
            action_data = data.get("action_data", {})
            
            self.add_action_card(action_name, action_data)
        
        elif action == "update":
            index = data.get("index", -1)
            action_name = data.get("action_name", "Unknown Action")
            action_data = data.get("action_data", {})
            
            if 0 <= index < len(self.action_cards):
                # Update workflow
                self.current_workflow["steps"][index] = {
                    "name": action_name,
                    "data": action_data
                }
                
                # Update UI
                old_card = self.action_cards[index]
                new_card = ActionCard(action_name, action_data, self)
                
                # Connect signals
                new_card.delete_requested.connect(self.delete_action_card)
                new_card.edit_requested.connect(self.edit_action_card)
                
                # Replace in layout
                self.action_layout.replaceWidget(old_card, new_card)
                old_card.deleteLater()
                
                # Update list
                self.action_cards[index] = new_card
        
        elif action == "remove":
            index = data.get("index", -1)
            
            if 0 <= index < len(self.action_cards):
                # Get card
                card = self.action_cards[index]
                
                # Delete card
                self.delete_action_card(card)
        
        elif action == "clear":
            # Clear workflow
            self.current_workflow["steps"] = []
            
            # Clear UI
            self.clear_action_cards()
    
    def get_current_workflow(self):
        """
        Get the current workflow
        
        Returns:
            dict: Current workflow
        """
        return self.current_workflow
    
    def load_workflow(self, file_path):
        """
        Load workflow from file
        
        Args:
            file_path: Path to workflow file
        """
        try:
            # Load workflow from file
            with open(file_path, 'r') as f:
                workflow = json.load(f)
            
            # Update current workflow
            self.current_workflow = workflow
            
            # Clear UI
            self.clear_action_cards()
            
            # Add action cards
            for step in workflow.get("steps", []):
                action_name = step.get("name", "Unknown Action")
                action_data = step.get("data", {})
                
                self.add_action_card(action_name, action_data)
            
            # Update UI
            self.message_bus.publish(MessageTypes.UI_STATUS_UPDATE, f"Workflow loaded from {file_path}")
            
            # Publish message
            self.message_bus.publish(MessageTypes.WORKFLOW_LOADED, {
                "workflow": workflow
            })
        except Exception as e:
            logger.error(f"Error loading workflow: {e}")
            raise
    
    def save_workflow(self, file_path):
        """
        Save workflow to file
        
        Args:
            file_path: Path to save workflow file
        """
        try:
            # Save workflow to file
            with open(file_path, 'w') as f:
                json.dump(self.current_workflow, f, indent=2)
            
            # Update UI
            self.message_bus.publish(MessageTypes.UI_STATUS_UPDATE, f"Workflow saved to {file_path}")
            
            # Publish message
            self.message_bus.publish(MessageTypes.WORKFLOW_SAVED, {
                "file_path": file_path
            })
        except Exception as e:
            logger.error(f"Error saving workflow: {e}")
            raise
    
    # Action specific methods
    def add_navigate_action(self):
        """Add navigate action"""
        # TODO: Implement dialog to get URL
        url = "https://example.com"  # This would come from a dialog
        
        # Create action data
        action_data = {
            "action_type": "navigate",
            "url": url
        }
        
        # Add action to workflow
        self.add_action_card("Navigate to URL", action_data)
    
    def add_click_action(self):
        """Add click action"""
        # Show message to select element
        QMessageBox.information(
            self,
            "Select Element",
            "Please click the 'Select Element' button in the browser toolbar, then click on the element you want to interact with."
        )
    
    def add_input_text_action(self):
        """Add input text action"""
        # Show message to select element
        QMessageBox.information(
            self,
            "Select Element",
            "Please click the 'Select Element' button in the browser toolbar, then click on the element you want to interact with."
        )
    
    def add_clear_field_action(self):
        """Add clear field action"""
        # Show message to select element
        QMessageBox.information(
            self,
            "Select Element",
            "Please click the 'Select Element' button in the browser toolbar, then click on the element you want to interact with."
        )
    
    def add_check_action(self):
        """Add check action"""
        # Show message to select element
        QMessageBox.information(
            self,
            "Select Element",
            "Please click the 'Select Element' button in the browser toolbar, then click on the element you want to interact with."
        )
    
    def add_select_option_action(self):
        """Add select option action"""
        # Show message to select element
        QMessageBox.information(
            self,
            "Select Element",
            "Please click the 'Select Element' button in the browser toolbar, then click on the element you want to interact with."
        )
    
    def add_extract_text_action(self):
        """Add extract text action"""
        # Show message to select element
        QMessageBox.information(
            self,
            "Select Element",
            "Please click the 'Select Element' button in the browser toolbar, then click on the element you want to interact with."
        )
    
    def add_wait_for_element_action(self):
        """Add wait for element action"""
        # Show message to select element
        QMessageBox.information(
            self,
            "Select Element",
            "Please click the 'Select Element' button in the browser toolbar, then click on the element you want to interact with."
        )
    
    def add_wait_time_action(self):
        """Add wait time action"""
        # TODO: Implement dialog to get wait time
        seconds = 5  # This would come from a dialog
        
        # Create action data
        action_data = {
            "action_type": "wait_time",
            "seconds": seconds
        }
        
        # Add action to workflow
        self.add_action_card("Wait Time", action_data)
    
    def add_verify_exists_action(self):
        """Add verify exists action"""
        # Show message to select element
        QMessageBox.information(
            self,
            "Select Element",
            "Please click the 'Select Element' button in the browser toolbar, then click on the element you want to interact with."
        )
    
    def add_verify_text_action(self):
        """Add verify text action"""
        # Show message to select element
        QMessageBox.information(
            self,
            "Select Element",
            "Please click the 'Select Element' button in the browser toolbar, then click on the element you want to interact with."
        )
    
    def add_generate_name_action(self):
        """Add generate name action"""
        # Show message to select element
        QMessageBox.information(
            self,
            "Select Element",
            "Please click the 'Select Element' button in the browser toolbar, then click on the element you want to interact with."
        )
    
    def add_generate_email_action(self):
        """Add generate email action"""
        # Show message to select element
        QMessageBox.information(
            self,
            "Select Element",
            "Please click the 'Select Element' button in the browser toolbar, then click on the element you want to interact with."
        )
    
    def add_generate_number_action(self):
        """Add generate number action"""
        # Show message to select element
        QMessageBox.information(
            self,
            "Select Element",
            "Please click the 'Select Element' button in the browser toolbar, then click on the element you want to interact with."
        )
    
    def add_generate_date_action(self):
        """Add generate date action"""
        # Show message to select element
        QMessageBox.information(
            self,
            "Select Element",
            "Please click the 'Select Element' button in the browser toolbar, then click on the element you want to interact with."
        )
    
    def add_generate_custom_action(self):
        """Add generate custom action"""
        # Show message to select element
        QMessageBox.information(
            self,
            "Select Element",
            "Please click the 'Select Element' button in the browser toolbar, then click on the element you want to interact with."
        )
    
    def add_excel_export_action(self):
        """Add excel export action"""
        # TODO: Implement dialog to configure export
        
        # Create action data
        action_data = {
            "action_type": "excel_export",
            "file_path": "data/export.xlsx",
            "variables": ["firstName", "lastName", "email"]
        }
        
        # Add action to workflow
        self.add_action_card("Export to Excel", action_data)
    
    def add_excel_import_action(self):
        """Add excel import action"""
        # TODO: Implement dialog to configure import
        
        # Create action data
        action_data = {
            "action_type": "excel_import",
            "file_path": "data/import.xlsx",
            "sheet_name": "Sheet1",
            "start_row": 2,
            "mappings": {
                "A": "firstName",
                "B": "lastName",
                "C": "email"
            }
        }
        
        # Add action to workflow
        self.add_action_card("Import from Excel", action_data)
    
    def edit_navigate_action(self, index):
        """
        Edit navigate action
        
        Args:
            index: Index of action in workflow
        """
        # Get action data
        action_data = self.current_workflow["steps"][index]["data"]
        
        # Get current URL
        current_url = action_data.get("url", "")
        
        # TODO: Implement dialog to edit URL
        new_url = current_url  # This would come from a dialog
        
        # Update action data
        action_data["url"] = new_url
        
        # Update workflow
        self.message_bus.publish(MessageTypes.UI_REFRESH_WORKFLOW, {
            "action": "update",
            "index": index,
            "action_name": "Navigate to URL",
            "action_data": action_data
        })
    
    def edit_click_action(self, index):
        """
        Edit click action
        
        Args:
            index: Index of action in workflow
        """
        # Show message to select element
        QMessageBox.information(
            self,
            "Select Element",
            "Please click the 'Select Element' button in the browser toolbar, then click on the element you want to interact with."
        )
    
    def edit_input_text_action(self, index):
        """
        Edit input text action
        
        Args:
            index: Index of action in workflow
        """
        # Get action data
        action_data = self.current_workflow["steps"][index]["data"]
        
        # Get current text
        current_text = action_data.get("text", "")
        
        # TODO: Implement dialog to edit text
        new_text = current_text  # This would come from a dialog
        
        # Update action data
        action_data["text"] = new_text
        
        # Update workflow
        self.message_bus.publish(MessageTypes.UI_REFRESH_WORKFLOW, {
            "action": "update",
            "index": index,
            "action_name": "Input Text",
            "action_data": action_data
        })
    
    def edit_extract_text_action(self, index):
        """
        Edit extract text action
        
        Args:
            index: Index of action in workflow
        """
        # Get action data
        action_data = self.current_workflow["steps"][index]["data"]
        
        # Get current variable name
        current_variable_name = action_data.get("variable_name", "")
        
        # TODO: Implement dialog to edit variable name
        new_variable_name = current_variable_name  # This would come from a dialog
        
        # Update action data
        action_data["variable_name"] = new_variable_name
        
        # Update workflow
        self.message_bus.publish(MessageTypes.UI_REFRESH_WORKFLOW, {
            "action": "update",
            "index": index,
            "action_name": "Extract Text",
            "action_data": action_data
        })