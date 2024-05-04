from typing import Optional, Union, Annotated, Sequence, Callable
from pydantic import BaseModel, Field
from pydantic.functional_validators import field_validator
from fastapi import Depends, params

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
    key: Optional[str] = _get_primary_keys(model)[0].name
    return key


def _get_primary_keys(model: type[DeclarativeBase]) -> Sequence[Column]:
    """Get the primary key of a SQLAlchemy model."""
    inspector = inspect(model).mapper
    primary_key_columns: Sequence[Column] = inspector.primary_key

    return primary_key_columns


def _get_python_type(column: Column) -> Optional[type]:
    try:
        direct_type: Optional[type] = column.type.python_type
        return direct_type
    except NotImplementedError:
        if hasattr(column.type, "impl") and hasattr(column.type.impl, "python_type"):
            indirect_type: Optional[type] = column.type.impl.python_type
            return indirect_type
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


def _inject_dependencies(
    funcs: Optional[Sequence[Callable]] = None,
) -> Sequence[params.Depends]:
    """Wraps a list of functions in FastAPI's Depends."""
    dependencies = []
    if funcs is not None:
        for func in funcs:
            dependency = Depends(func)
            dependencies.append(dependency)
    return dependencies
