# ui/main_window.py
# WebFlow Automator - Main Window
# This module contains the main application window and UI layout

import os
import logging
from typing import Dict, Any, List, Optional

# Dynamically import the correct UI framework
try:
    from PyQt6.QtWidgets import (
        QMainWindow, QSplitter, QWidget, QVBoxLayout, QHBoxLayout, 
        QToolBar, QStatusBar, QMessageBox, QFileDialog, QMenu
    )
    from PyQt6.QtCore import Qt, QSettings, QSize, QUrl
    from PyQt6.QtGui import QIcon, QKeySequence, QAction  # QAction moved here
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    USE_PYQT6 = True
except ImportError:
    from PySide6.QtWidgets import (
        QMainWindow, QSplitter, QWidget, QVBoxLayout, QHBoxLayout, 
        QToolBar, QStatusBar, QMessageBox, QFileDialog, QMenu
    )
    from PySide6.QtCore import Qt, QSettings, QSize, QUrl
    from PySide6.QtGui import QIcon, QKeySequence, QAction  # QAction moved here
    from PySide6.QtWebEngineWidgets import QWebEngineView
    USE_PYQT6 = False

from core.message_bus import MessageBus, MessageTypes
from ui.browser_view import BrowserView
from ui.workflow_panel import WorkflowPanel
from ui.variable_panel import VariablePanel
from ui.element_selector import ElementSelector

logger = logging.getLogger("WebFlowAutomator.UI.MainWindow")

class MainWindow(QMainWindow):
    """
    Main application window for WebFlow Automator
    
    This class is responsible for initializing and managing the main UI components.
    """
    
    def __init__(self, modules: Dict[str, Any], settings: QSettings):
        """
        Initialize the main window
        
        Args:
            modules: Dictionary containing application modules
            settings: Application settings
        """
        super().__init__()
        
        self.modules = modules
        self.settings = settings
        self.message_bus = modules["message_bus"]
        
        # Create UI components first - important to initialize these before other setup
        self.create_ui_components()
        
        # Now set up UI layout and connections
        self.setup_ui()
        
        # Connect to message bus
        self.message_bus.subscribe(MessageTypes.UI_STATUS_UPDATE, self.update_status)
        self.message_bus.subscribe(MessageTypes.WORKFLOW_STARTED, self.on_workflow_started)
        self.message_bus.subscribe(MessageTypes.WORKFLOW_COMPLETED, self.on_workflow_completed)
        self.message_bus.subscribe(MessageTypes.WORKFLOW_STEP_STARTED, self.on_workflow_step_started)
        
        # Notify that UI is ready
        self.message_bus.publish(MessageTypes.UI_READY)
        
        # Set initial status
        self.update_status("Ready")
    
    def create_ui_components(self):
        """Create all UI components before layout setup"""
        # Create browser view
        self.browser_view = BrowserView(self.modules)
        
        # Create workflow panel
        self.workflow_panel = WorkflowPanel(self.modules)
        
        # Create variable panel
        self.variable_panel = VariablePanel(self.modules)
        
        # Create toolbar
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QSize(24, 24))
        
        # Create status bar
        self.status_bar = QStatusBar()
    
    def setup_ui(self):
        """Set up the user interface"""
        # Set window properties
        self.setWindowTitle("WebFlow Automator")
        self.setMinimumSize(1200, 800)
        
        # Restore window geometry from settings if available
        geometry = self.settings.value("mainwindow/geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            # Center on screen if first time
            self.resize(1400, 900)
        
        # Set up central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create main layout
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Add toolbar to the main window
        self.addToolBar(self.toolbar)
        self.setup_toolbar()
        
        # Create main splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_layout.addWidget(self.main_splitter)
        
        # Add browser view to splitter
        self.main_splitter.addWidget(self.browser_view)
        
        # Create right side panel
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.main_splitter.addWidget(self.right_panel)
        
        # Add workflow panel to right layout
        self.right_layout.addWidget(self.workflow_panel)
        
        # Add variable panel to right layout
        self.right_layout.addWidget(self.variable_panel)
        
        # Set splitter sizes
        self.main_splitter.setSizes([600, 400])
        
        # Set status bar
        self.setStatusBar(self.status_bar)
        
        # Apply stylesheet for modern look
        self.apply_stylesheet()
    
    def setup_toolbar(self):
        """Set up the main toolbar"""
        # Navigation actions
        self.action_back = QAction("Back", self)
        self.action_back.setShortcut(QKeySequence.StandardKey.Back)
        self.action_back.triggered.connect(self.browser_view.go_back)
        self.toolbar.addAction(self.action_back)
        
        self.action_forward = QAction("Forward", self)
        self.action_forward.setShortcut(QKeySequence.StandardKey.Forward)
        self.action_forward.triggered.connect(self.browser_view.go_forward)
        self.toolbar.addAction(self.action_forward)
        
        self.action_reload = QAction("Reload", self)
        self.action_reload.setShortcut(QKeySequence.StandardKey.Refresh)
        self.action_reload.triggered.connect(self.browser_view.reload)
        self.toolbar.addAction(self.action_reload)
        
        self.toolbar.addSeparator()
        
        # URL field (will be added in a future version)
        
        self.toolbar.addSeparator()
        
        # Workflow actions
        self.action_new_workflow = QAction("New Workflow", self)
        self.action_new_workflow.triggered.connect(self.workflow_panel.new_workflow)
        self.toolbar.addAction(self.action_new_workflow)
        
        self.action_open_workflow = QAction("Open Workflow", self)
        self.action_open_workflow.triggered.connect(self.open_workflow)
        self.toolbar.addAction(self.action_open_workflow)
        
        self.action_save_workflow = QAction("Save Workflow", self)
        self.action_save_workflow.setShortcut(QKeySequence.StandardKey.Save)
        self.action_save_workflow.triggered.connect(self.save_workflow)
        self.toolbar.addAction(self.action_save_workflow)
        
        self.toolbar.addSeparator()
        
        # Execution actions
        self.action_start = QAction("Start", self)
        self.action_start.triggered.connect(self.start_workflow)
        self.toolbar.addAction(self.action_start)
        
        self.action_pause = QAction("Pause", self)
        self.action_pause.setEnabled(False)
        self.action_pause.triggered.connect(self.pause_workflow)
        self.toolbar.addAction(self.action_pause)
        
        self.action_stop = QAction("Stop", self)
        self.action_stop.setEnabled(False)
        self.action_stop.triggered.connect(self.stop_workflow)
        self.toolbar.addAction(self.action_stop)
        
        self.toolbar.addSeparator()
        
        # Settings action
        self.action_settings = QAction("Settings", self)
        self.action_settings.triggered.connect(self.show_settings)
        self.toolbar.addAction(self.action_settings)
    
    def apply_stylesheet(self):
        """Apply custom stylesheet for modern UI look"""
        # Define stylesheet
        stylesheet = """
        QMainWindow {
            background-color: #f5f5f7;
        }
        
        QSplitter::handle {
            background-color: #d1d1d6;
        }
        
        QToolBar {
            background-color: #ffffff;
            border-bottom: 1px solid #d1d1d6;
            spacing: 5px;
            padding: 2px;
        }
        
        QToolBar QToolButton {
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: 4px;
            padding: 4px;
        }
        
        QToolBar QToolButton:hover {
            background-color: #f0f0f0;
            border: 1px solid #d1d1d6;
        }
        
        QToolBar QToolButton:pressed {
            background-color: #e0e0e0;
        }
        
        QStatusBar {
            background-color: #ffffff;
            border-top: 1px solid #d1d1d6;
        }
        
        QGroupBox {
            border: 1px solid #d1d1d6;
            border-radius: 4px;
            margin-top: 0.5em;
            padding-top: 0.5em;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 3px 0 3px;
        }
        """
        
        # Apply the stylesheet
        self.setStyleSheet(stylesheet)
    
    def update_status(self, message):
        """
        Update the status bar with a message
        
        Args:
            message: Status message to display
        """
        self.status_bar.showMessage(message)
    
    def on_workflow_started(self, data):
        """
        Handle workflow started event
        
        Args:
            data: Workflow data
        """
        # Update UI state
        self.action_start.setEnabled(False)
        self.action_pause.setEnabled(True)
        self.action_stop.setEnabled(True)
        
        # Update status
        workflow_name = data.get("name", "Unnamed workflow")
        self.update_status(f"Running workflow: {workflow_name}")
    
    def on_workflow_completed(self, data):
        """
        Handle workflow completed event
        
        Args:
            data: Workflow completion data
        """
        # Update UI state
        self.action_start.setEnabled(True)
        self.action_pause.setEnabled(False)
        self.action_stop.setEnabled(False)
        
        # Update status
        status = data.get("status", "unknown")
        if status == "success":
            self.update_status("Workflow completed successfully")
        elif status == "error":
            error_message = data.get("error", "Unknown error")
            self.update_status(f"Workflow failed: {error_message}")
        elif status == "stopped":
            self.update_status("Workflow stopped by user")
        else:
            self.update_status("Workflow completed")
    
    def on_workflow_step_started(self, data):
        """
        Handle workflow step started event
        
        Args:
            data: Step data
        """
        # Update status
        step_name = data.get("name", "Unknown step")
        step_number = data.get("number", 0)
        total_steps = data.get("total", 0)
        
        if total_steps > 0:
            self.update_status(f"Running step {step_number}/{total_steps}: {step_name}")
        else:
            self.update_status(f"Running step: {step_name}")
    
    def open_workflow(self):
        """Open a workflow from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Workflow",
            os.path.join(os.getcwd(), "workflows"),
            "Workflow Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                # Forward to workflow manager to load
                self.modules["workflow_builder"].load_workflow(file_path)
                self.update_status(f"Workflow loaded from {file_path}")
            except Exception as e:
                logger.error(f"Error opening workflow: {e}")
                QMessageBox.critical(self, "Error", f"Could not open workflow: {str(e)}")
    
    def save_workflow(self):
        """Save the current workflow to file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Workflow",
            os.path.join(os.getcwd(), "workflows"),
            "Workflow Files (*.json);;All Files (*)"
        )
        
        if file_path:
            if not file_path.endswith(".json"):
                file_path += ".json"
                
            try:
                # Forward to workflow manager to save
                self.modules["workflow_builder"].save_workflow(file_path)
                self.update_status(f"Workflow saved to {file_path}")
            except Exception as e:
                logger.error(f"Error saving workflow: {e}")
                QMessageBox.critical(self, "Error", f"Could not save workflow: {str(e)}")
    
    def start_workflow(self):
        """Start the current workflow"""
        try:
            # Get the current workflow from the workflow panel
            workflow = self.workflow_panel.get_current_workflow()
            
            if not workflow or not workflow.get("steps"):
                QMessageBox.warning(self, "Warning", "No workflow steps defined. Please add steps to your workflow first.")
                return
            
            # Start the workflow
            self.modules["execution_engine"].start_workflow(workflow)
        except Exception as e:
            logger.error(f"Error starting workflow: {e}")
            QMessageBox.critical(self, "Error", f"Could not start workflow: {str(e)}")
    
    def pause_workflow(self):
        """Pause the currently running workflow"""
        try:
            self.modules["execution_engine"].pause_workflow()
            self.action_pause.setEnabled(False)
            self.update_status("Workflow paused")
        except Exception as e:
            logger.error(f"Error pausing workflow: {e}")
            QMessageBox.critical(self, "Error", f"Could not pause workflow: {str(e)}")
    
    def stop_workflow(self):
        """Stop the currently running workflow"""
        try:
            self.modules["execution_engine"].stop_workflow()
            self.action_start.setEnabled(True)
            self.action_pause.setEnabled(False)
            self.action_stop.setEnabled(False)
            self.update_status("Workflow stopped")
        except Exception as e:
            logger.error(f"Error stopping workflow: {e}")
            QMessageBox.critical(self, "Error", f"Could not stop workflow: {str(e)}")
    
    def show_settings(self):
        """Show settings dialog"""
        # This will be implemented in a future version
        QMessageBox.information(self, "Settings", "Settings dialog will be implemented in a future version.")
    
    def closeEvent(self, event):
        """
        Handle window close event
        
        Args:
            event: Close event
        """
        # Save window geometry
        self.settings.setValue("mainwindow/geometry", self.saveGeometry())
        
        # Ask for confirmation if workflow is running
        if self.action_stop.isEnabled():
            reply = QMessageBox.question(
                self,
                "Confirm Exit",
                "A workflow is currently running. Are you sure you want to exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
        
        # Notify modules that UI is closing
        self.message_bus.publish(MessageTypes.UI_CLOSING)
        
        # Accept the event
        event.accept()