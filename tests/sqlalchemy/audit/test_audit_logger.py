import pytest
from unittest.mock import MagicMock
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from fastcrud.audit.logger import AuditContext, AuditLogger, LogLevel, OperationType
from fastcrud.audit.models import AuditLog


# Create test models
Base = declarative_base()


class TestModel(Base):
    __tablename__ = "test_model"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    value = Column(Integer)


@pytest.fixture
def sync_session():
    """Create a synchronous SQLAlchemy session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestSessionLocal()
    
    # Create the audit tables
    AuditBase = declarative_base()
    AuditLog.metadata = AuditBase.metadata
    AuditBase.metadata.create_all(engine)
    
    yield session
    session.close()


@pytest.fixture
def mock_async_session():
    """Create a mock AsyncSession."""
    session = MagicMock(spec=AsyncSession)
    session.commit = MagicMock()
    return session


def test_audit_logger_initialization():
    """Test the initialization of the audit logger."""
    # Default initialization
    logger = AuditLogger()
    assert logger.audit_log_model == AuditLog
    assert logger.context_getter is None
    assert logger.log_level == LogLevel.INFO
    
    # Custom initialization
    def context_getter():
        return {"user_id": "admin"}
    logger = AuditLogger(context_getter=context_getter, log_level=LogLevel.DEBUG)
    assert logger.context_getter == context_getter
    assert logger.log_level == LogLevel.DEBUG


def test_extract_record_changes():
    """Test extracting changes between old and new data."""
    logger = AuditLogger()
    
    # Test create operation (no old data)
    new_data = {"name": "Test", "value": 100}
    changes = logger._extract_record_changes(None, new_data)
    assert len(changes) == 2
    assert all(field in changes for field in ["name", "value"])
    assert changes["name"]["new"] == "Test"
    assert changes["value"]["new"] == 100
    assert "old" not in changes["name"]
    
    # Test update operation
    old_data = {"name": "Old Name", "value": 50}
    new_data = {"name": "New Name", "value": 100}
    changes = logger._extract_record_changes(old_data, new_data)
    assert len(changes) == 2
    assert changes["name"]["old"] == "Old Name"
    assert changes["name"]["new"] == "New Name"
    assert changes["value"]["old"] == 50
    assert changes["value"]["new"] == 100
    
    # Test delete operation (no new data)
    old_data = {"name": "To Delete", "value": 75}
    changes = logger._extract_record_changes(old_data, None)
    assert len(changes) == 2
    assert changes["name"]["old"] == "To Delete"
    assert changes["value"]["old"] == 75
    assert "new" not in changes["name"]


def test_get_context():
    """Test retrieving context information."""
    # Test with a direct dictionary
    context_data = {"user_id": "test_user", "ip_address": "127.0.0.1"}
    
    def context_getter():
        return context_data
    logger = AuditLogger(context_getter=context_getter)
    context = logger._get_context()
    assert context == context_data
    
    # Test with a Pydantic model
    
    def context_getter():
        return AuditContext(user_id="test_user", ip_address="127.0.0.1")
    logger = AuditLogger(context_getter=context_getter)
    context = logger._get_context()
    assert context["user_id"] == "test_user"
    assert context["ip_address"] == "127.0.0.1"
    
    # Test with a generic object
    class TestContext:
        def __init__(self):
            self.user_id = "test_user"
            self.ip_address = "127.0.0.1"
    
    
    def context_getter():
        return TestContext()
    logger = AuditLogger(context_getter=context_getter)
    context = logger._get_context()
    assert context["user_id"] == "test_user"
    assert context["ip_address"] == "127.0.0.1"


def test_log_operation_sync(sync_session):
    """Test synchronous logging of operations."""
    logger = AuditLogger()
    
    # Test CREATE operation
    audit_log = logger.log_operation(
        sync_session,
        operation=OperationType.CREATE,
        table_name="test_model",
        record_id="1",
        user_id="test_user",
        new_data={"name": "Test Create", "value": 100},
        commit=True
    )
    
    assert audit_log is not None
    assert audit_log.operation == OperationType.CREATE
    assert audit_log.table_name == "test_model"
    assert audit_log.record_id == "1"
    assert audit_log.user_id == "test_user"
    
    # Test UPDATE operation
    audit_log = logger.log_operation(
        sync_session,
        operation=OperationType.UPDATE,
        table_name="test_model",
        record_id="1",
        user_id="test_user",
        old_data={"name": "Test Create", "value": 100},
        new_data={"name": "Test Update", "value": 200},
        commit=True
    )
    
    assert audit_log is not None
    assert audit_log.operation == OperationType.UPDATE
    assert len(audit_log.changes) > 0
    
    # Test DELETE operation
    audit_log = logger.log_operation(
        sync_session,
        operation=OperationType.DELETE,
        table_name="test_model",
        record_id="1",
        user_id="test_user",
        old_data={"name": "Test Update", "value": 200},
        commit=True
    )
    
    assert audit_log is not None
    assert audit_log.operation == OperationType.DELETE


@pytest.mark.asyncio
async def test_log_operation_async(mock_async_session):
    """Test asynchronous logging of operations."""
    logger = AuditLogger()
    
    # Setup mock to store the added audit logs
    added_logs = []
    mock_async_session.add = lambda log: added_logs.append(log)
    
    # Test CREATE operation
    await logger.log_operation_async(
        mock_async_session,
        operation=OperationType.CREATE,
        table_name="test_model",
        record_id="1",
        user_id="test_user",
        new_data={"name": "Test Create", "value": 100},
        commit=True
    )
    
    assert len(added_logs) == 1
    assert added_logs[0].operation == OperationType.CREATE
    assert added_logs[0].table_name == "test_model"
    
    # Verify commit was called
    mock_async_session.commit.assert_called_once()


def test_log_level_filtering():
    """Test that log level filtering works correctly."""
    logger = AuditLogger(log_level=LogLevel.WARNING)
    
    # This should be filtered out (INFO < WARNING)
    result = logger.log_operation(
        MagicMock(),
        operation=OperationType.READ,
        table_name="test_model",
        level=LogLevel.INFO
    )
    
    assert result is None
    
    # This should pass through (WARNING == WARNING)
    mock_session = MagicMock()
    logger.log_operation(
        mock_session,
        operation=OperationType.READ,
        table_name="test_model",
        level=LogLevel.WARNING
    )
    
    # Verify add was called (log was not filtered)
    mock_session.add.assert_called_once()
