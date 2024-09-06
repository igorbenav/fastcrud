from typing import Any, Optional, Union, Sequence, cast

from sqlalchemy import inspect
from sqlalchemy.orm.util import AliasedClass
from sqlalchemy.sql import ColumnElement
from pydantic import BaseModel, ConfigDict
from pydantic.functional_validators import field_validator

from fastcrud.types import ModelType

from ..endpoint.helper import _get_primary_key


class JoinConfig(BaseModel):
    model: Any
    join_on: Any
    join_prefix: Optional[str] = None
    schema_to_select: Optional[type[BaseModel]] = None
    join_type: str = "left"
    alias: Optional[AliasedClass] = None
    filters: Optional[dict] = None
    relationship_type: Optional[str] = "one-to-one"

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator("relationship_type")
    def check_valid_relationship_type(cls, value):
        valid_relationship_types = {"one-to-one", "one-to-many"}
        if value is not None and value not in valid_relationship_types:
            raise ValueError(f"Invalid relationship type: {value}")  # pragma: no cover
        return value

    @field_validator("join_type")
    def check_valid_join_type(cls, value):
        valid_join_types = {"left", "inner"}
        if value not in valid_join_types:
            raise ValueError(f"Unsupported join type: {value}")
        return value


def _extract_matching_columns_from_schema(
    model: Union[ModelType, AliasedClass],
    schema: Optional[type[BaseModel]],
    prefix: Optional[str] = None,
    alias: Optional[AliasedClass] = None,
    use_temporary_prefix: Optional[bool] = False,
    temp_prefix: Optional[str] = "joined__",
) -> list[Any]:
    """
    Retrieves a list of ORM column objects from a SQLAlchemy model that match the field names in a given Pydantic schema,
    or all columns from the model if no schema is provided. When an alias is provided, columns are referenced through
    this alias, and a prefix can be applied to column names if specified.

    Args:
        model: The SQLAlchemy ORM model containing columns to be matched with the schema fields.
        schema: Optional; a Pydantic schema containing field names to be matched with the model's columns. If `None`, all columns from the model are used.
        prefix: Optional; a prefix to be added to all column names. If `None`, no prefix is added.
        alias: Optional; an alias for the model, used for referencing the columns through this alias in the query. If `None`, the original model is used.
        use_temporary_prefix: Whether to use or not an aditional prefix for joins. Default `False`.
        temp_prefix: The temporary prefix to be used. Default `"joined__"`.

    Returns:
        A list of ORM column objects (potentially labeled with a prefix) that correspond to the field names defined
        in the schema or all columns from the model if no schema is specified. These columns are correctly referenced
        through the provided alias if one is given.
    """
    if not hasattr(model, "__table__"):  # pragma: no cover
        raise AttributeError(f"{model.__name__} does not have a '__table__' attribute.")

    model_or_alias = alias if alias else model
    columns = []
    temp_prefix = (
        temp_prefix if use_temporary_prefix and temp_prefix is not None else ""
    )
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


def _auto_detect_join_condition(
    base_model: ModelType,
    join_model: ModelType,
) -> Optional[ColumnElement]:
    """
    Automatically detects the join condition for SQLAlchemy models based on foreign key relationships.

    Args:
        base_model: The base SQLAlchemy model from which to join.
        join_model: The SQLAlchemy model to join with the base model.

    Returns:
        A SQLAlchemy `ColumnElement` representing the join condition, if successfully detected.

    Raises:
        ValueError: If the join condition cannot be automatically determined.
        AttributeError: If either base_model or join_model does not have a `__table__` attribute.
    """
    if not hasattr(base_model, "__table__"):  # pragma: no cover
        raise AttributeError(
            f"{base_model.__name__} does not have a '__table__' attribute."
        )
    if not hasattr(join_model, "__table__"):  # pragma: no cover
        raise AttributeError(
            f"{join_model.__name__} does not have a '__table__' attribute."
        )

    inspector = inspect(base_model)
    if inspector is not None:
        fk_columns = [col for col in inspector.c if col.foreign_keys]
        join_on = next(
            (
                cast(
                    ColumnElement,
                    base_model.__table__.c[col.name]
                    == join_model.__table__.c[list(col.foreign_keys)[0].column.name],
                )
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


def _handle_one_to_one(nested_data, nested_key, nested_field, value):
    """
    Handles the nesting of one-to-one relationships in the data.

    Args:
        nested_data: The current state of the nested data.
        nested_key: The key under which the nested data should be stored.
        nested_field: The field name of the nested data to be added.
        value: The value of the nested data to be added.

    Returns:
        dict[str, Any]: The updated nested data dictionary.

    Examples:

        Input:

        ```python
        nested_data = {
            'id': 1,
            'name': 'Test Author',
        }
        nested_key = 'profile'
        nested_field = 'bio'
        value = 'This is a bio.'
        ```

        Output:

        ```json
        {
            'id': 1,
            'name': 'Test Author',
            'profile': {
                'bio': 'This is a bio.'
            }
        }
        ```
    """
    if nested_key not in nested_data or not isinstance(nested_data[nested_key], dict):
        nested_data[nested_key] = {}
    nested_data[nested_key][nested_field] = value
    return nested_data


def _handle_one_to_many(nested_data, nested_key, nested_field, value):
    """
    Handles the nesting of one-to-many relationships in the data.

    Args:
        nested_data: The current state of the nested data.
        nested_key: The key under which the nested data should be stored.
        nested_field: The field name of the nested data to be added.
        value: The value of the nested data to be added.

    Returns:
        dict[str, Any]: The updated nested data dictionary.

    Examples:

        Input:

        ```python
        nested_data = {
            'id': 1,
            'name': 'Test Author',
            'articles': [
                {
                    'title': 'First Article',
                    'content': 'Content of the first article!',
                }
            ],
        }
        nested_key = 'articles'
        nested_field = 'title'
        value = 'Second Article'
        ```

        Output:

        ```json
        {
            'id': 1,
            'name': 'Test Author',
            'articles': [
                {
                    'title': 'First Article',
                    'content': 'Content of the first article!'
                },
                {
                    'title': 'Second Article'
                }
            ]
        }
        ```

        Input:

        ```python
        nested_data = {
            'id': 1,
            'name': 'Test Author',
            'articles': [],
        }
        nested_key = 'articles'
        nested_field = 'title'
        value = 'First Article'
        ```

        Output:

        ```json
        {
            'id': 1,
            'name': 'Test Author',
            'articles': [
                {
                    'title': 'First Article'
                }
            ]
        }
        ```
    """
    if nested_key not in nested_data or not isinstance(nested_data[nested_key], list):
        nested_data[nested_key] = []

    if not nested_data[nested_key] or nested_field in nested_data[nested_key][-1]:
        nested_data[nested_key].append({nested_field: value})
    else:
        nested_data[nested_key][-1][nested_field] = value

    return nested_data


def _nest_join_data(
    data: dict,
    join_definitions: list[JoinConfig],
    temp_prefix: str = "joined__",
    nested_data: Optional[dict[str, Any]] = None,
) -> dict:
    """
    Nests joined data based on join definitions provided. This function processes the input `data` dictionary, identifying keys
    that correspond to joined tables using the provided `join_definitions` and nest them under their respective table keys.

    Args:
        data: The flat dictionary containing data with potentially prefixed keys from joined tables.
        join_definitions: A list of `JoinConfig` instances defining the join configurations, including prefixes.
        temp_prefix: The temporary prefix applied to joined columns to differentiate them. Defaults to `"joined__"`.
        nested_data: The nested dictionary to which the data will be added. If None, a new dictionary is created. Defaults to `None`.

    Returns:
        dict[str, Any]: A dictionary with nested structures for joined table data.

    Examples:

        Input:

        ```python
        data = {
            'id': 1,
            'title': 'Test Author',
            'joined__articles_id': 1,
            'joined__articles_title': 'Article 1',
            'joined__articles_author_id': 1
        }

        join_definitions = [
            JoinConfig(
                model=Article,
                join_prefix='articles_',
                relationship_type='one-to-many',
            ),
        ]
        ```

        Output:

        ```json
        {
            'id': 1,
            'title': 'Test Author',
            'articles': [
                {
                    'id': 1,
                    'title': 'Article 1',
                    'author_id': 1
                }
            ]
        }
        ```

        Input:

        ```python
        data = {
            'id': 1,
            'title': 'Test Article',
            'joined__author_id': 1,
            'joined__author_name': 'Author 1'
        }

        join_definitions = [
            JoinConfig(
                model=Author,
                join_prefix='author_',
                relationship_type='one-to-one',
            ),
        ]
        ```

        Output:

        ```json
        {
            'id': 1,
            'title': 'Test Article',
            'author': {
                'id': 1,
                'name': 'Author 1'
            }
        }
        ```
    """
    if nested_data is None:
        nested_data = {}

    for key, value in data.items():
        nested = False
        for join in join_definitions:
            join_prefix = join.join_prefix or ""
            full_prefix = f"{temp_prefix}{join_prefix}"

            if isinstance(key, str) and key.startswith(full_prefix):
                nested_key = (
                    join_prefix.rstrip("_") if join_prefix else join.model.__tablename__
                )
                nested_field = key[len(full_prefix) :]

                if join.relationship_type == "one-to-many":
                    nested_data = _handle_one_to_many(
                        nested_data, nested_key, nested_field, value
                    )
                else:
                    nested_data = _handle_one_to_one(
                        nested_data, nested_key, nested_field, value
                    )

                nested = True
                break

        if not nested:
            stripped_key = (
                key[len(temp_prefix) :]
                if isinstance(key, str) and key.startswith(temp_prefix)
                else key
            )
            if nested_data is None:  # pragma: no cover
                nested_data = {}

            nested_data[stripped_key] = value

    if nested_data is None:  # pragma: no cover
        nested_data = {}

    for join in join_definitions:
        join_primary_key = _get_primary_key(join.model)
        nested_key = (
            join.join_prefix.rstrip("_")
            if join.join_prefix
            else join.model.__tablename__
        )
        if join.relationship_type == "one-to-many" and nested_key in nested_data:
            if isinstance(nested_data.get(nested_key, []), list):
                if any(
                    item[join_primary_key] is None for item in nested_data[nested_key]
                ):
                    nested_data[nested_key] = []

        if nested_key in nested_data and isinstance(nested_data[nested_key], dict):
            if (
                join_primary_key in nested_data[nested_key]
                and nested_data[nested_key][join_primary_key] is None
            ):
                nested_data[nested_key] = None

    assert nested_data is not None, "Couldn't nest the data."
    return nested_data


def _nest_multi_join_data(
    base_primary_key: str,
    data: list[Union[dict, BaseModel]],
    joins_config: Sequence[JoinConfig],
    return_as_model: bool = False,
    schema_to_select: Optional[type[BaseModel]] = None,
    nested_schema_to_select: Optional[dict[str, type[BaseModel]]] = None,
) -> Sequence[Union[dict, BaseModel]]:
    """
    Nests joined data based on join definitions provided for multiple records. This function processes the input list of
    dictionaries, identifying keys that correspond to joined tables using the provided `joins_config`, and nests them
    under their respective table keys.

    Args:
        base_primary_key: The primary key of the base model.
        data: The list of dictionaries containing the records with potentially nested data.
        joins_config: The list of join configurations containing the joined model classes and related settings.
        schema_to_select: Pydantic schema for selecting specific columns from the primary model. Used for converting
                          dictionaries back to Pydantic models.
        return_as_model: If `True`, converts the fetched data to Pydantic models based on `schema_to_select`. Defaults to `False`.
        nested_schema_to_select: A dictionary mapping join prefixes to their corresponding Pydantic schemas.

    Returns:
        Sequence[Union[dict, BaseModel]]: A list of dictionaries with nested structures for joined table data or Pydantic models.

    Example:

        Input:

        ```python
        data = [
            {'id': 1, 'title': 'Test Author', 'articles': [{'id': 1, 'title': 'Article 1', 'author_id': 1}]},
            {'id': 2, 'title': 'Test Author 2', 'articles': [{'id': 2, 'title': 'Article 2', 'author_id': 2}]},
            {'id': 2, 'title': 'Test Author 2', 'articles': [{'id': 3, 'title': 'Article 3', 'author_id': 2}]},
            {'id': 3, 'title': 'Test Author 3', 'articles': [{'id': None, 'title': None, 'author_id': None}]},
        ]

        joins_config = [
            JoinConfig(model=Article, join_prefix='articles_', relationship_type='one-to-many')
        ]
        ```

        Output:

        ```json
        [
            {
                'id': 1,
                'title': 'Test Author',
                'articles': [
                    {
                        'id': 1,
                        'title': 'Article 1',
                        'author_id': 1
                    }
                ]
            },
            {
                'id': 2,
                'title': 'Test Author 2',
                'articles': [
                    {
                        'id': 2,
                        'title': 'Article 2',
                        'author_id': 2
                    },
                    {
                        'id': 3,
                        'title': 'Article 3',
                        'author_id': 2
                    }
                ]
            },
            {
                'id': 3,
                'title': 'Test Author 3',
                'articles': []
            }
        ]
        ```
    """
    pre_nested_data = {}

    for join_config in joins_config:
        join_primary_key = _get_primary_key(join_config.model)

        for row in data:
            if isinstance(row, BaseModel):
                new_row = {
                    key: (value[:] if isinstance(value, list) else value)
                    for key, value in row.model_dump().items()
                }
            else:
                new_row = {
                    key: (value[:] if isinstance(value, list) else value)
                    for key, value in row.items()
                }

            primary_key_value = new_row[base_primary_key]

            if primary_key_value not in pre_nested_data:
                for key, value in new_row.items():
                    if isinstance(value, list) and any(
                        item[join_primary_key] is None for item in value
                    ):  # pragma: no cover
                        new_row[key] = []
                    elif (
                        isinstance(value, dict) and value[join_primary_key] is None
                    ):  # pragma: no cover
                        new_row[key] = None

                pre_nested_data[primary_key_value] = new_row
            else:
                existing_row = pre_nested_data[primary_key_value]
                for key, value in new_row.items():
                    if isinstance(value, list):
                        if any(
                            item[join_primary_key] is None for item in value
                        ):  # pragma: no cover
                            existing_row[key] = []
                        else:
                            existing_row[key].extend(value)

    nested_data: list = list(pre_nested_data.values())

    if return_as_model:
        for i, item in enumerate(nested_data):
            if nested_schema_to_select:
                for prefix, schema in nested_schema_to_select.items():
                    if prefix in item:
                        if isinstance(item[prefix], list):
                            item[prefix] = [
                                schema(**nested_item) for nested_item in item[prefix]
                            ]
                        else:  # pragma: no cover
                            item[prefix] = schema(**item[prefix])
            if schema_to_select:
                nested_data[i] = schema_to_select(**item)

    return nested_data


def _handle_null_primary_key_multi_join(
    data: list[Union[dict[str, Any], BaseModel]], join_definitions: list[JoinConfig]
) -> list[Union[dict[str, Any], BaseModel]]:
    for item in data:
        item_dict = item if isinstance(item, dict) else item.model_dump()

        for join in join_definitions:
            join_prefix = join.join_prefix or ""
            nested_key = (
                join_prefix.rstrip("_") if join_prefix else join.model.__tablename__
            )

            if nested_key in item_dict and isinstance(item_dict[nested_key], dict):
                join_primary_key = _get_primary_key(join.model)

                primary_key = join_primary_key
                if join_primary_key:
                    if (
                        primary_key in item_dict[nested_key]
                        and item_dict[nested_key][primary_key] is None
                    ):  # pragma: no cover
                        item_dict[nested_key] = None

        if isinstance(item, BaseModel):
            for key, value in item_dict.items():
                setattr(item, key, value)

    return data
