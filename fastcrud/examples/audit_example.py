"""
Example demonstrating how to use the auditing and logging functionality with FastCRUD.
"""

from typing import Optional
from datetime import datetime
import logging
import asyncio

from sqlalchemy import Column, Integer, String, DateTime, Boolean, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from fastcrud.audit import AuditableFastCRUD, AuditContext, OperationType
from fastcrud.audit.models import AuditBase
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Create SQLAlchemy models
Base = declarative_base()


class User(Base):
    """Example user model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    deleted_at = Column(DateTime, nullable=True)


# Create Pydantic schemas
class UserBase(BaseModel):
    """Base user schema."""

    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool = True


class CreateUserSchema(UserBase):
    """Schema for creating users."""

    pass


class UpdateUserSchema(BaseModel):
    """Schema for updating users."""

    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None

    class Config:
        from_attributes = True


class ReadUserSchema(UserBase):
    """Schema for reading users."""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Main example function
async def main():
    """Run the audit example."""
    # Create async SQLite engine
    engine = create_async_engine("sqlite+aiosqlite:///audit_example.db")

    # Create async session
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        # Create audit log tables - since both models use the same base, we only need to call create_all once
        await conn.run_sync(AuditBase.metadata.create_all)

    # Create AuditableFastCRUD instance
    user_crud = AuditableFastCRUD(User)

    async with async_session() as session:
        # Create user context for audit tracking
        user_context = AuditContext(
            user_id="admin",
            ip_address="127.0.0.1",
            user_agent="Example/1.0",
            custom_data={"source": "user_management_api"},
        )

        # Use the context manager to set audit context
        async with user_crud.audit_context_manager.audited_async_session(
            session, user_context
        ):
            # Create a user - this will be tracked in the audit log
            new_user = await user_crud.create(
                session,
                CreateUserSchema(
                    username="johndoe", email="john@example.com", full_name="John Doe"
                ),
            )

            print(f"Created user: {new_user.username} (ID: {new_user.id})")

            # Update the user - this will be tracked with before/after values
            await user_crud.update(
                session, UpdateUserSchema(email="john.doe@example.com"), id=new_user.id
            )

            # Read the user
            user = await user_crud.get(
                session,
                schema_to_select=ReadUserSchema,
                return_as_model=True,
                id=new_user.id,
            )

            print(f"Updated user email: {user.email}")

            # Delete the user - this will perform a soft delete since the model has is_deleted
            await user_crud.delete(session, id=new_user.id)

            # Query all audit logs
            stmt = await session.execute(text("SELECT * FROM audit_logs"))
            audit_logs = stmt.fetchall()

            print("\nAudit Logs:")
            for log in audit_logs:
                print(
                    f"Operation: {log.operation}, Table: {log.table_name}, "
                    f"Record ID: {log.record_id}, User: {log.user_id}, "
                    f"Timestamp: {log.timestamp}"
                )

                # For update operations, show the changes
                if log.operation == OperationType.UPDATE.value and log.changes:
                    print("Changes:")
                    for field, change in log.changes.items():
                        print(f"  {field}: {change.get('old')} -> {change.get('new')}")


if __name__ == "__main__":
    asyncio.run(main())
