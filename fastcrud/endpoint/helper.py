from typing import Union, Annotated, List
from pydantic import BaseModel, Field, ValidationError
from pydantic.functional_validators import field_validator

from sqlalchemy.sql.schema import Column
from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase


class CRUDMethods(BaseModel):
    valid_methods: Annotated[
        List[str],
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
    def check_valid_method(cls, values: List[str]) -> List[str]:
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


def _get_primary_keys(model: DeclarativeBase) -> Union[str, None]:
    """Get the primary key of a SQLAlchemy model."""
    inspector = inspect(model)
    primary_key_columns = inspector.primary_key

    # Some patching when using derived sa.TypeDecorator as primary keys
    # if sa.TypeDecorator.python_type is not implemented by using
    # the sa.TypeDecorator.impl.python_type one.
    for pk in primary_key_columns:
        try:
            pk.type.python_type
        except NotImplementedError:
            pk.type.__class__.python_type = pk.type.__class__.impl.python_type

    return primary_key_columns


def _extract_unique_columns(model: type[DeclarativeBase]) -> list[Column]:
    """Extracts columns from a SQLAlchemy model that are marked as unique."""
    unique_columns = [column for column in model.__table__.columns if column.unique]
    return unique_columns
