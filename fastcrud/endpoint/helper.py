from typing import Union

from sqlalchemy.sql.schema import Column
from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase


def _get_primary_key(model: DeclarativeBase) -> Union[str, None]:
    """Get the primary key of a SQLAlchemy model."""
    inspector = inspect(model)
    primary_key_columns = inspector.primary_key
    return primary_key_columns[0].name if primary_key_columns else None


def _extract_unique_columns(model: type[DeclarativeBase]) -> list[Column]:
    """Extracts columns from a SQLAlchemy model that are marked as unique."""
    unique_columns = [column for column in model.__table__.columns if column.unique]
    return unique_columns
