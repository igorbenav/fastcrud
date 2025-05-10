import pytest
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

from fastcrud.audit.models import AuditLog, AuditLogEntry, OperationType

# Create test models
Base = declarative_base()


class SampleModel(Base):
    __tablename__ = "test_model"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    value = Column(Integer)


@pytest.fixture
def create_tables():
    """Create test database and tables."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestSessionLocal()

    # Also create the audit tables directly
    AuditLog.__table__.create(engine)
    AuditLogEntry.__table__.create(engine)

    yield session
    session.close()


def test_audit_log_create(create_tables):
    """Test creating an audit log entry."""
    session = create_tables

    # Create an audit log
    audit_log = AuditLog.create(
        operation=OperationType.CREATE,
        table_name="test_model",
        record_id="1",
        user_id="test_user",
        ip_address="127.0.0.1",
        details="Test create operation",
        new_data={"name": "Test", "value": 100},
    )

    session.add(audit_log)
    session.commit()

    # Query the audit log
    retrieved_log = session.query(AuditLog).first()

    assert retrieved_log is not None
    assert retrieved_log.operation == OperationType.CREATE
    assert retrieved_log.table_name == "test_model"
    assert retrieved_log.record_id == "1"
    assert retrieved_log.user_id == "test_user"
    assert retrieved_log.ip_address == "127.0.0.1"


def test_audit_log_with_entries(create_tables):
    """Test creating an audit log with detailed entries."""
    session = create_tables

    # Create an audit log for an update operation
    audit_log = AuditLog.create(
        operation=OperationType.UPDATE,
        table_name="test_model",
        record_id="1",
        user_id="test_user",
        old_data={"name": "Old Name", "value": 50},
        new_data={"name": "New Name", "value": 100},
    )

    session.add(audit_log)
    session.commit()

    # Add detailed entries through the add_entries method
    changes = {
        "name": {"old": "Old Name", "new": "New Name"},
        "value": {"old": 50, "new": 100},
    }

    entries = audit_log.add_entries(changes)
    session.add_all(entries)
    session.commit()

    # Query the entries
    retrieved_entries = session.query(AuditLogEntry).all()

    assert len(retrieved_entries) == 2

    # Verify field changes were recorded properly
    name_entry = next(e for e in retrieved_entries if e.field_name == "name")
    value_entry = next(e for e in retrieved_entries if e.field_name == "value")

    assert name_entry.old_value == "Old Name"
    assert name_entry.new_value == "New Name"
    assert value_entry.old_value == "50"
    assert value_entry.new_value == "100"

    # Verify the relationship works bidirectionally
    assert len(audit_log.entries) == 2


def test_enum_operation_types():
    """Test the operation type enum."""
    assert OperationType.CREATE == "create"
    assert OperationType.READ == "read"
    assert OperationType.UPDATE == "update"
    assert OperationType.DELETE == "delete"
