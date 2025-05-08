"""
Audit log models for database operation tracking.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Mapped
from enum import Enum
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# Create a Base for audit models
AuditBase = declarative_base()

# Type alias for change data
ChangeData = Dict[str, Dict[str, Any]]


class OperationType(str, Enum):
    """Enum representing the type of database operation."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"


class AuditLogBase:
    """
    Base class that can be used to implement audit tables that align with
    the library's audit logging mechanisms.

    This is an abstract base that users can inherit from when creating their own
    audit log tables.
    """

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    user_id = Column(String(255), nullable=True, index=True)
    operation = Column(String(50), nullable=False, index=True)
    table_name = Column(String(255), nullable=False, index=True)
    record_id = Column(String(255), nullable=True, index=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)


class AuditLog(AuditBase, AuditLogBase):
    """
    Default implementation of an audit log table.

    This provides a complete implementation with detailed changelog support.
    """

    __tablename__ = "audit_logs"

    # Additional fields for detailed logging
    details = Column(Text, nullable=True)
    changes = Column(JSON, nullable=True)  # Stores before/after values for updates
    context = Column(JSON, nullable=True)  # Additional contextual information

    # Relationship to entries (if using separate records for change details)
    entries: Mapped[List["AuditLogEntry"]] = relationship(
        "AuditLogEntry", back_populates="audit_log", cascade="all, delete-orphan"
    )

    @classmethod
    def create(
        cls,
        operation: OperationType,
        table_name: str,
        record_id: Optional[str] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[str] = None,
        changes: Optional[ChangeData] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> "AuditLog":
        """
        Create a new audit log entry.

        Args:
            operation: The type of operation (create, read, update, delete)
            table_name: The name of the table that was affected
            record_id: ID of the record that was affected
            user_id: ID of the user who performed the operation
            ip_address: IP address from which the request originated
            user_agent: User agent string from the request
            details: Additional text details about the operation
            changes: Dictionary of changes with before/after values
            context: Additional contextual information as a dictionary

        Returns:
            A new AuditLog instance
        """
        return cls(
            operation=operation.value,
            table_name=table_name,
            record_id=record_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
            changes=changes,
            context=context,
        )

    def add_entries(self, changes: ChangeData) -> List["AuditLogEntry"]:
        """
        Add detailed entry records for each changed field.

        Args:
            changes: Dictionary with keys as field names and values as dictionaries with 'old' and 'new' keys

        Returns:
            List of created AuditLogEntry instances
        """
        entries = []
        for field_name, change in changes.items():
            old_value = change.get("old")
            new_value = change.get("new")

            if isinstance(old_value, (dict, list)):
                old_value = str(old_value)
            if isinstance(new_value, (dict, list)):
                new_value = str(new_value)

            entry = AuditLogEntry(
                field_name=field_name, old_value=old_value, new_value=new_value
            )
            entry.audit_log_id = self.id
            entries.append(entry)
            self.entries.append(entry)

        return entries


class AuditLogEntry(AuditBase):
    """
    Represents a single field change in an audit log.

    This allows for more detailed tracking of specific field changes
    when a record is updated.
    """

    __tablename__ = "audit_log_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    audit_log_id = Column(Integer, ForeignKey("audit_logs.id"), nullable=False)
    field_name = Column(String(255), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)

    # Relationship to parent
    audit_log: Mapped["AuditLog"] = relationship("AuditLog", back_populates="entries")
