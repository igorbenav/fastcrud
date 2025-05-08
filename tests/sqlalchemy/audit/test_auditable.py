import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declarative_base

from fastcrud.audit.auditable import AuditableFastCRUD
from fastcrud.audit.logger import AuditLogger, OperationType

# Create test models
Base = declarative_base()


class TestModel(Base):
    __tablename__ = "test_model"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    value = Column(Integer)
    is_deleted = Column(Boolean, default=False)


@pytest.fixture
def mock_async_session():
    """Create a mock AsyncSession."""
    session = MagicMock(spec=AsyncSession)
    session.commit = MagicMock()
    return session


@pytest.fixture
def mock_audit_logger():
    """Create a mock AuditLogger."""
    logger = MagicMock(spec=AuditLogger)
    logger.log_operation_async = MagicMock()
    return logger


def test_auditable_fastcrud_initialization():
    """Test initializing the AuditableFastCRUD class."""
    # Default initialization
    crud = AuditableFastCRUD(TestModel)
    assert crud.model == TestModel
    assert crud.is_deleted_column == "is_deleted"
    assert crud.enable_audit is True
    
    # With custom audit logger
    custom_logger = AuditLogger()
    crud = AuditableFastCRUD(
        TestModel,
        audit_logger=custom_logger,
        is_deleted_column="custom_deleted",
        enable_audit=False
    )
    assert crud.audit_logger == custom_logger
    assert crud.is_deleted_column == "custom_deleted"
    assert crud.enable_audit is False


@pytest.mark.asyncio
async def test_create_with_audit(mock_async_session, mock_audit_logger):
    """Test that create operations are properly audited."""
    # Create a test model that will be returned by the super().create call
    test_instance = TestModel(id=1, name="Test", value=100)
    
    # Mock the superclass create method
    with patch('fastcrud.crud.fast_crud.FastCRUD.create', return_value=test_instance):
        # Initialize with our mock audit logger
        crud = AuditableFastCRUD(TestModel, audit_logger=mock_audit_logger)
        
        # Call create with a test schema
        class TestSchema:
            def model_dump(self):
                return {"name": "Test", "value": 100}
        
        result = await crud.create(mock_async_session, TestSchema())
        
        # Verify the result is correct
        assert result == test_instance
        
        # Verify audit logging was called
        assert mock_audit_logger.log_operation_async.called
        call_args = mock_audit_logger.log_operation_async.call_args[1]
        assert call_args["operation"] == OperationType.CREATE
        assert call_args["table_name"] == "test_model"
        assert call_args["new_data"] == {"name": "Test", "value": 100}


@pytest.mark.asyncio
async def test_update_with_audit(mock_async_session, mock_audit_logger):
    """Test that update operations are properly audited."""
    # Mock what super().update would return
    update_result = {"id": 1, "name": "Updated", "value": 200}
    
    # Mock get to return the old state
    old_state = {"id": 1, "name": "Original", "value": 100}
    
    with patch('fastcrud.crud.fast_crud.FastCRUD.update', return_value=update_result), \
         patch('fastcrud.crud.fast_crud.FastCRUD.get', return_value=old_state):
        
        # Initialize with our mock audit logger
        crud = AuditableFastCRUD(TestModel, audit_logger=mock_audit_logger)
        
        # Call update with a test schema
        class UpdateSchema:
            def model_dump(self, exclude_unset=False):
                return {"name": "Updated", "value": 200}
        
        result = await crud.update(
            mock_async_session,
            object=UpdateSchema(),
            id=1
        )
        
        # Verify the result is correct
        assert result == update_result
        
        # Verify audit logging was called with the right parameters
        assert mock_audit_logger.log_operation_async.called
        call_args = mock_audit_logger.log_operation_async.call_args[1]
        assert call_args["operation"] == OperationType.UPDATE
        assert call_args["table_name"] == "test_model"
        assert call_args["record_id"] == "1"
        assert call_args["old_data"] == old_state
        assert call_args["new_data"] == {"name": "Updated", "value": 200}


@pytest.mark.asyncio
async def test_delete_with_audit(mock_async_session, mock_audit_logger):
    """Test that delete operations are properly audited."""
    # Mock the current state that will be returned by get
    current_state = {"id": 1, "name": "To Delete", "value": 100}
    
    with patch('fastcrud.crud.fast_crud.FastCRUD.delete'), \
         patch('fastcrud.crud.fast_crud.FastCRUD.get', return_value=current_state):
        
        # Initialize with our mock audit logger
        crud = AuditableFastCRUD(TestModel, audit_logger=mock_audit_logger)
        
        # Call delete
        await crud.delete(
            mock_async_session,
            id=1
        )
        
        # Verify audit logging was called with the right parameters
        assert mock_audit_logger.log_operation_async.called
        call_args = mock_audit_logger.log_operation_async.call_args[1]
        assert call_args["operation"] == OperationType.DELETE
        assert call_args["table_name"] == "test_model"
        assert call_args["record_id"] == "1"
        assert call_args["old_data"] == current_state


@pytest.mark.asyncio
async def test_with_audit_context():
    """Test using the audit context manager."""
    # Initialize the crud object
    crud = AuditableFastCRUD(TestModel)
    
    # Set up a test context
    context = {"user_id": "test_user", "ip_address": "127.0.0.1"}
    
    # Get the audit context manager
    context_manager = crud.with_audit_context(context)
    
    # Verify the context was set
    assert context_manager.default_context == context
    
    # Test with disabled audit
    crud.enable_audit = False
    with pytest.raises(RuntimeError):
        crud.with_audit_context(context)


@pytest.mark.asyncio
async def test_audit_disabled_operations(mock_async_session):
    """Test that operations don't log when auditing is disabled."""
    # Initialize with auditing disabled
    crud = AuditableFastCRUD(TestModel, enable_audit=False)
    
    # Mock the necessary methods
    with patch('fastcrud.crud.fast_crud.FastCRUD.create'), \
         patch('fastcrud.crud.fast_crud.FastCRUD.update'), \
         patch('fastcrud.crud.fast_crud.FastCRUD.delete'), \
         patch('fastcrud.audit.logger.AuditLogger.log_operation_async') as mock_log:
        
        # Perform operations
        await crud.create(mock_async_session, MagicMock())
        await crud.update(mock_async_session, MagicMock(), id=1)
        await crud.delete(mock_async_session, id=1)
        
        # Verify logging was never called
        assert not mock_log.called
