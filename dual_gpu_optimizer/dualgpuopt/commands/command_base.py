"""
Base command classes for implementing the command pattern.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from dualgpuopt.services.event_service import event_bus


class Command(ABC):
    """Abstract base class for commands."""

    def __init__(self, name: str) -> None:
        """
        Initialize the command.

        Args:
            name: Command name for identification
        """
        self.name = name
        self.logger = logging.getLogger(f"dualgpuopt.commands.{name}")

    @abstractmethod
    def execute(self) -> bool:
        """
        Execute the command.

        Returns:
            Success status
        """

    @abstractmethod
    def undo(self) -> bool:
        """
        Undo the command.

        Returns:
            Success status
        """

    def _publish_result(
        self, success: bool, context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Publish command execution result.

        Args:
            success: Whether the command succeeded
            context: Additional context information
        """
        if context is None:
            context = {}

        context["command"] = self.name
        context["success"] = success

        event_type = f"command_executed:{self.name}"
        event_bus.publish(event_type, context)
        event_bus.publish("command_executed", context)


class CommandManager:
    """Manages command execution and history."""

    def __init__(self, max_history: int = 50) -> None:
        """
        Initialize the command manager.

        Args:
            max_history: Maximum size of command history
        """
        self.history: List[Command] = []
        self.future: List[Command] = []  # For redo operations
        self.max_history = max_history
        self.logger = logging.getLogger("dualgpuopt.commands.manager")

    def execute(self, command: Command) -> bool:
        """
        Execute a command and add it to history.

        Args:
            command: Command to execute

        Returns:
            Success status
        """
        self.logger.debug(f"Executing command: {command.name}")
        result = command.execute()

        if result:
            self.history.append(command)
            self.future.clear()  # Clear redo stack

            # Limit history size
            if len(self.history) > self.max_history:
                self.history = self.history[-self.max_history :]

            # Publish history updated event
            event_bus.publish(
                "command_history_updated",
                {
                    "history_size": len(self.history),
                    "can_undo": bool(self.history),
                    "can_redo": bool(self.future),
                },
            )

        return result

    def undo(self) -> bool:
        """
        Undo the last command.

        Returns:
            Success status
        """
        if not self.history:
            self.logger.debug("No commands to undo")
            return False

        command = self.history.pop()
        self.logger.debug(f"Undoing command: {command.name}")

        result = command.undo()
        if result:
            self.future.append(command)

            # Publish history updated event
            event_bus.publish(
                "command_history_updated",
                {
                    "history_size": len(self.history),
                    "can_undo": bool(self.history),
                    "can_redo": bool(self.future),
                },
            )
        else:
            # If undo failed, put the command back in history
            self.history.append(command)

        return result

    def redo(self) -> bool:
        """
        Redo the last undone command.

        Returns:
            Success status
        """
        if not self.future:
            self.logger.debug("No commands to redo")
            return False

        command = self.future.pop()
        self.logger.debug(f"Redoing command: {command.name}")

        result = command.execute()
        if result:
            self.history.append(command)

            # Publish history updated event
            event_bus.publish(
                "command_history_updated",
                {
                    "history_size": len(self.history),
                    "can_undo": bool(self.history),
                    "can_redo": bool(self.future),
                },
            )
        else:
            # If redo failed, put the command back in future
            self.future.append(command)

        return result

    def clear_history(self) -> None:
        """Clear command history."""
        self.history.clear()
        self.future.clear()

        # Publish history updated event
        event_bus.publish(
            "command_history_updated",
            {"history_size": 0, "can_undo": False, "can_redo": False},
        )


# Create global command manager
command_manager = CommandManager()
