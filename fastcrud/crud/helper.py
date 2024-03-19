from typing import Any, Optional, NamedTuple

from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase, DeclarativeMeta
from sqlalchemy.orm.util import AliasedClass
from sqlalchemy.sql import ColumnElement
from pydantic import BaseModel


class JoinConfig(NamedTuple):
    model: Any
    join_on: Any
    join_prefix: Optional[str] = None
    schema_to_select: Optional[type[BaseModel]] = None
    join_type: str = "left"
    alias: Optional[AliasedClass] = None


def _extract_matching_columns_from_schema(
    model: type[DeclarativeBase],
    schema: Optional[type[BaseModel]],
    prefix: Optional[str] = None,
    alias: Optional[AliasedClass] = None,
) -> list[Any]:
    """
    Retrieves a list of ORM column objects from a SQLAlchemy model that match the field names in a given Pydantic schema,
    or all columns from the model if no schema is provided. When an alias is provided, columns are referenced through
    this alias, and a prefix can be applied to column names if specified.

    Args:
        model: The SQLAlchemy ORM model containing columns to be matched with the schema fields.
        schema: Optional; a Pydantic schema containing field names to be matched with the model's columns. If None, all columns from the model are used.
        prefix: Optional; a prefix to be added to all column names. If None, no prefix is added.
        alias: Optional; an alias for the model, used for referencing the columns through this alias in the query. If None, the original model is used.

    Returns:
        A list of ORM column objects (potentially labeled with a prefix) that correspond to the field names defined
        in the schema or all columns from the model if no schema is specified. These columns are correctly referenced
        through the provided alias if one is given.
    """
    model_or_alias = alias if alias else model
    columns = []
    if schema:
        for field in schema.model_fields.keys():
            if hasattr(model_or_alias, field):
                column = getattr(model_or_alias, field)
                if prefix:
                    column = column.label(f"{prefix}{field}")
                columns.append(column)
    else:
        for column in model.__table__.c:
            column = getattr(model_or_alias, column.key)
            if prefix:
                column = column.label(f"{prefix}{column.key}")
            columns.append(column)

    return columns


def _auto_detect_join_condition(
    base_model: type[DeclarativeMeta], join_model: type[DeclarativeMeta]
) -> Optional[ColumnElement]:
    """
    Automatically detects the join condition for SQLAlchemy models based on foreign key relationships.

    Args:
        base_model: The base SQLAlchemy model from which to join.
        join_model: The SQLAlchemy model to join with the base model.

    Returns:
        A SQLAlchemy ColumnElement representing the join condition, if successfully detected.

    Raises:
        ValueError: If the join condition cannot be automatically determined.

    Example:
        # Assuming User has a foreign key reference to Tier:
        join_condition = auto_detect_join_condition(User, Tier)
    """
    fk_columns = [col for col in inspect(base_model).c if col.foreign_keys]
    join_on = next(
        (
            base_model.__table__.c[col.name]
            == join_model.__table__.c[list(col.foreign_keys)[0].column.name]
            for col in fk_columns
            if list(col.foreign_keys)[0].column.table == join_model.__table__
        ),
        None,
    )

    if join_on is None:
        raise ValueError(
            "Could not automatically determine join condition. Please provide join_on."
        )

    return join_on
