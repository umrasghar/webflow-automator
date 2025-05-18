# ui/variable_panel.py
# WebFlow Automator - Variable Panel
# This module contains the variable management UI component

import logging
import json
from typing import Dict, Any, List, Optional

# Dynamically import the correct UI framework
try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
        QFrame, QMenu, QToolButton, QDialog, QLineEdit, QCheckBox, QComboBox,
        QSpinBox, QDateEdit, QMessageBox, QListWidget, QListWidgetItem, QGroupBox,
        QFormLayout, QSplitter, QTableWidget, QTableWidgetItem, QHeaderView
    )
    from PyQt6.QtCore import Qt, QSize, pyqtSignal, QDateTime
    from PyQt6.QtGui import QIcon, QAction, QDrag, QPixmap
    USE_PYQT6 = True
except ImportError:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
        QFrame, QMenu, QToolButton, QDialog, QLineEdit, QCheckBox, QComboBox,
        QSpinBox, QDateEdit, QMessageBox, QListWidget, QListWidgetItem, QGroupBox,
        QFormLayout, QSplitter, QTableWidget, QTableWidgetItem, QHeaderView
    )
    from PySide6.QtCore import Qt, QSize, Signal as pyqtSignal, QDateTime
    from PySide6.QtGui import QIcon, QAction, QDrag, QPixmap
    USE_PYQT6 = False

from core.message_bus import MessageBus, MessageTypes

logger = logging.getLogger("WebFlowAutomator.UI.VariablePanel")

class VariableDialog(QDialog):
    """
    Dialog for adding or editing variables
    """
    
    def __init__(self, parent=None, variable_name="", variable_value="", variable_type="text"):
        """
        Initialize the variable dialog
        
        Args:
            parent: Parent widget
            variable_name: Initial variable name
            variable_value: Initial variable value
            variable_type: Initial variable type
        """
        super().__init__(parent)
        
        self.variable_name = variable_name
        self.variable_value = variable_value
        self.variable_type = variable_type
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface"""
        # Set window properties
        self.setWindowTitle("Variable" if not self.variable_name else f"Edit Variable: {self.variable_name}")
        self.resize(400, 250)
        
        # Create layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(10)
        
        # Create form layout
        self.form_layout = QFormLayout()
        self.form_layout.setContentsMargins(0, 0, 0, 0)
        self.form_layout.setSpacing(10)
        
        # Create name field
        self.name_field = QLineEdit(self.variable_name)
        self.name_field.setPlaceholderText("Enter variable name")
        self.form_layout.addRow("Name:", self.name_field)
        
        # Create type field
        self.type_field = QComboBox()
        self.type_field.addItems(["text", "number", "date", "boolean"])
        self.type_field.setCurrentText(self.variable_type)
        self.type_field.currentTextChanged.connect(self.on_type_changed)
        self.form_layout.addRow("Type:", self.type_field)
        
        # Create value field (will be replaced based on type)
        self.value_container = QWidget()
        self.value_layout = QHBoxLayout(self.value_container)
        self.value_layout.setContentsMargins(0, 0, 0, 0)
        self.setup_value_field()
        self.form_layout.addRow("Value:", self.value_container)
        
        # Add form layout to main layout
        self.layout.addLayout(self.form_layout)
        
        # Add spacer
        self.layout.addStretch()
        
        # Create button layout
        self.button_layout = QHBoxLayout()
        self.button_layout.setContentsMargins(0, 10, 0, 0)
        
        # Create cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.button_layout.addWidget(self.cancel_button)
        
        # Create save button
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.accept)
        self.button_layout.addWidget(self.save_button)
        
        # Add button layout to main layout
        self.layout.addLayout(self.button_layout)
        
        # Apply stylesheet
        self.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #f5f5f7;
                border: 1px solid #d1d1d6;
                border-radius: 4px;
            }
            
            QPushButton:hover {
                background-color: #e5e5ea;
            }
            
            QPushButton:pressed {
                background-color: #d1d1d6;
            }
            
            QPushButton:default {
                background-color: #007aff;
                color: white;
                border: 1px solid #0062cc;
            }
            
            QPushButton:default:hover {
                background-color: #0062cc;
            }
            
            QPushButton:default:pressed {
                background-color: #004999;
            }
        """)
        
        # Set default button
        self.save_button.setDefault(True)
    
    def setup_value_field(self):
        """Set up the value field based on the current type"""
        # Clear current layout
        while self.value_layout.count():
            item = self.value_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Create field based on type
        if self.type_field.currentText() == "text":
            self.value_field = QLineEdit(str(self.variable_value))
            self.value_layout.addWidget(self.value_field)
        
        elif self.type_field.currentText() == "number":
            self.value_field = QSpinBox()
            self.value_field.setMinimum(-1000000)
            self.value_field.setMaximum(1000000)
            try:
                self.value_field.setValue(int(self.variable_value))
            except (ValueError, TypeError):
                self.value_field.setValue(0)
            self.value_layout.addWidget(self.value_field)
        
        elif self.type_field.currentText() == "date":
            self.value_field = QDateEdit()
            self.value_field.setCalendarPopup(True)
            self.value_field.setDisplayFormat("yyyy-MM-dd")
            try:
                date = QDateTime.fromString(str(self.variable_value), "yyyy-MM-dd")
                if date.isValid():
                    self.value_field.setDateTime(date)
                else:
                    self.value_field.setDateTime(QDateTime.currentDateTime())
            except (ValueError, TypeError):
                self.value_field.setDateTime(QDateTime.currentDateTime())
            self.value_layout.addWidget(self.value_field)
        
        elif self.type_field.currentText() == "boolean":
            self.value_field = QCheckBox()
            try:
                self.value_field.setChecked(bool(self.variable_value))
            except (ValueError, TypeError):
                self.value_field.setChecked(False)
            self.value_layout.addWidget(self.value_field)
    
    def on_type_changed(self, type_text):
        """
        Handle type change
        
        Args:
            type_text: New type text
        """
        self.setup_value_field()
    
    def get_variable(self):
        """
        Get the variable data
        
        Returns:
            tuple: (name, value, type)
        """
        name = self.name_field.text()
        type_text = self.type_field.currentText()
        
        # Get value based on type
        if type_text == "text":
            value = self.value_field.text()
        elif type_text == "number":
            value = self.value_field.value()
        elif type_text == "date":
            value = self.value_field.date().toString("yyyy-MM-dd")
        elif type_text == "boolean":
            value = self.value_field.isChecked()
        else:
            value = ""
        
        return (name, value, type_text)


class VariablePanel(QWidget):
    """
    Panel for managing variables
    """
    
    def __init__(self, modules: Dict[str, Any]):
        """
        Initialize the variable panel
        
        Args:
            modules: Dictionary containing application modules
        """
        super().__init__()
        
        self.modules = modules
        self.message_bus = modules["message_bus"]
        self.variable_storage = modules.get("variable_storage")
        
        # Initialize UI
        self.setup_ui()
        
        # Connect to message bus
        self.message_bus.subscribe(MessageTypes.UI_REFRESH_VARIABLES, self.on_variables_refresh)
        self.message_bus.subscribe(MessageTypes.VARIABLE_CREATED, self.on_variable_created)
        self.message_bus.subscribe(MessageTypes.VARIABLE_UPDATED, self.on_variable_updated)
        self.message_bus.subscribe(MessageTypes.VARIABLE_DELETED, self.on_variable_deleted)
    
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
            border-top: 1px solid #d1d1d6;
            border-bottom: 1px solid #d1d1d6;
        """)
        
        self.header_layout = QHBoxLayout(self.header)
        self.header_layout.setContentsMargins(10, 0, 10, 0)
        
        self.header_label = QLabel("Variables")
        self.header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.header_layout.addWidget(self.header_label)
        
        self.header_layout.addStretch()
        
        # Add variable button
        self.add_button = QToolButton()
        self.add_button.setText("+")
        self.add_button.setToolTip("Add Variable")
        self.add_button.clicked.connect(self.add_variable)
        self.header_layout.addWidget(self.add_button)
        
        self.layout.addWidget(self.header)
        
        # Create table
        self.variable_table = QTableWidget()
        self.variable_table.setColumnCount(4)  # Name, Type, Value, Actions
        self.variable_table.setHorizontalHeaderLabels(["Name", "Type", "Value", ""])
        self.variable_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.variable_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.variable_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.variable_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.variable_table.verticalHeader().setVisible(False)
        self.variable_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.variable_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.variable_table.setAlternatingRowColors(True)
        
        self.layout.addWidget(self.variable_table)
        
        # Set maximum height
        self.setMinimumHeight(200)
        self.setMaximumHeight(300)
        
        # Apply stylesheet
        self.variable_table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                alternate-background-color: #f5f5f7;
                gridline-color: #d1d1d6;
            }
            
            QHeaderView::section {
                background-color: #f5f5f7;
                padding: 4px;
                border: 1px solid #d1d1d6;
                font-weight: bold;
            }
            
            QToolButton {
                border: none;
                background-color: transparent;
                padding: 4px;
                border-radius: 4px;
            }
            
            QToolButton:hover {
                background-color: #e5e5ea;
            }
            
            QToolButton:pressed {
                background-color: #d1d1d6;
            }
        """)
        
        # Populate variables
        self.refresh_variables()
    
    def refresh_variables(self):
        """Refresh the variable table from storage"""
        # Clear table
        self.variable_table.setRowCount(0)
        
        # Get variables from storage
        if self.variable_storage:
            variables = self.variable_storage.get_all_variables()
        else:
            # Fallback to empty list if storage not available
            variables = []
        
        # Populate table
        for i, var in enumerate(variables):
            name = var.get("name", "")
            value = var.get("value", "")
            var_type = var.get("type", "text")
            
            self.variable_table.insertRow(i)
            
            # Name
            name_item = QTableWidgetItem(name)
            self.variable_table.setItem(i, 0, name_item)
            
            # Type
            type_item = QTableWidgetItem(var_type)
            self.variable_table.setItem(i, 1, type_item)
            
            # Value
            value_item = QTableWidgetItem(str(value))
            self.variable_table.setItem(i, 2, value_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(4)
            
            edit_button = QToolButton()
            edit_button.setText("✎")
            edit_button.setToolTip("Edit Variable")
            edit_button.clicked.connect(lambda checked, idx=i: self.edit_variable(idx))
            actions_layout.addWidget(edit_button)
            
            delete_button = QToolButton()
            delete_button.setText("✕")
            delete_button.setToolTip("Delete Variable")
            delete_button.clicked.connect(lambda checked, idx=i: self.delete_variable(idx))
            actions_layout.addWidget(delete_button)
            
            self.variable_table.setCellWidget(i, 3, actions_widget)
    
    def add_variable(self):
        """Add a new variable"""
        dialog = VariableDialog(self)
        
        if dialog.exec():
            # Get variable data
            name, value, var_type = dialog.get_variable()
            
            # Validate
            if not name:
                QMessageBox.warning(self, "Warning", "Variable name cannot be empty")
                return
            
            # Check for duplicate
            if self.variable_storage:
                existing = self.variable_storage.get_variable(name)
                if existing is not None:
                    QMessageBox.warning(self, "Warning", f"Variable '{name}' already exists")
                    return
            
            # Create variable
            if self.variable_storage:
                self.variable_storage.set_variable(name, value, var_type)
            
            # Refresh table
            self.refresh_variables()
            
            # Publish message
            self.message_bus.publish(MessageTypes.UI_STATUS_UPDATE, f"Variable '{name}' created")
    
    def edit_variable(self, index):
        """
        Edit a variable
        
        Args:
            index: Row index of variable
        """
        # Get variable data
        name = self.variable_table.item(index, 0).text()
        var_type = self.variable_table.item(index, 1).text()
        value = self.variable_table.item(index, 2).text()
        
        # Show dialog
        dialog = VariableDialog(self, name, value, var_type)
        
        if dialog.exec():
            # Get new variable data
            new_name, new_value, new_type = dialog.get_variable()
            
            # Validate
            if not new_name:
                QMessageBox.warning(self, "Warning", "Variable name cannot be empty")
                return
            
            # Check for duplicate if name changed
            if new_name != name and self.variable_storage:
                existing = self.variable_storage.get_variable(new_name)
                if existing is not None:
                    QMessageBox.warning(self, "Warning", f"Variable '{new_name}' already exists")
                    return
            
            # Update variable
            if self.variable_storage:
                if new_name != name:
                    # Remove old variable
                    self.variable_storage.delete_variable(name)
                    
                    # Add new variable
                    self.variable_storage.set_variable(new_name, new_value, new_type)
                else:
                    # Update existing variable
                    self.variable_storage.set_variable(name, new_value, new_type)
            
            # Refresh table
            self.refresh_variables()
            
            # Publish message
            self.message_bus.publish(MessageTypes.UI_STATUS_UPDATE, f"Variable '{name}' updated")
    
    def delete_variable(self, index):
        """
        Delete a variable
        
        Args:
            index: Row index of variable
        """
        # Get variable name
        name = self.variable_table.item(index, 0).text()
        
        # Confirm
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete the variable '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Delete variable
        if self.variable_storage:
            self.variable_storage.delete_variable(name)
        
        # Refresh table
        self.refresh_variables()
        
        # Publish message
        self.message_bus.publish(MessageTypes.UI_STATUS_UPDATE, f"Variable '{name}' deleted")
    
    def on_variables_refresh(self, data):
        """
        Handle variables refresh message
        
        Args:
            data: Refresh data
        """
        self.refresh_variables()
    
    def on_variable_created(self, data):
        """
        Handle variable created message
        
        Args:
            data: Variable data
        """
        self.refresh_variables()
    
    def on_variable_updated(self, data):
        """
        Handle variable updated message
        
        Args:
            data: Variable data
        """
        self.refresh_variables()
    
    def on_variable_deleted(self, data):
        """
        Handle variable deleted message
        
        Args:
            data: Variable data
        """
        self.refresh_variables()