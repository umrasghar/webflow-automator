
# core/message_bus.py
# WebFlow Automator - Message Bus
# This module provides a simple event-based communication system between application components

import logging
import threading
import queue
import time
from typing import Callable, Dict, List, Any, Optional

logger = logging.getLogger("WebFlowAutomator.MessageBus")

class MessageBus:
    """
    A simple message bus implementation for inter-module communication
    
    This class provides a publish-subscribe pattern for modules to communicate
    without direct dependencies on each other.
    """
    
    def __init__(self, async_mode: bool = False):
        """
        Initialize the message bus
        
        Args:
            async_mode: If True, message delivery happens in a separate thread
        """
        self.subscribers: Dict[str, List[Callable]] = {}
        self.async_mode = async_mode
        self.running = False
        self.message_queue = queue.Queue()
        self.worker_thread = None
        
        if self.async_mode:
            self._start_worker()
    
    def _start_worker(self):
        """Start the asynchronous message delivery worker thread"""
        self.running = True
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()
        logger.debug("Message bus worker thread started")
    
    def _process_queue(self):
        """Process messages from the queue (runs in worker thread)"""
        while self.running:
            try:
                # Get message from queue with timeout to allow for thread termination
                message_type, data = self.message_queue.get(timeout=0.1)
                self._deliver_message(message_type, data)
                self.message_queue.task_done()
            except queue.Empty:
                # No messages in queue, continue waiting
                continue
            except Exception as e:
                logger.error(f"Error processing message: {e}")
    
    def _deliver_message(self, message_type: str, data: Any):
        """
        Deliver a message to all subscribers
        
        Args:
            message_type: The type of message to deliver
            data: The message data
        """
        if message_type in self.subscribers:
            for callback in self.subscribers[message_type]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error in subscriber callback for message '{message_type}': {e}")
    
    def subscribe(self, message_type: str, callback: Callable[[Any], None]) -> None:
        """
        Subscribe to a message type
        
        Args:
            message_type: The type of message to subscribe to
            callback: The function to call when a message of this type is published
        """
        if message_type not in self.subscribers:
            self.subscribers[message_type] = []
        
        if callback not in self.subscribers[message_type]:
            self.subscribers[message_type].append(callback)
            logger.debug(f"Subscribed to message '{message_type}'")
    
    def unsubscribe(self, message_type: str, callback: Callable[[Any], None]) -> None:
        """
        Unsubscribe from a message type
        
        Args:
            message_type: The type of message to unsubscribe from
            callback: The callback function to remove
        """
        if message_type in self.subscribers and callback in self.subscribers[message_type]:
            self.subscribers[message_type].remove(callback)
            logger.debug(f"Unsubscribed from message '{message_type}'")
            
            # Remove the message type if no subscribers left
            if not self.subscribers[message_type]:
                del self.subscribers[message_type]
    
    def publish(self, message_type: str, data: Any = None) -> None:
        """
        Publish a message to all subscribers
        
        Args:
            message_type: The type of message to publish
            data: The message data (can be any type)
        """
        logger.debug(f"Publishing message '{message_type}'")
        
        if self.async_mode:
            # Add to queue for asynchronous delivery
            self.message_queue.put((message_type, data))
        else:
            # Deliver immediately (synchronous)
            self._deliver_message(message_type, data)
    
    def shutdown(self) -> None:
        """
        Shutdown the message bus
        
        This stops the worker thread if running in async mode
        """
        if self.async_mode and self.running:
            self.running = False
            if self.worker_thread:
                self.worker_thread.join(timeout=1.0)
            logger.debug("Message bus worker thread stopped")


class MessageTypes:
    """
    Predefined message types used throughout the application
    
    Using constants helps avoid typos and makes it easier to discover
    available message types.
    """
    
    # UI related messages
    UI_READY = "ui.ready"
    UI_CLOSING = "ui.closing"
    UI_ELEMENT_SELECTED = "ui.element.selected"
    UI_STATUS_UPDATE = "ui.status.update"
    UI_REFRESH_WORKFLOW = "ui.refresh.workflow"
    UI_REFRESH_VARIABLES = "ui.refresh.variables"
    
    # Browser related messages
    BROWSER_READY = "browser.ready"
    BROWSER_PAGE_LOADED = "browser.page.loaded"
    BROWSER_ERROR = "browser.error"
    BROWSER_ELEMENT_FOUND = "browser.element.found"
    BROWSER_SCREENSHOT_TAKEN = "browser.screenshot.taken"
    
    # Workflow related messages
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_STEP_STARTED = "workflow.step.started"
    WORKFLOW_STEP_COMPLETED = "workflow.step.completed"
    WORKFLOW_STEP_FAILED = "workflow.step.failed" 
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_PAUSED = "workflow.paused"
    WORKFLOW_RESUMED = "workflow.resumed"
    WORKFLOW_STOPPED = "workflow.stopped"
    WORKFLOW_SAVED = "workflow.saved"
    WORKFLOW_LOADED = "workflow.loaded"
    
    # Data related messages
    VARIABLE_CREATED = "data.variable.created"
    VARIABLE_UPDATED = "data.variable.updated"
    VARIABLE_DELETED = "data.variable.deleted"
    DATA_EXCEL_EXPORTED = "data.excel.exported"
    DATA_EXCEL_IMPORTED = "data.excel.imported"


# Example of how to use the message bus:
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    # Create message bus
    bus = MessageBus(async_mode=True)
    
    # Define some subscribers
    def on_workflow_started(data):
        print(f"Workflow started: {data}")
    
    def on_workflow_completed(data):
        print(f"Workflow completed: {data}")
    
    # Subscribe to messages
    bus.subscribe(MessageTypes.WORKFLOW_STARTED, on_workflow_started)
    bus.subscribe(MessageTypes.WORKFLOW_COMPLETED, on_workflow_completed)
    
    # Publish messages
    bus.publish(MessageTypes.WORKFLOW_STARTED, {"workflow_id": "123", "name": "Test Workflow"})
    
    # Need a small delay to allow async messages to be processed
    time.sleep(0.1)
    
    # Publish another message
    bus.publish(MessageTypes.WORKFLOW_COMPLETED, {"workflow_id": "123", "status": "success"})
    
    # Cleanup
    time.sleep(0.1)
    bus.shutdown()
