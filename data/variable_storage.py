# data/variable_storage.py
# WebFlow Automator - Variable Storage
# This module manages the storage and retrieval of variables

import os
import json
import logging
import datetime
import random
from typing import Dict, Any, List, Optional, Union

from core.message_bus import MessageBus, MessageTypes

logger = logging.getLogger("WebFlowAutomator.Data.VariableStorage")

class VariableStorage:
    """
    Manages the storage and retrieval of variables used in workflows
    """
    
    def __init__(self, message_bus: MessageBus):
        """
        Initialize the variable storage
        
        Args:
            message_bus: Message bus for communication
        """
        self.message_bus = message_bus
        
        # Dictionary to store variables
        # Format: {name: {value: Any, type: str}}
        self.variables = {}
        
        # Register with message bus
        self.subscribe_to_messages()
    
    def subscribe_to_messages(self):
        """Subscribe to relevant messages"""
        self.message_bus.subscribe(MessageTypes.WORKFLOW_STARTED, self.on_workflow_started)
        self.message_bus.subscribe(MessageTypes.WORKFLOW_COMPLETED, self.on_workflow_completed)
    
    def get_variable(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a variable by name
        
        Args:
            name: Variable name
        
        Returns:
            dict or None: Variable data if exists, None otherwise
        """
        if name in self.variables:
            var_data = self.variables[name]
            return {
                "name": name,
                "value": var_data["value"],
                "type": var_data["type"]
            }
        
        return None
    
    def get_variable_value(self, name: str) -> Any:
        """
        Get a variable value by name
        
        Args:
            name: Variable name
        
        Returns:
            Any: Variable value if exists, None otherwise
        """
        if name in self.variables:
            return self.variables[name]["value"]
        
        return None
    
    def set_variable(self, name: str, value: Any, var_type: str = "text") -> None:
        """
        Set a variable
        
        Args:
            name: Variable name
            value: Variable value
            var_type: Variable type (text, number, date, boolean)
        """
        # Convert value based on type
        converted_value = self.convert_value(value, var_type)
        
        # Check if variable exists
        is_new = name not in self.variables
        
        # Set variable
        self.variables[name] = {
            "value": converted_value,
            "type": var_type
        }
        
        # Publish message
        if is_new:
            self.message_bus.publish(MessageTypes.VARIABLE_CREATED, {
                "name": name,
                "value": converted_value,
                "type": var_type
            })
        else:
            self.message_bus.publish(MessageTypes.VARIABLE_UPDATED, {
                "name": name,
                "value": converted_value,
                "type": var_type
            })
        
        logger.debug(f"Variable '{name}' {'created' if is_new else 'updated'}")
    
    def delete_variable(self, name: str) -> bool:
        """
        Delete a variable
        
        Args:
            name: Variable name
        
        Returns:
            bool: True if deleted, False if not found
        """
        if name in self.variables:
            # Get variable data for event
            var_data = self.variables[name]
            
            # Delete variable
            del self.variables[name]
            
            # Publish message
            self.message_bus.publish(MessageTypes.VARIABLE_DELETED, {
                "name": name,
                "value": var_data["value"],
                "type": var_data["type"]
            })
            
            logger.debug(f"Variable '{name}' deleted")
            return True
        
        return False
    
    def clear_variables(self) -> None:
        """Clear all variables"""
        # Make a copy of variable names to avoid modification during iteration
        var_names = list(self.variables.keys())
        
        # Delete each variable
        for name in var_names:
            self.delete_variable(name)
        
        logger.debug("All variables cleared")
    
    def get_all_variables(self) -> List[Dict[str, Any]]:
        """
        Get all variables
        
        Returns:
            list: List of variable data dictionaries
        """
        result = []
        
        for name, data in self.variables.items():
            result.append({
                "name": name,
                "value": data["value"],
                "type": data["type"]
            })
        
        return result
    
    def resolve_variable_references(self, text: str) -> str:
        """
        Resolve variable references in a text string
        
        Variable references are in the format ${variable_name}
        
        Args:
            text: Text containing variable references
        
        Returns:
            str: Text with variable references replaced with values
        """
        if not text or "${" not in text:
            return text
        
        result = text
        
        # Find all variable references
        start_pos = 0
        while True:
            start_pos = result.find("${", start_pos)
            if start_pos == -1:
                break
            
            end_pos = result.find("}", start_pos)
            if end_pos == -1:
                break
            
            # Extract variable name
            var_name = result[start_pos + 2:end_pos]
            
            # Get variable value
            var_value = self.get_variable_value(var_name)
            
            # Replace variable reference with value
            if var_value is not None:
                result = result[:start_pos] + str(var_value) + result[end_pos + 1:]
                # Don't increment start_pos to check for nested variables
            else:
                # Skip this reference
                start_pos = end_pos + 1
        
        return result
    
    def convert_value(self, value: Any, var_type: str) -> Any:
        """
        Convert a value to the specified type
        
        Args:
            value: Value to convert
            var_type: Target type (text, number, date, boolean)
        
        Returns:
            Any: Converted value
        """
        try:
            if var_type == "text":
                return str(value)
            elif var_type == "number":
                return int(value)
            elif var_type == "date":
                if isinstance(value, str):
                    # Try to parse date
                    return value
                elif isinstance(value, (datetime.date, datetime.datetime)):
                    return value.strftime("%Y-%m-%d")
                else:
                    return str(value)
            elif var_type == "boolean":
                if isinstance(value, bool):
                    return value
                elif isinstance(value, str):
                    return value.lower() in ("true", "yes", "1", "t", "y")
                elif isinstance(value, (int, float)):
                    return value != 0
                else:
                    return bool(value)
            else:
                # Unknown type, return as is
                return value
        except (ValueError, TypeError):
            # Conversion error, return as string
            return str(value)
    
    def save_to_file(self, file_path: str) -> None:
        """
        Save variables to a file
        
        Args:
            file_path: Path to save file
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Convert variables to serializable format
            data = []
            for name, var_data in self.variables.items():
                value = var_data["value"]
                
                # Convert non-serializable values
                if isinstance(value, (datetime.date, datetime.datetime)):
                    value = value.isoformat()
                
                data.append({
                    "name": name,
                    "value": value,
                    "type": var_data["type"]
                })
            
            # Save to file
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Variables saved to {file_path}")
        except Exception as e:
            logger.error(f"Error saving variables to file: {e}")
            raise
    
    def load_from_file(self, file_path: str) -> None:
        """
        Load variables from a file
        
        Args:
            file_path: Path to load file
        """
        try:
            # Load from file
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Clear current variables
            self.variables = {}
            
            # Add variables
            for var in data:
                name = var.get("name", "")
                value = var.get("value", "")
                var_type = var.get("type", "text")
                
                if name:
                    self.set_variable(name, value, var_type)
            
            logger.info(f"Variables loaded from {file_path}")
        except Exception as e:
            logger.error(f"Error loading variables from file: {e}")
            raise
    
    def on_workflow_started(self, data):
        """
        Handle workflow started event
        
        Args:
            data: Workflow data
        """
        # Clear temporary variables
        # This will be implemented in a future version
        pass
    
    def on_workflow_completed(self, data):
        """
        Handle workflow completed event
        
        Args:
            data: Workflow completion data
        """
        # Save variables if auto-save enabled
        # This will be implemented in a future version
        pass