import inspect
from typing import Optional, Union, Annotated, Sequence, Callable, TypeVar, Any
import warnings

from pydantic import BaseModel, Field
from pydantic.functional_validators import field_validator
from fastapi import Depends, Query, params

from sqlalchemy import Column, inspect as sa_inspect
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql.elements import KeyedColumnElement

F = TypeVar("F", bound=Callable[..., Any])


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


class FilterConfig(BaseModel):
    filters: Annotated[dict[str, Any], Field(default={})]

    @field_validator("filters")
    def check_filter_types(cls, filters: dict[str, Any]) -> dict[str, Any]:
        for key, value in filters.items():
            if not isinstance(value, (type(None), str, int, float, bool)):
                raise ValueError(f"Invalid default value for '{key}': {value}")
        return filters

    def __init__(self, **kwargs: Any) -> None:
        filters = kwargs.pop("filters", {})
        filters.update(kwargs)
        super().__init__(filters=filters)

    def get_params(self) -> dict[str, Any]:
        params = {}
        for key, value in self.filters.items():
            params[key] = Query(value)
        return params


def _get_primary_key(
    model: type[DeclarativeBase],
) -> Union[str, None]:  # pragma: no cover
    key: Optional[str] = _get_primary_keys(model)[0].name
    return key


def _get_primary_keys(model: type[DeclarativeBase]) -> Sequence[Column]:
    """Get the primary key of a SQLAlchemy model."""
    inspector = sa_inspect(model).mapper
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


def _get_column_types(model: type[DeclarativeBase]) -> dict[str, Union[type, None]]:
    """Get a dictionary of column names and their corresponding Python types from a SQLAlchemy model."""
    inspector = sa_inspect(model).mapper
    column_types = {}
    for column in inspector.columns:
        column_types[column.name] = _get_python_type(column)
    return column_types


def _extract_unique_columns(
    model: type[DeclarativeBase],
) -> Sequence[KeyedColumnElement]:
    """Extracts columns from a SQLAlchemy model that are marked as unique."""
    unique_columns = [column for column in model.__table__.columns if column.unique]
    return unique_columns


def _temporary_dependency_handling(
    funcs: Optional[Sequence[Callable]] = None,
) -> Union[Sequence[params.Depends], None]:  # pragma: no cover
    """
    Checks if any function in the provided sequence is an instance of params.Depends.
    Issues a deprecation warning once if such instances are found, and returns the sequence if any params.Depends are found.

    Args:
        funcs: Optional sequence of callables or params.Depends instances.
    """
    if funcs is not None:
        if any(isinstance(func, params.Depends) for func in funcs):
            warnings.warn(
                "Passing a function wrapped in `Depends` directly to dependency handlers is deprecated and will be removed in version 0.15.0.",
                DeprecationWarning,
                stacklevel=2,
            )
            return [
                func if isinstance(func, params.Depends) else Depends(func)
                for func in funcs
            ]
    return None


def _inject_dependencies(
    funcs: Optional[Sequence[Callable]] = None,
) -> Optional[Sequence[params.Depends]]:
    """Wraps a list of functions in FastAPI's Depends."""
    temp_handling = _temporary_dependency_handling(funcs)
    if temp_handling is not None:  # pragma: no cover
        return temp_handling

    if funcs is not None:
        return [Depends(func) for func in funcs]

    return None


def _apply_model_pk(**pkeys: dict[str, type]):
    """
    This decorator injects positional arguments into a fastCRUD endpoint.
    It dynamically changes the endpoint signature and allows to use
    multiple primary keys without defining them explicitly.
    """

    def wrapper(endpoint):
        signature = inspect.signature(endpoint)
        parameters = [
            p
            for p in signature.parameters.values()
            if p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
        ]
        extra_positional_params = [
            inspect.Parameter(
                name=k, annotation=v, kind=inspect.Parameter.POSITIONAL_ONLY
            )
            for k, v in pkeys.items()
        ]

        endpoint.__signature__ = signature.replace(
            parameters=extra_positional_params + parameters
        )
        return endpoint

    return wrapper


def _create_dynamic_filters(
    filter_config: Optional[FilterConfig] = None,
    column_types: Optional[dict[str, type]] = None,
) -> Callable[..., dict[str, Any]]:
    if filter_config is None:
        return lambda: {}

    filter_params = filter_config.get_params()

    def filters(**kwargs: Any) -> dict[str, Any]:
        return {k: v for k, v in kwargs.items() if v is not None}

    params = [
        inspect.Parameter(
            name=key,
            kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=Query(value),
            annotation=column_types.get(key, str) if column_types else str,
        )
        for key, value in filter_params.items()
    ]

    sig = inspect.Signature(params)
    setattr(filters, "__signature__", sig)

    return filters
