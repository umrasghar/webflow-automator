# config.py
# WebFlow Automator - Configuration
# This file defines global configuration settings and constants

# UI Framework Configuration
# Force a specific UI framework to be used throughout the application
UI_FRAMEWORK = "PyQt6"  # Options: "PyQt6", "PySide6"

# Appearance
APP_NAME = "WebFlow Automator"
APP_VERSION = "1.0.0"

# File paths
DEFAULT_WORKFLOWS_DIR = "workflows"
DEFAULT_DATA_DIR = "data"
DEFAULT_LOGS_DIR = "logs"
DEFAULT_TEMP_DIR = "temp"

# Browser settings
DEFAULT_BROWSER_ENGINE = "chromium"  # Options: "chromium", "firefox", "edge"
DEFAULT_TIMEOUT = 30  # Default timeout in seconds for browser operations

# Debug settings
DEBUG_MODE = False  # Enable debug mode for additional logging