"""
Auditable extension of FastCRUD for tracking database operations.
"""

from typing import Any, Dict, List, Optional, Type, Union
from sqlalchemy.engine import Row

from sqlalchemy.ext.asyncio import AsyncSession

from fastcrud.crud.fast_crud import FastCRUD
from fastcrud.types import (
    CreateSchemaType,
    DeleteSchemaType,
    ModelType,
    SelectSchemaType,
    UpdateSchemaInternalType,
    UpdateSchemaType,
)

from .models import OperationType
from .logger import AuditLogger
from .context import AuditContextManager


class AuditableFastCRUD(
    FastCRUD[
        ModelType,
        CreateSchemaType,
        UpdateSchemaType,
        UpdateSchemaInternalType,
        DeleteSchemaType,
        SelectSchemaType,
    ]
):
    """
    Extension of FastCRUD that incorporates audit logging capabilities.

    This class adds audit logging to all CRUD operations, tracking changes
    to data, who made the changes, and when they occurred.

    Attributes:
        model: The SQLAlchemy model type
        is_deleted_column: Column name for soft deletes
        deleted_at_column: Column name for soft delete timestamp
        updated_at_column: Column name for update timestamp
        audit_logger: The audit logger instance
        audit_context_manager: The audit context manager instance
    """

    def __init__(
        self,
        model: type[ModelType],
        is_deleted_column: str = "is_deleted",
        deleted_at_column: str = "deleted_at",
        updated_at_column: str = "updated_at",
        audit_logger: Optional[AuditLogger] = None,
        enable_audit: bool = True,
    ) -> None:
        """
        Initialize the auditable FastCRUD instance.

        Args:
            model: The SQLAlchemy model type
            is_deleted_column: Column name for soft deletes (default: "is_deleted")
            deleted_at_column: Column name for soft delete timestamp (default: "deleted_at")
            updated_at_column: Column name for update timestamp (default: "updated_at")
            audit_logger: The audit logger instance (default: creates a new instance)
            enable_audit: Whether to enable audit logging (default: True)
        """
        super().__init__(model, is_deleted_column, deleted_at_column, updated_at_column)

        self.enable_audit = enable_audit
        self.audit_logger = (
            audit_logger or AuditLogger()
        )  # Always set audit_logger regardless of enable_audit
        if enable_audit:
            self.audit_context_manager = AuditContextManager(self.audit_logger)

    async def create(
        self,
        db: AsyncSession,
        object: CreateSchemaType,
        commit: bool = True,
        audit: bool = True,
    ) -> ModelType:
        """
        Create a new record in the database with audit logging.

        Args:
            db: The SQLAlchemy async session
            object: The Pydantic schema containing the data to be saved
            commit: If True, commits the transaction immediately
            audit: Whether to log this operation for auditing

        Returns:
            The created database object
        """
        # Execute the standard create operation
        db_object = await super().create(db, object, commit=commit)

        # Log the operation if audit is enabled
        if self.enable_audit and audit:
            object_dict = object.model_dump()

            await self.audit_context_manager.log_operation_async(
                db,
                operation=OperationType.CREATE,
                table_name=self.model.__tablename__,
                record_id=self._get_record_id(db_object),
                new_data=object_dict,
                commit=False,  # Don't commit in the audit logger
            )

        return db_object

    async def update(
        self,
        db: AsyncSession,
        object: Union[UpdateSchemaType, Dict[str, Any]],
        allow_multiple: bool = False,
        commit: bool = True,
        return_columns: Optional[List[str]] = None,
        schema_to_select: Optional[Type[SelectSchemaType]] = None,
        return_as_model: bool = False,
        one_or_none: bool = True,
        **kwargs: Any,
    ) -> Union[Dict[Any, Any], SelectSchemaType, None]:
        """
        Update a record in the database with audit logging.

        Args:
            db: The SQLAlchemy async session
            object: The update data
            audit: Whether to log this operation for auditing
            fetch_before_update: Whether to fetch the current state before updating
            **kwargs: Filters to identify the record(s) to update

        Returns:
            The number of updated records or None
        """
        # Extract audit-specific parameters from kwargs
        audit = kwargs.pop("audit", True)
        fetch_before_update = kwargs.pop("fetch_before_update", True)

        # If auditing is enabled, fetch the current state of the records
        old_data = None
        if self.enable_audit and audit and fetch_before_update:
            try:
                # Fetch current data for audit trail
                record = await self.get(db, **kwargs)
                if record:
                    old_data = dict(record)
            except Exception:
                # Continue even if we can't get the old data
                pass

        # Execute the standard update operation and get the result
        result = await super().update(
            db,
            object=object,
            allow_multiple=allow_multiple,
            commit=commit,
            return_columns=return_columns,
            schema_to_select=schema_to_select,
            return_as_model=return_as_model,
            one_or_none=one_or_none,
            **kwargs,
        )

        # Log the operation if audit is enabled and result was returned
        if self.enable_audit and audit and result:
            # Prepare update data for logging
            if isinstance(object, dict):
                update_data = object
            else:
                update_data = object.model_dump(exclude_unset=True)

            # If we have record IDs, include them in the audit log
            record_id = None
            for pk in self._primary_keys:
                if pk.name in kwargs:
                    record_id = str(kwargs[pk.name])
                    break

            await self.audit_context_manager.log_operation_async(
                db,
                operation=OperationType.UPDATE,
                table_name=self.model.__tablename__,
                record_id=record_id,
                old_data=old_data,
                new_data=update_data,
                commit=False,  # Don't commit in the audit logger
            )

        # The parent method doesn't return anything, so we also return None
        return None

    async def delete(
        self,
        db: AsyncSession,
        db_row: Optional[Row[Any]] = None,
        allow_multiple: bool = False,
        commit: bool = True,
        **kwargs: Any,
    ) -> None:
        """
        Delete (soft or hard) a record from the database with audit logging.

        Args:
            db: The SQLAlchemy async session
            audit: Whether to log this operation for auditing
            fetch_before_delete: Whether to fetch the record before deletion
            **kwargs: Filters to identify the record(s) to delete

        Returns:
            The number of deleted records or None
        """
        # Extract audit-specific parameters from kwargs
        audit = kwargs.pop("audit", True)
        fetch_before_delete = kwargs.pop("fetch_before_delete", True)

        # If auditing is enabled, fetch the current state of the records
        old_data = None
        if self.enable_audit and audit and fetch_before_delete:
            try:
                # Fetch current data for audit trail
                record = await self.get(db, **kwargs)
                if record:
                    old_data = dict(record)
            except Exception:
                # Continue even if we can't get the old data
                pass

        # Determine if this is a soft or hard delete
        is_soft_delete = hasattr(self.model, self.is_deleted_column)

        # Execute the standard delete operation - no return value
        await super().delete(
            db, db_row=db_row, allow_multiple=allow_multiple, commit=commit, **kwargs
        )

        # Log the operation if audit is enabled
        if self.enable_audit and audit:
            # If we have record IDs, include them in the audit log
            record_id = None
            for pk in self._primary_keys:
                if pk.name in kwargs:
                    record_id = str(kwargs[pk.name])
                    break

            await self.audit_context_manager.log_operation_async(
                db,
                operation=OperationType.DELETE,
                table_name=self.model.__tablename__,
                record_id=record_id,
                old_data=old_data,
                details=f"Soft delete: {is_soft_delete}",
                commit=False,  # Don't commit in the audit logger
            )

        # The parent method doesn't return anything, so we also return None
        return None

    def _get_record_id(self, record: ModelType) -> Optional[str]:
        """
        Extract the record ID for audit logging.

        Args:
            record: The database record

        Returns:
            The record ID as a string or None
        """
        for pk in self._primary_keys:
            if hasattr(record, pk.name):
                pk_value = getattr(record, pk.name)
                if pk_value is not None:
                    return str(pk_value)
        return None

    def with_audit_context(self, context: Optional[Dict[str, Any]] = None):
        """
        Create a context manager for setting audit context.

        Args:
            context: The audit context information

        Returns:
            An audit context manager
        """
        if not self.enable_audit:
            raise RuntimeError("Audit logging is not enabled for this instance")

        # Create a new context manager with the provided context as default_context
        return AuditContextManager(self.audit_logger, default_context=context)
