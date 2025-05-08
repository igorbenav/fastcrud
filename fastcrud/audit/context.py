"""
Context management for audit logging in FastCRUD.
"""

from typing import Any, Dict, Optional, TypeVar, Union
from contextlib import asynccontextmanager, contextmanager

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from .logger import AuditLogger, AuditContext
from .models import OperationType

# Type variables
T = TypeVar("T")
SessionType = TypeVar("SessionType", AsyncSession, Session)


class AuditContextManager:
    """
    Context manager for audit logging in FastCRUD operations.

    This class provides context managers for setting up audit context
    for both synchronous and asynchronous database operations.
    """

    def __init__(self, logger: AuditLogger):
        """
        Initialize the audit context manager.

        Args:
            logger: The AuditLogger instance to use for logging
        """
        self.logger = logger
        self._context: Dict[str, Dict[str, Any]] = {}

    def _get_context_key(self, session_id: str) -> str:
        """Generate a unique key for the context based on session ID."""
        return f"session_{session_id}"

    def set_context(
        self,
        session: Union[AsyncSession, Session],
        context: Union[Dict[str, Any], AuditContext],
    ) -> None:
        """
        Set the audit context for a specific database session.

        Args:
            session: The SQLAlchemy session to associate with the context
            context: The audit context information
        """
        session_id = str(id(session))
        context_key = self._get_context_key(session_id)

        if isinstance(context, AuditContext):
            context_data = context.model_dump()
        else:
            context_data = dict(context)

        self._context[context_key] = context_data

    def get_context(
        self, session: Union[AsyncSession, Session]
    ) -> Optional[Dict[str, Any]]:
        """
        Get the audit context for a specific database session.

        Args:
            session: The SQLAlchemy session to get context for

        Returns:
            The audit context or None if not set
        """
        session_id = str(id(session))
        context_key = self._get_context_key(session_id)
        return self._context.get(context_key)

    def clear_context(self, session: Union[AsyncSession, Session]) -> None:
        """
        Clear the audit context for a specific database session.

        Args:
            session: The SQLAlchemy session to clear context for
        """
        session_id = str(id(session))
        context_key = self._get_context_key(session_id)
        self._context.pop(context_key, None)

    @contextmanager
    def audited_session(
        self,
        session: Session,
        context: Optional[Union[Dict[str, Any], AuditContext]] = None,
        cleanup: bool = True,
    ):
        """
        Context manager for audited synchronous database operations.

        Args:
            session: The SQLAlchemy session to use
            context: The audit context information
            cleanup: Whether to clean up the context after the operation

        Yields:
            The provided session
        """
        if context:
            self.set_context(session, context)

        try:
            yield session
        finally:
            if cleanup:
                self.clear_context(session)

    @asynccontextmanager
    async def audited_async_session(
        self,
        session: AsyncSession,
        context: Optional[Union[Dict[str, Any], AuditContext]] = None,
        cleanup: bool = True,
    ):
        """
        Context manager for audited asynchronous database operations.

        Args:
            session: The SQLAlchemy async session to use
            context: The audit context information
            cleanup: Whether to clean up the context after the operation

        Yields:
            The provided async session
        """
        if context:
            self.set_context(session, context)

        try:
            yield session
        finally:
            if cleanup:
                self.clear_context(session)

    def log_operation(
        self,
        session: Session,
        operation: OperationType,
        table_name: str,
        record_id: Optional[str] = None,
        old_data: Optional[Dict[str, Any]] = None,
        new_data: Optional[Dict[str, Any]] = None,
        details: Optional[str] = None,
        commit: bool = True,
    ) -> None:
        """
        Log a database operation with the context from the current session.

        Args:
            session: The SQLAlchemy session
            operation: Type of operation
            table_name: Name of the affected table
            record_id: ID of the affected record
            old_data: Data before the operation
            new_data: Data after the operation
            details: Additional text details
            commit: Whether to commit the transaction immediately
        """
        context = self.get_context(session)

        user_id = None
        ip_address = None
        user_agent = None

        if context:
            user_id = context.get("user_id")
            ip_address = context.get("ip_address")
            user_agent = context.get("user_agent")

        self.logger.log_operation(
            session,
            operation,
            table_name,
            record_id,
            old_data,
            new_data,
            user_id,
            ip_address,
            user_agent,
            details,
            context=context,
            commit=commit,
        )

    async def log_operation_async(
        self,
        session: AsyncSession,
        operation: OperationType,
        table_name: str,
        record_id: Optional[str] = None,
        old_data: Optional[Dict[str, Any]] = None,
        new_data: Optional[Dict[str, Any]] = None,
        details: Optional[str] = None,
        commit: bool = True,
    ) -> None:
        """
        Log a database operation asynchronously with the context from the current session.

        Args:
            session: The SQLAlchemy async session
            operation: Type of operation
            table_name: Name of the affected table
            record_id: ID of the affected record
            old_data: Data before the operation
            new_data: Data after the operation
            details: Additional text details
            commit: Whether to commit the transaction immediately
        """
        context = self.get_context(session)

        user_id = None
        ip_address = None
        user_agent = None

        if context:
            user_id = context.get("user_id")
            ip_address = context.get("ip_address")
            user_agent = context.get("user_agent")

        await self.logger.log_operation_async(
            session,
            operation,
            table_name,
            record_id,
            old_data,
            new_data,
            user_id,
            ip_address,
            user_agent,
            details,
            context=context,
            commit=commit,
        )
