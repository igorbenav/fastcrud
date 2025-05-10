# PR Title: Add Comprehensive Auditing and Logging System to FastCRUD

## Description

This PR introduces a complete auditing and logging system for FastCRUD that tracks database operations, user actions, and data changes. The new `audit` module provides tools to enhance accountability, compliance, and debugging capabilities without requiring significant changes to existing code.

## Features

- **Operation Tracking**: Records create, read, update, and delete operations
- **Change Tracking**: Captures before/after values for all field updates
- **User Attribution**: Tracks which user performed each operation
- **Context Capture**: Records IP address, user agent, and custom context data
- **Integrated Logging**: Works with both database storage and standard Python logging
- **Non-intrusive Implementation**: Drop-in replacement via `AuditableFastCRUD` class

## Implementation Details

The auditing system consists of the following components:

1. **Database Models**: `AuditLog` and `AuditLogEntry` tables for storing audit data
2. **Audit Logger**: Core logging functionality with both async and sync support
3. **Context Management**: Session-based context tracking for user information
4. **Auditable CRUD Class**: Extension of FastCRUD with built-in auditing capabilities

## Usage Example

```python
# Import the auditable CRUD class
from fastcrud.audit import AuditableFastCRUD, AuditContext

# Create an auditable CRUD instance (drop-in replacement for FastCRUD)
user_crud = AuditableFastCRUD(User)

# Set audit context with user information
context = AuditContext(
    user_id="admin",
    ip_address="127.0.0.1",
    user_agent="Browser/1.0"
)

# Use the context manager for audit tracking
async with user_crud.audit_context_manager.audited_async_session(db, context):
    # All operations in this block will include the user context in audit logs
    await user_crud.create(db, user_schema)
    await user_crud.update(db, update_schema, id=1)
    await user_crud.delete(db, id=2)
```

## Benefits

- **Compliance Support**: Helps meet regulatory requirements for data auditing
- **Enhanced Debugging**: Simplifies troubleshooting by tracking all data changes
- **Security Monitoring**: Identifies suspicious activity patterns
- **Change History**: Provides a complete history of record modifications
- **Minimal Overhead**: Efficient implementation with configurable logging levels

## Testing

Added a comprehensive example in `fastcrud/examples/audit_example.py` that demonstrates the complete functionality of the auditing system, including:
- Creating the necessary audit tables
- Recording create/update/delete operations
- Capturing user context
- Retrieving and displaying audit logs

## Documentation

Full documentation added for all components with detailed examples of how to use the auditing functionality in various scenarios.

## Related Issues

Addresses feature request for enhanced auditing capabilities.

## Development Requirements

- ✅ Added comprehensive tests in `tests/sqlalchemy/audit/` directory
- ✅ Code passes mypy type checking
- ✅ Code follows style guidelines (verified with ruff)
- ✅ Documentation added for all components
