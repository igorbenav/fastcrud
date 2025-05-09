"""
Audit logger implementation for FastCRUD operations.
"""

import logging
from enum import Enum
from typing import Any, Dict, Optional, Callable, TypeVar, Generic, Type, cast

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from pydantic import BaseModel

from .models import AuditLog, OperationType, ChangeData


# Type variable for the context
T = TypeVar("T")


class LogLevel(str, Enum):
    """Log levels for audit logging."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AuditContext(BaseModel):
    """Context information for audit logging."""

    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    custom_data: Dict[str, Any] = {}


class AuditLogger(Generic[T]):
    """
    Audit logger for tracking database operations with FastCRUD.

    This class provides methods for logging database operations with
    detailed change tracking and contextual information.

    Attributes:
        audit_log_model: SQLAlchemy model class for audit logs
        context_getter: Optional function to retrieve context data
        standard_logger: Python logger for outputting log messages
    """

    def __init__(
        self,
        audit_log_model: Type[AuditLog] = AuditLog,
        context_getter: Optional[Callable[[], T]] = None,
        log_level: LogLevel = LogLevel.INFO,
        logger_name: str = "fastcrud.audit",
    ):
        """
        Initialize the audit logger.

        Args:
            audit_log_model: SQLAlchemy model class for audit logs (default: AuditLog)
            context_getter: Optional function to retrieve context data
            log_level: Minimum log level to record
            logger_name: Name for the standard Python logger
        """
        self.audit_log_model = audit_log_model
        self.context_getter = context_getter
        self.log_level = log_level

        # Set up standard Python logging
        self.standard_logger = logging.getLogger(logger_name)

    def _get_context(self) -> Optional[Dict[str, Any]]:
        """
        Get contextual information from the context getter if available.

        Returns:
            Dictionary with context information or None
        """
        if self.context_getter:
            try:
                context = self.context_getter()
                if isinstance(context, dict):
                    return cast(Dict[str, Any], context)
                elif hasattr(context, "model_dump") and callable(
                    getattr(context, "model_dump")
                ):
                    return cast(Dict[str, Any], context.model_dump())
                # Fallback for older Pydantic versions
                elif hasattr(context, "dict") and callable(getattr(context, "dict")):
                    return cast(Dict[str, Any], context.dict())
                elif hasattr(context, "__dict__"):
                    # Explicitly cast to Dict[str, Any] to avoid mypy errors
                    return cast(Dict[str, Any], dict(context.__dict__))
            except Exception as e:
                self.standard_logger.warning(f"Error getting audit context: {e}")
        return None

    def _extract_record_changes(
        self, old_data: Optional[Dict[str, Any]], new_data: Optional[Dict[str, Any]]
    ) -> ChangeData:
        """
        Extract changes between old and new data.

        Args:
            old_data: Dictionary of old values before the operation
            new_data: Dictionary of new values after the operation

        Returns:
            Dictionary with field names as keys and before/after values
        """
        changes = {}

        if old_data is None and new_data:
            # Handle creation case
            for key, value in new_data.items():
                changes[key] = {"new": value}  # Don't include "old": None
        elif old_data and new_data is None:
            # Handle deletion case
            for key, value in old_data.items():
                changes[key] = {"old": value}  # Don't include "new": None
        elif old_data and new_data:
            # Handle update case
            all_keys = set(old_data.keys()) | set(new_data.keys())
            for key in all_keys:
                old_value = old_data.get(key)
                new_value = new_data.get(key)
                if old_value != new_value:
                    change = {}
                    if old_value is not None:
                        change["old"] = old_value
                    if new_value is not None:
                        change["new"] = new_value
                    changes[key] = change

        return changes

    async def log_operation_async(
        self,
        db: AsyncSession,
        operation: OperationType,
        table_name: str,
        record_id: Optional[str] = None,
        old_data: Optional[Dict[str, Any]] = None,
        new_data: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[str] = None,
        level: LogLevel = LogLevel.INFO,
        context: Optional[Dict[str, Any]] = None,
        commit: bool = True,
    ) -> Optional[AuditLog]:
        """
        Log a database operation asynchronously.

        Args:
            db: SQLAlchemy async session
            operation: Type of operation (create, read, update, delete)
            table_name: Name of the affected table
            record_id: ID of the affected record
            old_data: Data before the operation (for updates and deletes)
            new_data: Data after the operation (for creates and updates)
            user_id: ID of the user who performed the operation
            ip_address: IP address of the request
            user_agent: User agent string from the request
            details: Additional text details about the operation
            level: Log level for this entry
            context: Additional contextual information
            commit: Whether to commit the transaction immediately

        Returns:
            The created AuditLog instance or None if logging is disabled
        """
        # Skip if log level is lower than configured level
        if LogLevel[level.value].value < LogLevel[self.log_level.value].value:
            return None

        # Get context if not provided
        if context is None:
            context = self._get_context()

        # Extract user information from context if available
        if context:
            user_id = user_id or context.get("user_id")
            ip_address = ip_address or context.get("ip_address")
            user_agent = user_agent or context.get("user_agent")

        # Extract changes
        changes = self._extract_record_changes(old_data, new_data)

        # Create audit log entry
        audit_log = self.audit_log_model.create(
            operation=operation,
            table_name=table_name,
            record_id=str(record_id) if record_id is not None else None,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
            changes=changes,
            context=context,
        )

        # Add to session and commit if requested
        db.add(audit_log)

        # Log to standard logger as well
        log_message = f"{operation.value.upper()} operation on {table_name}"
        if record_id:
            log_message += f" (ID: {record_id})"
        if user_id:
            log_message += f" by user {user_id}"

        self.standard_logger.log(
            getattr(logging, level.value),
            log_message,
            extra={
                "audit_data": {
                    "table": table_name,
                    "operation": operation.value,
                    "record_id": record_id,
                    "user_id": user_id,
                    "changes": changes,
                }
            },
        )

        if commit:
            await db.commit()

        return audit_log

    def log_operation(
        self,
        db: Session,
        operation: OperationType,
        table_name: str,
        record_id: Optional[str] = None,
        old_data: Optional[Dict[str, Any]] = None,
        new_data: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[str] = None,
        level: LogLevel = LogLevel.INFO,
        context: Optional[Dict[str, Any]] = None,
        commit: bool = True,
    ) -> Optional[AuditLog]:
        """
        Log a database operation synchronously.

        Args:
            db: SQLAlchemy session
            operation: Type of operation (create, read, update, delete)
            table_name: Name of the affected table
            record_id: ID of the affected record
            old_data: Data before the operation (for updates and deletes)
            new_data: Data after the operation (for creates and updates)
            user_id: ID of the user who performed the operation
            ip_address: IP address of the request
            user_agent: User agent string from the request
            details: Additional text details about the operation
            level: Log level for this entry
            context: Additional contextual information
            commit: Whether to commit the transaction immediately

        Returns:
            The created AuditLog instance or None if logging is disabled
        """
        # Skip if log level is lower than configured level
        if LogLevel[level.value].value < LogLevel[self.log_level.value].value:
            return None

        # Get context if not provided
        if context is None:
            context = self._get_context()

        # Extract user information from context if available
        if context:
            user_id = user_id or context.get("user_id")
            ip_address = ip_address or context.get("ip_address")
            user_agent = user_agent or context.get("user_agent")

        # Extract changes
        changes = self._extract_record_changes(old_data, new_data)

        # Create audit log entry
        audit_log = self.audit_log_model.create(
            operation=operation,
            table_name=table_name,
            record_id=str(record_id) if record_id is not None else None,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
            changes=changes,
            context=context,
        )

        # Add to session and commit if requested
        db.add(audit_log)

        # Log to standard logger as well
        log_message = f"{operation.value.upper()} operation on {table_name}"
        if record_id:
            log_message += f" (ID: {record_id})"
        if user_id:
            log_message += f" by user {user_id}"

        self.standard_logger.log(
            getattr(logging, level.value),
            log_message,
            extra={
                "audit_data": {
                    "table": table_name,
                    "operation": operation.value,
                    "record_id": record_id,
                    "user_id": user_id,
                    "changes": changes,
                }
            },
        )

        if commit:
            db.commit()

        return audit_log
