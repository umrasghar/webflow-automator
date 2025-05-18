# workflow/execution_engine.py
# WebFlow Automator - Execution Engine
# This module handles the execution of workflows

import time
import logging
import threading
from typing import Dict, Any, List, Optional, Union, Callable

from core.message_bus import MessageBus, MessageTypes

logger = logging.getLogger("WebFlowAutomator.Workflow.ExecutionEngine")

class ExecutionEngine:
    """
    Handles the execution of workflow steps
    """
    
    def __init__(self, message_bus: MessageBus):
        """
        Initialize the execution engine
        
        Args:
            message_bus: Message bus for communication
        """
        # Fix: Accept message_bus directly instead of looking for it in a modules dictionary
        self.message_bus = message_bus
        self.browser_controller = None
        self.variable_storage = None
        
        # Execution state
        self.current_workflow = None
        self.execution_thread = None
        self.running = False
        self.paused = False
        self.stop_requested = False
        
        # Subscribe to messages
        self.message_bus.subscribe(MessageTypes.BROWSER_PAGE_LOADED, self.on_page_loaded)
        self.message_bus.subscribe(MessageTypes.UI_CLOSING, self.on_ui_closing)
    
    def set_modules(self, modules: Dict[str, Any]):
        """
        Set module references
        
        Args:
            modules: Dictionary containing application modules
        """
        # Set module references
        if "browser_controller" in modules:
            self.browser_controller = modules["browser_controller"]
        
        if "variable_storage" in modules:
            self.variable_storage = modules["variable_storage"]
    
    def start_workflow(self, workflow: Dict[str, Any]) -> None:
        """
        Start executing a workflow
        
        Args:
            workflow: Workflow data
        """
        if self.running:
            raise RuntimeError("Workflow is already running")
        
        # Set workflow
        self.current_workflow = workflow
        
        # Reset state
        self.running = True
        self.paused = False
        self.stop_requested = False
        
        # Start execution thread
        self.execution_thread = threading.Thread(target=self.execute_workflow)
        self.execution_thread.daemon = True
        self.execution_thread.start()
        
        # Publish started message
        self.message_bus.publish(MessageTypes.WORKFLOW_STARTED, {
            "name": workflow.get("name", "Unnamed workflow"),
            "steps": len(workflow.get("steps", []))
        })
        
        logger.info(f"Workflow started: {workflow.get('name', 'Unnamed workflow')}")
    
    def pause_workflow(self) -> None:
        """Pause the current workflow"""
        if not self.running:
            raise RuntimeError("No workflow is running")
        
        if self.paused:
            raise RuntimeError("Workflow is already paused")
        
        # Set paused state
        self.paused = True
        
        # Publish paused message
        self.message_bus.publish(MessageTypes.WORKFLOW_PAUSED, {
            "name": self.current_workflow.get("name", "Unnamed workflow")
        })
        
        logger.info("Workflow paused")
    
    def resume_workflow(self) -> None:
        """Resume the current workflow"""
        if not self.running:
            raise RuntimeError("No workflow is running")
        
        if not self.paused:
            raise RuntimeError("Workflow is not paused")
        
        # Clear paused state
        self.paused = False
        
        # Publish resumed message
        self.message_bus.publish(MessageTypes.WORKFLOW_RESUMED, {
            "name": self.current_workflow.get("name", "Unnamed workflow")
        })
        
        logger.info("Workflow resumed")
    
    def stop_workflow(self) -> None:
        """Stop the current workflow"""
        if not self.running:
            raise RuntimeError("No workflow is running")
        
        # Set stop requested state
        self.stop_requested = True
        
        # Clear paused state
        self.paused = False
        
        # Wait for thread to finish
        if self.execution_thread:
            self.execution_thread.join(timeout=5.0)
        
        # Reset state
        self.running = False
        self.stop_requested = False
        self.execution_thread = None
        
        # Publish stopped message
        self.message_bus.publish(MessageTypes.WORKFLOW_STOPPED, {
            "name": self.current_workflow.get("name", "Unnamed workflow")
        })
        
        logger.info("Workflow stopped")
    
    def execute_workflow(self) -> None:
        """Execute the current workflow"""
        try:
            # Get workflow steps
            steps = self.current_workflow.get("steps", [])
            
            # Check if workflow has steps
            if not steps:
                logger.warning("Workflow has no steps")
                self.complete_workflow(success=True)
                return
            
            # Execute each step
            for i, step in enumerate(steps):
                # Check if stop requested
                if self.stop_requested:
                    logger.info("Workflow execution stopped")
                    return
                
                # Check if paused
                while self.paused and not self.stop_requested:
                    time.sleep(0.1)
                
                # Get step details
                step_name = step.get("name", f"Step {i+1}")
                step_data = step.get("data", {})
                
                # Publish step started message
                self.message_bus.publish(MessageTypes.WORKFLOW_STEP_STARTED, {
                    "number": i + 1,
                    "total": len(steps),
                    "name": step_name,
                    "action_type": step_data.get("action_type", "unknown")
                })
                
                # Execute step
                success = self.execute_step(step_data)
                
                # Check if step succeeded
                if not success:
                    logger.error(f"Step failed: {step_name}")
                    self.message_bus.publish(MessageTypes.WORKFLOW_STEP_FAILED, {
                        "number": i + 1,
                        "name": step_name,
                        "action_type": step_data.get("action_type", "unknown")
                    })
                    
                    # TODO: Handle step failure based on workflow settings
                    # For now, stop workflow on first failure
                    self.complete_workflow(success=False, error=f"Step failed: {step_name}")
                    return
                
                # Publish step completed message
                self.message_bus.publish(MessageTypes.WORKFLOW_STEP_COMPLETED, {
                    "number": i + 1,
                    "name": step_name,
                    "action_type": step_data.get("action_type", "unknown")
                })
                
                # Pause between steps (to avoid overloading the browser)
                time.sleep(0.5)
            
            # All steps completed successfully
            self.complete_workflow(success=True)
        except Exception as e:
            logger.error(f"Error executing workflow: {e}")
            self.complete_workflow(success=False, error=str(e))
    
    def complete_workflow(self, success: bool, error: Optional[str] = None) -> None:
        """
        Complete workflow execution
        
        Args:
            success: Whether workflow completed successfully
            error: Error message if failed
        """
        # Reset state
        self.running = False
        self.paused = False
        self.stop_requested = False
        self.execution_thread = None
        
        # Publish completed message
        self.message_bus.publish(MessageTypes.WORKFLOW_COMPLETED, {
            "name": self.current_workflow.get("name", "Unnamed workflow"),
            "status": "success" if success else "error",
            "error": error
        })
        
        logger.info(f"Workflow {'completed successfully' if success else 'failed'}")
    
    def execute_step(self, step_data: Dict[str, Any]) -> bool:
        """
        Execute a workflow step
        
        Args:
            step_data: Step data
        
        Returns:
            bool: Whether step was executed successfully
        """
        action_type = step_data.get("action_type", "unknown")
        
        try:
            # Execute action based on type
            if action_type == "navigate":
                return self.execute_navigate(step_data)
            elif action_type == "click":
                return self.execute_click(step_data)
            elif action_type == "input_text":
                return self.execute_input_text(step_data)
            elif action_type == "clear_field":
                return self.execute_clear_field(step_data)
            elif action_type == "check":
                return self.execute_check(step_data)
            elif action_type == "uncheck":
                return self.execute_uncheck(step_data)
            elif action_type == "select_radio":
                return self.execute_select_radio(step_data)
            elif action_type == "select_option":
                return self.execute_select_option(step_data)
            elif action_type == "select_random_option":
                return self.execute_select_random_option(step_data)
            elif action_type == "extract_text":
                return self.execute_extract_text(step_data)
            elif action_type == "wait_for_element":
                return self.execute_wait_for_element(step_data)
            elif action_type == "wait_time":
                return self.execute_wait_time(step_data)
            elif action_type == "verify_exists":
                return self.execute_verify_exists(step_data)
            elif action_type == "verify_text":
                return self.execute_verify_text(step_data)
            elif action_type.startswith("generate_"):
                return self.execute_generate_data(step_data)
            elif action_type == "excel_export":
                return self.execute_excel_export(step_data)
            elif action_type == "excel_import":
                return self.execute_excel_import(step_data)
            else:
                logger.error(f"Unknown action type: {action_type}")
                return False
        except Exception as e:
            logger.error(f"Error executing step: {e}")
            return False
    
    def execute_navigate(self, step_data: Dict[str, Any]) -> bool:
        """
        Execute navigate action
        
        Args:
            step_data: Step data
        
        Returns:
            bool: Success status
        """
        url = step_data.get("url", "")
        
        # Resolve variable references in URL
        if self.variable_storage:
            url = self.variable_storage.resolve_variable_references(url)
        
        # Navigate to URL
        if self.browser_controller:
            return self.browser_controller.navigate(url)
        else:
            logger.error("Browser controller not available")
            return False
    
    def execute_click(self, step_data: Dict[str, Any]) -> bool:
        """
        Execute click action
        
        Args:
            step_data: Step data
        
        Returns:
            bool: Success status
        """
        element = step_data.get("element", {})
        
        # Find element
        if self.browser_controller:
            return self.browser_controller.click_element(element)
        else:
            logger.error("Browser controller not available")
            return False
    
    def execute_input_text(self, step_data: Dict[str, Any]) -> bool:
        """
        Execute input text action
        
        Args:
            step_data: Step data
        
        Returns:
            bool: Success status
        """
        element = step_data.get("element", {})
        text = step_data.get("text", "")
        
        # Resolve variable references in text
        if self.variable_storage:
            text = self.variable_storage.resolve_variable_references(text)
        
        # Input text
        if self.browser_controller:
            return self.browser_controller.input_text(element, text)
        else:
            logger.error("Browser controller not available")
            return False
    
    def execute_clear_field(self, step_data: Dict[str, Any]) -> bool:
        """
        Execute clear field action
        
        Args:
            step_data: Step data
        
        Returns:
            bool: Success status
        """
        element = step_data.get("element", {})
        
        # Clear field
        if self.browser_controller:
            return self.browser_controller.clear_field(element)
        else:
            logger.error("Browser controller not available")
            return False
    
    def execute_check(self, step_data: Dict[str, Any]) -> bool:
        """
        Execute check action
        
        Args:
            step_data: Step data
        
        Returns:
            bool: Success status
        """
        element = step_data.get("element", {})
        
        # Check checkbox
        if self.browser_controller:
            return self.browser_controller.check_checkbox(element)
        else:
            logger.error("Browser controller not available")
            return False
    
    def execute_uncheck(self, step_data: Dict[str, Any]) -> bool:
        """
        Execute uncheck action
        
        Args:
            step_data: Step data
        
        Returns:
            bool: Success status
        """
        element = step_data.get("element", {})
        
        # Uncheck checkbox
        if self.browser_controller:
            return self.browser_controller.uncheck_checkbox(element)
        else:
            logger.error("Browser controller not available")
            return False
    
    def execute_select_radio(self, step_data: Dict[str, Any]) -> bool:
        """
        Execute select radio action
        
        Args:
            step_data: Step data
        
        Returns:
            bool: Success status
        """
        element = step_data.get("element", {})
        
        # Select radio
        if self.browser_controller:
            return self.browser_controller.select_radio(element)
        else:
            logger.error("Browser controller not available")
            return False
    
    def execute_select_option(self, step_data: Dict[str, Any]) -> bool:
        """
        Execute select option action
        
        Args:
            step_data: Step data
        
        Returns:
            bool: Success status
        """
        element = step_data.get("element", {})
        option = step_data.get("option", "")
        
        # Resolve variable references in option
        if self.variable_storage:
            option = self.variable_storage.resolve_variable_references(option)
        
        # Select option
        if self.browser_controller:
            return self.browser_controller.select_option(element, option)
        else:
            logger.error("Browser controller not available")
            return False
    
    def execute_select_random_option(self, step_data: Dict[str, Any]) -> bool:
        """
        Execute select random option action
        
        Args:
            step_data: Step data
        
        Returns:
            bool: Success status
        """
        element = step_data.get("element", {})
        
        # Select random option
        if self.browser_controller:
            return self.browser_controller.select_random_option(element)
        else:
            logger.error("Browser controller not available")
            return False
    
    def execute_extract_text(self, step_data: Dict[str, Any]) -> bool:
        """
        Execute extract text action
        
        Args:
            step_data: Step data
        
        Returns:
            bool: Success status
        """
        element = step_data.get("element", {})
        variable_name = step_data.get("variable_name", "")
        
        if not variable_name:
            logger.error("No variable name specified for extract text action")
            return False
        
        # Extract text
        if self.browser_controller:
            text = self.browser_controller.get_element_text(element)
            
            if text is not None:
                # Store text in variable
                if self.variable_storage:
                    self.variable_storage.set_variable(variable_name, text, "text")
                    return True
                else:
                    logger.error("Variable storage not available")
                    return False
            else:
                logger.error("Failed to extract text from element")
                return False
        else:
            logger.error("Browser controller not available")
            return False
    
    def execute_wait_for_element(self, step_data: Dict[str, Any]) -> bool:
        """
        Execute wait for element action
        
        Args:
            step_data: Step data
        
        Returns:
            bool: Success status
        """
        element = step_data.get("element", {})
        timeout = step_data.get("timeout", 10)  # Default 10 seconds
        
        # Wait for element
        if self.browser_controller:
            return self.browser_controller.wait_for_element(element, timeout)
        else:
            logger.error("Browser controller not available")
            return False
    
    def execute_wait_time(self, step_data: Dict[str, Any]) -> bool:
        """
        Execute wait time action
        
        Args:
            step_data: Step data
        
        Returns:
            bool: Success status
        """
        seconds = step_data.get("seconds", 1)  # Default 1 second
        
        # Wait for specified time
        logger.info(f"Waiting for {seconds} seconds")
        time.sleep(seconds)
        
        return True
    
    def execute_verify_exists(self, step_data: Dict[str, Any]) -> bool:
        """
        Execute verify exists action
        
        Args:
            step_data: Step data
        
        Returns:
            bool: Success status
        """
        element = step_data.get("element", {})
        
        # Verify element exists
        if self.browser_controller:
            exists = self.browser_controller.element_exists(element)
            
            if not exists:
                logger.error("Element does not exist")
            
            return exists
        else:
            logger.error("Browser controller not available")
            return False
    
    def execute_verify_text(self, step_data: Dict[str, Any]) -> bool:
        """
        Execute verify text action
        
        Args:
            step_data: Step data
        
        Returns:
            bool: Success status
        """
        element = step_data.get("element", {})
        expected_text = step_data.get("text", "")
        
        # Resolve variable references in expected text
        if self.variable_storage:
            expected_text = self.variable_storage.resolve_variable_references(expected_text)
        
        # Verify element text
        if self.browser_controller:
            actual_text = self.browser_controller.get_element_text(element)
            
            if actual_text is None:
                logger.error("Failed to get element text")
                return False
            
            matches = actual_text == expected_text
            
            if not matches:
                logger.error(f"Text mismatch. Expected: '{expected_text}', Actual: '{actual_text}'")
            
            return matches
        else:
            logger.error("Browser controller not available")
            return False
    
    def execute_generate_data(self, step_data: Dict[str, Any]) -> bool:
        """
        Execute generate data action
        
        Args:
            step_data: Step data
        
        Returns:
            bool: Success status
        """
        action_type = step_data.get("action_type", "")
        element = step_data.get("element", {})
        
        # Get data generator from modules
        data_generator = None
        # TODO: Get data generator from modules
        
        if not data_generator:
            logger.error("Data generator not available")
            return False
        
        # Generate data based on action type
        if action_type == "generate_name":
            name_type = step_data.get("name_type", "full")
            value = data_generator.generate_name(name_type)
        elif action_type == "generate_email":
            value = data_generator.generate_email()
        elif action_type == "generate_number":
            min_val = step_data.get("min", 1)
            max_val = step_data.get("max", 100)
            value = data_generator.generate_number(min_val, max_val)
        elif action_type == "generate_date":
            format_str = step_data.get("format", "%Y-%m-%d")
            value = data_generator.generate_date(format_str=format_str)
        elif action_type == "generate_custom":
            format_str = step_data.get("format", "")
            value = data_generator.generate_custom(format_str)
        else:
            logger.error(f"Unknown generate action type: {action_type}")
            return False
        
        # Input generated data
        if self.browser_controller:
            # Use generated value for logging
            logger.info(f"Generated {action_type[9:]}: {value}")
            return self.browser_controller.input_text(element, str(value))
        else:
            logger.error("Browser controller not available")
            return False
    
    def execute_excel_export(self, step_data: Dict[str, Any]) -> bool:
        """
        Execute excel export action
        
        Args:
            step_data: Step data
        
        Returns:
            bool: Success status
        """
        file_path = step_data.get("file_path", "")
        variables = step_data.get("variables", [])
        
        if not file_path:
            logger.error("No file path specified for excel export action")
            return False
        
        # Get excel integrator from modules
        excel_integrator = None
        # TODO: Get excel integrator from modules
        
        if not excel_integrator:
            logger.error("Excel integrator not available")
            return False
        
        # Get variable values
        if not self.variable_storage:
            logger.error("Variable storage not available")
            return False
        
        # Resolve variable references in file path
        file_path = self.variable_storage.resolve_variable_references(file_path)
        
        # Create data for export
        data = []
        for var_name in variables:
            var = self.variable_storage.get_variable(var_name)
            if var:
                data.append({
                    "name": var["name"],
                    "value": var["value"],
                    "type": var["type"]
                })
        
        # Export to Excel
        try:
            excel_integrator.write_excel(file_path, data, append=step_data.get("append", False))
            return True
        except Exception as e:
            logger.error(f"Error exporting to Excel: {e}")
            return False
    
    def execute_excel_import(self, step_data: Dict[str, Any]) -> bool:
        """
        Execute excel import action
        
        Args:
            step_data: Step data
        
        Returns:
            bool: Success status
        """
        file_path = step_data.get("file_path", "")
        sheet_name = step_data.get("sheet_name", None)
        start_row = step_data.get("start_row", 0)
        mappings = step_data.get("mappings", {})
        
        if not file_path:
            logger.error("No file path specified for excel import action")
            return False
        
        # Get excel integrator from modules
        excel_integrator = None
        # TODO: Get excel integrator from modules
        
        if not excel_integrator:
            logger.error("Excel integrator not available")
            return False
        
        # Get variable storage
        if not self.variable_storage:
            logger.error("Variable storage not available")
            return False
        
        # Resolve variable references in file path
        file_path = self.variable_storage.resolve_variable_references(file_path)
        
        # Import from Excel
        try:
            data = excel_integrator.read_excel(file_path, sheet_name, start_row)
            
            # Apply mappings if provided
            if mappings:
                mapped_data = excel_integrator.map_columns(data, mappings)
            else:
                mapped_data = data
            
            # Store in variables
            for row_idx, row in enumerate(mapped_data):
                for col_name, value in row.items():
                    # Create variable for each cell
                    var_name = f"{col_name}_{row_idx}"
                    self.variable_storage.set_variable(var_name, value)
            
            # Publish message
            self.message_bus.publish(MessageTypes.DATA_EXCEL_IMPORTED, {
                "file_path": file_path,
                "row_count": len(mapped_data)
            })
            
            return True
        except Exception as e:
            logger.error(f"Error importing from Excel: {e}")
            return False
    
    def on_page_loaded(self, data):
        """
        Handle page loaded event
        
        Args:
            data: Page data
        """
        # This will be implemented in a future version
        pass
    
    def on_ui_closing(self, data):
        """
        Handle UI closing event
        
        Args:
            data: Event data
        """
        # Stop any running workflow
        if self.running:
            self.stop_workflow()