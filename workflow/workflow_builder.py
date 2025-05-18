# workflow/workflow_builder.py
# WebFlow Automator - Workflow Builder
# This module handles workflow creation and management

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union

from core.message_bus import MessageBus, MessageTypes

logger = logging.getLogger("WebFlowAutomator.Workflow.WorkflowBuilder")

class WorkflowBuilder:
    """
    Handles workflow creation, editing, saving, and loading
    """
    
    def __init__(self, message_bus: MessageBus):
        """
        Initialize the workflow builder
        
        Args:
            message_bus: Message bus for communication
        """
        self.message_bus = message_bus
        
        # Current workflow
        self.current_workflow = {
            "name": "New Workflow",
            "steps": []
        }
        
        # Subscribe to messages
        self.subscribe_to_messages()
    
    def subscribe_to_messages(self):
        """Subscribe to relevant messages"""
        self.message_bus.subscribe(MessageTypes.UI_REFRESH_WORKFLOW, self.on_workflow_refresh)
    
    def new_workflow(self):
        """Create a new workflow"""
        # Reset current workflow
        self.current_workflow = {
            "name": "New Workflow",
            "steps": []
        }
        
        # Publish message
        self.message_bus.publish(MessageTypes.UI_REFRESH_WORKFLOW, {
            "action": "clear"
        })
        
        logger.info("New workflow created")
    
    def get_current_workflow(self):
        """
        Get the current workflow
        
        Returns:
            dict: Current workflow data
        """
        return self.current_workflow
    
    def add_step(self, step_name: str, step_data: Dict[str, Any]):
        """
        Add a step to the workflow
        
        Args:
            step_name: Name of the step
            step_data: Step data
        """
        # Add step to workflow
        self.current_workflow["steps"].append({
            "name": step_name,
            "data": step_data
        })
        
        # Publish message
        self.message_bus.publish(MessageTypes.UI_REFRESH_WORKFLOW, {
            "action": "add",
            "action_name": step_name,
            "action_data": step_data
        })
        
        logger.info(f"Step added to workflow: {step_name}")
    
    def update_step(self, index: int, step_name: str, step_data: Dict[str, Any]):
        """
        Update a step in the workflow
        
        Args:
            index: Step index
            step_name: New step name
            step_data: New step data
        """
        # Check if index is valid
        if index < 0 or index >= len(self.current_workflow["steps"]):
            logger.error(f"Invalid step index: {index}")
            return
        
        # Update step
        self.current_workflow["steps"][index] = {
            "name": step_name,
            "data": step_data
        }
        
        # Publish message
        self.message_bus.publish(MessageTypes.UI_REFRESH_WORKFLOW, {
            "action": "update",
            "index": index,
            "action_name": step_name,
            "action_data": step_data
        })
        
        logger.info(f"Step updated in workflow: {step_name}")
    
    def remove_step(self, index: int):
        """
        Remove a step from the workflow
        
        Args:
            index: Step index
        """
        # Check if index is valid
        if index < 0 or index >= len(self.current_workflow["steps"]):
            logger.error(f"Invalid step index: {index}")
            return
        
        # Get step name for logging
        step_name = self.current_workflow["steps"][index]["name"]
        
        # Remove step
        self.current_workflow["steps"].pop(index)
        
        # Publish message
        self.message_bus.publish(MessageTypes.UI_REFRESH_WORKFLOW, {
            "action": "remove",
            "index": index
        })
        
        logger.info(f"Step removed from workflow: {step_name}")
    
    def move_step(self, from_index: int, to_index: int):
        """
        Move a step in the workflow
        
        Args:
            from_index: Source index
            to_index: Target index
        """
        # Check if indices are valid
        if from_index < 0 or from_index >= len(self.current_workflow["steps"]):
            logger.error(f"Invalid source index: {from_index}")
            return
        
        if to_index < 0 or to_index >= len(self.current_workflow["steps"]):
            logger.error(f"Invalid target index: {to_index}")
            return
        
        # Get step
        step = self.current_workflow["steps"].pop(from_index)
        
        # Insert at new position
        self.current_workflow["steps"].insert(to_index, step)
        
        # Publish message
        self.message_bus.publish(MessageTypes.UI_REFRESH_WORKFLOW, {
            "action": "refresh"
        })
        
        logger.info(f"Step moved from {from_index} to {to_index}")
    
    def save_workflow(self, file_path: str):
        """
        Save workflow to a file
        
        Args:
            file_path: Path to save the workflow
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Save workflow to file
            with open(file_path, "w") as f:
                json.dump(self.current_workflow, f, indent=2)
            
            # Publish message
            self.message_bus.publish(MessageTypes.WORKFLOW_SAVED, {
                "file_path": file_path
            })
            
            logger.info(f"Workflow saved to {file_path}")
        except Exception as e:
            logger.error(f"Error saving workflow: {e}")
            raise
    
    def load_workflow(self, file_path: str):
        """
        Load workflow from a file
        
        Args:
            file_path: Path to load the workflow from
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                logger.error(f"Workflow file not found: {file_path}")
                raise FileNotFoundError(f"Workflow file not found: {file_path}")
            
            # Load workflow from file
            with open(file_path, "r") as f:
                workflow = json.load(f)
            
            # Update current workflow
            self.current_workflow = workflow
            
            # Publish message
            self.message_bus.publish(MessageTypes.UI_REFRESH_WORKFLOW, {
                "action": "clear"
            })
            
            # Add steps to UI
            for step in self.current_workflow["steps"]:
                self.message_bus.publish(MessageTypes.UI_REFRESH_WORKFLOW, {
                    "action": "add",
                    "action_name": step["name"],
                    "action_data": step["data"]
                })
            
            # Publish loaded message
            self.message_bus.publish(MessageTypes.WORKFLOW_LOADED, {
                "file_path": file_path
            })
            
            logger.info(f"Workflow loaded from {file_path}")
        except Exception as e:
            logger.error(f"Error loading workflow: {e}")
            raise
    
    def on_workflow_refresh(self, data):
        """
        Handle workflow refresh message
        
        Args:
            data: Message data
        """
        action = data.get("action", "")
        
        if action == "add":
            # Add step
            action_name = data.get("action_name", "")
            action_data = data.get("action_data", {})
            
            # Add to current workflow if not from UI refresh
            if not data.get("from_refresh", False):
                self.current_workflow["steps"].append({
                    "name": action_name,
                    "data": action_data
                })
        
        elif action == "update":
            # Update step
            index = data.get("index", -1)
            action_name = data.get("action_name", "")
            action_data = data.get("action_data", {})
            
            # Update current workflow if not from UI refresh
            if not data.get("from_refresh", False) and 0 <= index < len(self.current_workflow["steps"]):
                self.current_workflow["steps"][index] = {
                    "name": action_name,
                    "data": action_data
                }
        
        elif action == "remove":
            # Remove step
            index = data.get("index", -1)
            
            # Remove from current workflow if not from UI refresh
            if not data.get("from_refresh", False) and 0 <= index < len(self.current_workflow["steps"]):
                self.current_workflow["steps"].pop(index)
        
        elif action == "clear":
            # Clear workflow
            if not data.get("from_refresh", False):
                self.current_workflow["steps"] = []
