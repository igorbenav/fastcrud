from typing import Any, Optional, NamedTuple, Union

from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase
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
    filters: Optional[dict] = None


def _extract_matching_columns_from_schema(
    model: Union[type[DeclarativeBase], AliasedClass],
    schema: Optional[type[BaseModel]],
    prefix: Optional[str] = None,
    alias: Optional[AliasedClass] = None,
    use_temporary_prefix: bool = False,
    temp_prefix="joined__",
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
    temp_prefix = temp_prefix if use_temporary_prefix else ""
    if schema:
        for field in schema.model_fields.keys():
            if hasattr(model_or_alias, field):
                column = getattr(model_or_alias, field)
                if prefix is not None or use_temporary_prefix:
                    column_label = (
                        f"{temp_prefix}{prefix}{field}"
                        if prefix
                        else f"{temp_prefix}{field}"
                    )
                    column = column.label(column_label)
                columns.append(column)
    else:
        for column in model.__table__.c:
            column = getattr(model_or_alias, column.key)
            if prefix is not None or use_temporary_prefix:
                column_label = (
                    f"{temp_prefix}{prefix}{column.key}"
                    if prefix
                    else f"{temp_prefix}{column.key}"
                )
                column = column.label(column_label)
            columns.append(column)

    return columns


def _nest_join_data(
    data: dict[str, Any],
    join_definitions: list[JoinConfig],
    temp_prefix: str = "joined__",
) -> dict[str, Any]:
    nested_data: dict = {}
    for key, value in data.items():
        nested = False
        for join in join_definitions:
            full_prefix = (
                f"{temp_prefix}{join.join_prefix}" if join.join_prefix else temp_prefix
            )
            if key.startswith(full_prefix):
                nested_key = (
                    join.join_prefix.rstrip("_")
                    if join.join_prefix
                    else join.model.__tablename__
                )
                nested_field = key[len(full_prefix) :]
                if nested_key not in nested_data:
                    nested_data[nested_key] = {}
                nested_data[nested_key][nested_field] = value
                nested = True
                break
        if not nested:
            stripped_key = (
                key[len(temp_prefix) :] if key.startswith(temp_prefix) else key
            )
            nested_data[stripped_key] = value

    return nested_data


def _auto_detect_join_condition(
    base_model: type[DeclarativeBase], join_model: type[DeclarativeBase]
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
    inspector = inspect(base_model)
    if inspector is not None:
        fk_columns = [col for col in inspector.c if col.foreign_keys]
        join_on = next(
            (
                base_model.__table__.c[col.name]
                == join_model.__table__.c[list(col.foreign_keys)[0].column.name]
                for col in fk_columns
                if list(col.foreign_keys)[0].column.table == join_model.__table__
            ),
            None,
        )

        if join_on is None:  # pragma: no cover
            raise ValueError(
                "Could not automatically determine join condition. Please provide join_on."
            )
    else:  # pragma: no cover
        raise ValueError("Could not automatically get model columns.")

    return join_on
