from typing import Optional, Union, Annotated, Sequence
from pydantic import BaseModel, Field
from pydantic.functional_validators import field_validator

from sqlalchemy import Column, inspect
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql.elements import KeyedColumnElement


class CRUDMethods(BaseModel):
    valid_methods: Annotated[
        Sequence[str],
        Field(
            default=[
                "create",
                "read",
                "read_multi",
                "read_paginated",
                "update",
                "delete",
                "db_delete",
            ]
        ),
    ]

    @field_validator("valid_methods")
    def check_valid_method(cls, values: Sequence[str]) -> Sequence[str]:
        valid_methods = {
            "create",
            "read",
            "read_multi",
            "read_paginated",
            "update",
            "delete",
            "db_delete",
        }

        for v in values:
            if v not in valid_methods:
                raise ValueError(f"Invalid CRUD method: {v}")

        return values


def _get_primary_key(
    model: type[DeclarativeBase],
) -> Union[str, None]:  # pragma: no cover
    return _get_primary_keys(model)[0].name


def _get_primary_keys(model: type[DeclarativeBase]) -> Sequence[Column]:
    """Get the primary key of a SQLAlchemy model."""
    inspector = inspect(model).mapper
    primary_key_columns = inspector.primary_key

    return primary_key_columns


def _get_python_type(column: Column) -> Optional[type]:
    try:
        return column.type.python_type
    except NotImplementedError:
        if hasattr(column.type, "impl") and hasattr(column.type.impl, "python_type"):  # type: ignore
            return column.type.impl.python_type  # type: ignore
        else:  # pragma: no cover
            raise NotImplementedError(
                f"The primary key column {column.name} uses a custom type without a defined `python_type` or suitable `impl` fallback."
            )


def _extract_unique_columns(
    model: type[DeclarativeBase],
) -> Sequence[KeyedColumnElement]:
    """Extracts columns from a SQLAlchemy model that are marked as unique."""
    unique_columns = [column for column in model.__table__.columns if column.unique]
    return unique_columns
