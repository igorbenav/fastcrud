from typing import Union, Annotated, Sequence
from pydantic import BaseModel, Field, ValidationError
from pydantic.functional_validators import field_validator

from sqlalchemy import inspect
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
                raise ValidationError(f"Invalid CRUD method: {v}")

        return values


def _get_primary_key(model: type[DeclarativeBase]) -> Union[str, None]:
    return _get_primary_keys(model)[0]


def _get_primary_keys(model: DeclarativeBase) -> Union[str, None]:
    """Get the primary key of a SQLAlchemy model."""
    inspector = inspect(model).mapper
    primary_key_columns = inspector.primary_key
    return [
        primary_key_column.name if primary_key_columns else None
        for primary_key_column in primary_key_columns
    ]


def _extract_unique_columns(
    model: type[DeclarativeBase],
) -> Sequence[KeyedColumnElement]:
    """Extracts columns from a SQLAlchemy model that are marked as unique."""
    unique_columns = [column for column in model.__table__.columns if column.unique]
    return unique_columns
