# main.py
# WebFlow Automator - Main entry point
# This file serves as the entry point for the application and ties all modules together

import sys
import os
import importlib
from packaging.version import parse as parse_version
import subprocess
import logging

# Import configuration
from config import UI_FRAMEWORK, APP_NAME, APP_VERSION

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("webflow_automator.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("WebFlowAutomator")

# Force specific UI framework based on configuration
if UI_FRAMEWORK == "PyQt6":
    # Force PyQt6
    try:
        import PyQt6
        logger.info("Using PyQt6 as UI framework")
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QSettings
    except ImportError:
        logger.warning("PyQt6 not available, installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PyQt6"])
        import PyQt6
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QSettings
elif UI_FRAMEWORK == "PySide6":
    # Force PySide6
    try:
        import PySide6
        logger.info("Using PySide6 as UI framework")
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QSettings
    except ImportError:
        logger.warning("PySide6 not available, installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PySide6"])
        import PySide6
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QSettings
else:
    logger.error(f"Invalid UI framework specified: {UI_FRAMEWORK}")
    sys.exit(1)


def check_dependencies():
    """
    Check and install required dependencies if missing
    """
    logger.info("Checking dependencies...")
    
    required_packages = {
        'selenium': '4.8.0',
        'pandas': '2.0.0',
        'openpyxl': '3.1.0',
        'Faker': '18.0.0',
        'pillow': '9.5.0',
        'packaging': '23.0.0'
    }
    
    missing_packages = []
    
    for package, version in required_packages.items():
        try:
            imported = importlib.import_module(package)
            if hasattr(imported, '__version__'):
                if parse_version(imported.__version__) < parse_version(version):
                    missing_packages.append(f"{package}>={version}")
            else:
                # If no version attribute, assume it's ok
                pass
        except ImportError:
            missing_packages.append(f"{package}>={version}")
    
    if missing_packages:
        logger.info(f"Installing missing dependencies: {missing_packages}")
        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                logger.info(f"Successfully installed {package}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install {package}: {e}")
                sys.exit(1)
        logger.info("All dependencies installed successfully")


def setup_environment():
    """
    Setup application environment
    
    Returns:
        QSettings: Application settings
    """
    # Create necessary directories if they don't exist
    directories = ['data', 'workflows', 'logs', 'temp']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    # Initialize settings
    settings = QSettings("WebFlowAutomator", "WebFlowAutomator")
    
    # Set default settings if first run
    if not settings.contains("first_run"):
        logger.info("First run detected, setting default settings")
        settings.setValue("first_run", False)
        settings.setValue("browser_engine", "chromium")
        settings.setValue("theme", "system")
        settings.setValue("excel_export_path", os.path.join(os.path.expanduser("~"), "Documents"))
        settings.setValue("screenshot_path", os.path.join(os.path.expanduser("~"), "Pictures"))
        settings.setValue("max_browser_instances", 1)
        settings.setValue("auto_save_interval", 5)  # minutes
    
    return settings


def load_modules():
    """
    Load and initialize all application modules
    
    Returns:
        dict: Dictionary containing all initialized modules
    """
    from core.message_bus import MessageBus
    
    # Create message bus for inter-module communication
    message_bus = MessageBus()
    
    # Initialize modules dictionary
    modules = {
        "message_bus": message_bus
    }
    
    # Import modules
    logger.info("Loading UI module...")
    from ui.main_window import MainWindow
    
    logger.info("Loading automation engine module...")
    from automation.browser_controller import BrowserController
    
    logger.info("Loading data manager module...")
    from data.variable_storage import VariableStorage
    from data.data_generator import DataGenerator
    
    logger.info("Loading workflow manager module...")
    from workflow.workflow_builder import WorkflowBuilder
    from workflow.execution_engine import ExecutionEngine
    
    # Initialize modules
    browser_controller = BrowserController(message_bus)
    variable_storage = VariableStorage(message_bus)
    data_generator = DataGenerator()
    workflow_builder = WorkflowBuilder(message_bus)
    execution_engine = ExecutionEngine(message_bus)
    
    # Add modules to dictionary
    modules["browser_controller"] = browser_controller
    modules["variable_storage"] = variable_storage
    modules["data_generator"] = data_generator
    modules["workflow_builder"] = workflow_builder
    modules["execution_engine"] = execution_engine
    
    # Set module references
    execution_engine.set_modules(modules)
    
    logger.info("All modules loaded successfully")
    return modules


def main():
    """
    Main application entry point
    """
    logger.info("Starting WebFlow Automator")
    
    # Check and install dependencies
    check_dependencies()
    
    # Setup environment
    settings = setup_environment()
    
    # Initialize application
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    
    # Set application style based on settings
    theme = settings.value("theme", "system")
    if theme == "dark":
        if UI_FRAMEWORK == "PyQt6":
            app.setStyle("Fusion")
            from PyQt6.QtGui import QPalette, QColor
            palette = QPalette()
            palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
            palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
            palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(0, 0, 0))
            palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.BrightText, QColor(0, 128, 255))
            palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
            palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
            app.setPalette(palette)
        else:  # PySide6
            app.setStyle("Fusion")
            from PySide6.QtGui import QPalette, QColor
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor(53, 53, 53))
            palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
            palette.setColor(QPalette.Base, QColor(25, 25, 25))
            palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
            palette.setColor(QPalette.ToolTipBase, QColor(0, 0, 0))
            palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
            palette.setColor(QPalette.Text, QColor(255, 255, 255))
            palette.setColor(QPalette.Button, QColor(53, 53, 53))
            palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
            palette.setColor(QPalette.BrightText, QColor(0, 128, 255))
            palette.setColor(QPalette.Link, QColor(42, 130, 218))
            palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
            app.setPalette(palette)
    
    # Load and initialize modules
    modules = load_modules()
    
    # Create main window
    from ui.main_window import MainWindow
    main_window = MainWindow(modules, settings)
    main_window.show()
    
    # Start the event loop
    logger.info("Application started successfully")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())