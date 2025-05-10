"""
Audit log models for database operation tracking.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Mapped
from enum import Enum
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship

# Create a Base for audit models
AuditBase = declarative_base()  # Using sqlalchemy.orm.declarative_base

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
    timestamp = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
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
        new_data: Optional[Dict[str, Any]] = None,
        old_data: Optional[Dict[str, Any]] = None,
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
            new_data: Data after the operation (for creates and updates)
            old_data: Data before the operation (for updates and deletes)

        Returns:
            A new AuditLog instance
        """
        # Process changes if not provided but new_data/old_data are
        if changes is None and (new_data is not None or old_data is not None):
            changes = {}
            if old_data is None and new_data:
                # Handle creation case
                for key, value in new_data.items():
                    changes[key] = {"new": value}
            elif old_data and new_data is None:
                # Handle deletion case
                for key, value in old_data.items():
                    changes[key] = {"old": value}
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
