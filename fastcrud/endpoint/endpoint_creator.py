import warnings
from typing import Type, TypeVar, Optional, Callable, Sequence, Union
from enum import Enum

from fastapi import Depends, Body, Query, APIRouter
from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from ..crud.fast_crud import FastCRUD
from ..exceptions.http_exceptions import DuplicateValueException, NotFoundException
from ..paginated.helper import compute_offset
from ..paginated.response import paginated_response
from .helper import (
    CRUDMethods,
    FilterConfig,
    _extract_unique_columns,
    _get_primary_keys,
    _get_python_type,
    _inject_dependencies,
    _apply_model_pk,
    _create_dynamic_filters,
    _get_column_types,
)

CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
UpdateSchemaInternalType = TypeVar("UpdateSchemaInternalType", bound=BaseModel)
DeleteSchemaType = TypeVar("DeleteSchemaType", bound=BaseModel)


class EndpointCreator:
    """
    A class to create and register CRUD endpoints for a FastAPI application.

    This class simplifies the process of adding create, read, update, and delete (CRUD) endpoints
    to a FastAPI router. It is initialized with a SQLAlchemy session, model, CRUD operations,
    and Pydantic schemas, and allows for custom dependency injection for each endpoint.
    The method assumes 'id' is the primary key for path parameters.

    Attributes:
        session: The SQLAlchemy async session.
        model: The SQLAlchemy model.
        crud: An optional FastCRUD instance. If not provided, uses FastCRUD(model).
        create_schema: Pydantic schema for creating an item.
        update_schema: Pydantic schema for updating an item.
        delete_schema: Optional Pydantic schema for deleting an item.
        include_in_schema: Whether to include the created endpoints in the OpenAPI schema.
        path: Base path for the CRUD endpoints.
        tags: List of tags for grouping endpoints in the documentation.
        is_deleted_column: Optional column name to use for indicating a soft delete. Defaults to "is_deleted".
        deleted_at_column: Optional column name to use for storing the timestamp of a soft delete. Defaults to "deleted_at".
        updated_at_column: Optional column name to use for storing the timestamp of an update. Defaults to "updated_at".
        endpoint_names: Optional dictionary to customize endpoint names for CRUD operations. Keys are operation types
                        ("create", "read", "update", "delete", "db_delete", "read_multi", "read_paginated"), and
                        values are the custom names to use. Unspecified operations will use default names.
        filter_config: Optional FilterConfig instance or dictionary to configure filters for the `read_multi` and `read_paginated` endpoints.

    Raises:
        ValueError: If both `included_methods` and `deleted_methods` are provided.

    Examples:
        Basic Setup:
        ```python
        from fastapi import FastAPI
        from fastcrud import EndpointCreator

        from myapp.models import MyModel
        from myapp.schemas import CreateMyModel, UpdateMyModel
        from myapp.database import async_session

        app = FastAPI()
        endpoint_creator = EndpointCreator(
            session=async_session,
            model=MyModel,
            create_schema=CreateMyModel,
            update_schema=UpdateMyModel
        )
        endpoint_creator.add_routes_to_router()
        app.include_router(endpoint_creator.router, prefix="/mymodel")
        ```

        With Custom Dependencies:
        ```python
        from fastapi.security import OAuth2PasswordBearer

        oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

        def get_current_user(token: str = Depends(oauth2_scheme)):
            return ...

        endpoint_creator.add_routes_to_router(
            read_deps=[get_current_user],
            update_deps=[get_current_user]
        )
        ```

        Selective Endpoint Creation (inclusion):
        ```python
        # Only create 'create' and 'read' endpoints
        endpoint_creator.add_routes_to_router(
            included_methods=["create", "read"]
        )
        ```

        Selective Endpoint Creation (deletion):
        ```python
        # Create all but 'update' and 'delete' endpoints
        endpoint_creator.add_routes_to_router(
            deleted_methods=["update", "delete"]
        )
        ```

        Integrating with Multiple Models:
        ```python
        # Assuming definitions for OtherModel, CRUDOtherModel, etc.

        other_model_crud = CRUDOtherModel(OtherModel)
        other_endpoint_creator = EndpointCreator(
            session=async_session,
            model=OtherModel,
            crud=other_model_crud,
            create_schema=CreateOtherModel,
            update_schema=UpdateOtherModel
        )
        other_endpoint_creator.add_routes_to_router()
        app.include_router(other_endpoint_creator.router, prefix="/othermodel")
        ```

        Customizing Endpoint Names:
        ```python
        endpoint_creator = EndpointCreator(
            session=async_session,
            model=MyModel,
            create_schema=CreateMyModel,
            update_schema=UpdateMyModel,
            path="/mymodel",
            tags=["MyModel"],
            endpoint_names={
                "create": "add",  # Custom endpoint name for creating items
                "read": "fetch",  # Custom endpoint name for reading a single item
                "update": "change",  # Custom endpoint name for updating items
                # The delete operation will use the default name "delete"
            }
        )
        endpoint_creator.add_routes_to_router()
        ```

        Using filter_config with dict:
        ```python
        from fastapi import FastAPI
        from fastcrud import EndpointCreator, FilterConfig

        from myapp.models import MyModel
        from myapp.schemas import CreateMyModel, UpdateMyModel
        from myapp.database import async_session

        app = FastAPI()
        endpoint_creator = EndpointCreator(
            session=async_session,
            model=MyModel,
            create_schema=CreateMyModel,
            update_schema=UpdateMyModel,
            filter_config=FilterConfig(filters={"id": None, "name": "default"})
        )
        # Adds CRUD routes with filtering capabilities
        endpoint_creator.add_routes_to_router()
        # Include the internal router into the FastAPI app
        app.include_router(endpoint_creator.router, prefix="/mymodel")

        # Explanation:
        # The FilterConfig specifies that 'id' should be a query parameter with no default value
        # and 'name' should be a query parameter with a default value of 'default'.
        # When fetching multiple items, you can filter by these parameters.
        # Example GET request: /mymodel/get_multi?id=1&name=example
        ```

        Using filter_config with keyword arguments:
        ```python
        from fastapi import FastAPI
        from fastcrud import EndpointCreator, FilterConfig

        from myapp.models import MyModel
        from myapp.schemas: CreateMyModel, UpdateMyModel
        from myapp.database: async_session

        app = FastAPI()
        endpoint_creator = EndpointCreator(
            session=async_session,
            model=MyModel,
            create_schema=CreateMyModel,
            update_schema=UpdateMyModel,
            filter_config=FilterConfig(id=None, name="default")
        )
        # Adds CRUD routes with filtering capabilities
        endpoint_creator.add_routes_to_router()
        # Include the internal router into the FastAPI app
        app.include_router(endpoint_creator.router, prefix="/mymodel")

        # Explanation:
        # The FilterConfig specifies that 'id' should be a query parameter with no default value
        # and 'name' should be a query parameter with a default value of 'default'.
        # When fetching multiple items, you can filter by these parameters.
        # Example GET request: /mymodel/get_multi?id=1&name=example
        ```
    """

    def __init__(
        self,
        session: Callable,
        model: type[DeclarativeBase],
        create_schema: Type[CreateSchemaType],
        update_schema: Type[UpdateSchemaType],
        crud: Optional[FastCRUD] = None,
        include_in_schema: bool = True,
        delete_schema: Optional[Type[DeleteSchemaType]] = None,
        path: str = "",
        tags: Optional[list[Union[str, Enum]]] = None,
        is_deleted_column: str = "is_deleted",
        deleted_at_column: str = "deleted_at",
        updated_at_column: str = "updated_at",
        endpoint_names: Optional[dict[str, str]] = None,
        filter_config: Optional[Union[FilterConfig, dict]] = None,
    ) -> None:
        self._primary_keys = _get_primary_keys(model)
        self._primary_keys_types = {
            pk.name: _get_python_type(pk) for pk in self._primary_keys
        }
        self.primary_key_names = [pk.name for pk in self._primary_keys]
        self.session = session
        self.crud = crud or FastCRUD(
            model=model,
            is_deleted_column=is_deleted_column,
            deleted_at_column=deleted_at_column,
            updated_at_column=updated_at_column,
        )
        self.model = model
        self.create_schema = create_schema
        self.update_schema = update_schema
        self.delete_schema = delete_schema
        self.include_in_schema = include_in_schema
        self.path = path
        self.tags = tags or []
        self.router = APIRouter()
        self.is_deleted_column = is_deleted_column
        self.deleted_at_column = deleted_at_column
        self.updated_at_column = updated_at_column
        self.default_endpoint_names = {
            "create": "create",
            "read": "get",
            "update": "update",
            "delete": "delete",
            "db_delete": "db_delete",
            "read_multi": "get_multi",
            "read_paginated": "get_paginated",
        }
        self.endpoint_names = {**self.default_endpoint_names, **(endpoint_names or {})}
        if self.endpoint_names == self.default_endpoint_names:
            warnings.warn(
                "Old default_endpoint_names are getting deprecated. "
                "Default values are going to be replaced by empty strings, "
                "resulting in plain endpoint names. "
                "For details see:"
                " https://github.com/igorbenav/fastcrud/issues/67",
                DeprecationWarning
            )
        if filter_config:
            if isinstance(filter_config, dict):
                filter_config = FilterConfig(**filter_config)
            self._validate_filter_config(filter_config)
        self.filter_config = filter_config
        self.column_types = _get_column_types(model)

    def _validate_filter_config(self, filter_config: FilterConfig) -> None:
        model_columns = self.crud.model_col_names
        for key in filter_config.filters.keys():
            if key not in model_columns:
                raise ValueError(
                    f"Invalid filter column '{key}': not found in model '{self.model.__name__}' columns"
                )

    def _create_item(self):
        """Creates an endpoint for creating items in the database."""

        async def endpoint(
            db: AsyncSession = Depends(self.session),
            item: self.create_schema = Body(...),  # type: ignore
        ):
            unique_columns = _extract_unique_columns(self.model)

            for column in unique_columns:
                col_name = column.name
                if hasattr(item, col_name):
                    value = getattr(item, col_name)
                    exists = await self.crud.exists(db, **{col_name: value})
                    if exists:  # pragma: no cover
                        raise DuplicateValueException(
                            f"Value {value} is already registered"
                        )

            return await self.crud.create(db, item)

        return endpoint

    def _read_item(self):
        """Creates an endpoint for reading a single item from the database."""

        @_apply_model_pk(**self._primary_keys_types)
        async def endpoint(db: AsyncSession = Depends(self.session), **pkeys):
            item = await self.crud.get(db, **pkeys)
            if not item:  # pragma: no cover
                raise NotFoundException(detail="Item not found")
            return item  # pragma: no cover

        return endpoint

    def _read_items(self):
        """Creates an endpoint for reading multiple items from the database."""
        dynamic_filters = _create_dynamic_filters(self.filter_config, self.column_types)

        async def endpoint(
            db: AsyncSession = Depends(self.session),
            page: Optional[int] = Query(
                None, alias="page", description="Page number"
            ),
            items_per_page: Optional[int] = Query(
                None, alias="itemsPerPage", description="Number of items per page"
            ),
            filters: dict = Depends(dynamic_filters),
        ):
            if not (page and items_per_page):
                return await self.crud.get_multi(db, offset=0, limit=100,
                                                 **filters)

            offset = compute_offset(page=page, items_per_page=items_per_page)
            crud_data = await self.crud.get_multi(
                db, offset=offset, limit=items_per_page, **filters
            )

            return paginated_response(
                crud_data=crud_data, page=page, items_per_page=items_per_page
            )  # pragma: no cover

        return endpoint

    def _read_paginated(self):
        """Creates an endpoint for reading multiple items from the database with pagination."""
        dynamic_filters = _create_dynamic_filters(self.filter_config, self.column_types)
        warnings.warn(
            "_read_paginated endpoint is getting deprecated and mixed "
            "into _read_items in the next major release. "
            "Please use _read_items with optional page and items_per_page "
            "query params instead, to achieve pagination as before."
            "Simple _read_items behaviour persists with no breaking changes.",
            DeprecationWarning
        )

        async def endpoint(
            db: AsyncSession = Depends(self.session),
            page: int = Query(
                1, alias="page", description="Page number, starting from 1"
            ),
            items_per_page: int = Query(
                10, alias="itemsPerPage", description="Number of items per page"
            ),
            filters: dict = Depends(dynamic_filters),
        ):
            if not (page and items_per_page):  # pragma: no cover
                return await self.crud.get_multi(db, offset=0, limit=100,
                                                 **filters)

            offset = compute_offset(page=page, items_per_page=items_per_page)
            crud_data = await self.crud.get_multi(
                db, offset=offset, limit=items_per_page, **filters
            )

            return paginated_response(
                crud_data=crud_data, page=page, items_per_page=items_per_page
            )  # pragma: no cover

        return endpoint

    def _update_item(self):
        """Creates an endpoint for updating an existing item in the database."""

        @_apply_model_pk(**self._primary_keys_types)
        async def endpoint(
            item: self.update_schema = Body(...),  # type: ignore
            db: AsyncSession = Depends(self.session),
            **pkeys,
        ):
            return await self.crud.update(db, item, **pkeys)

        return endpoint

    def _delete_item(self):
        """Creates an endpoint for deleting an item from the database."""

        @_apply_model_pk(**self._primary_keys_types)
        async def endpoint(db: AsyncSession = Depends(self.session), **pkeys):
            await self.crud.delete(db, **pkeys)
            return {"message": "Item deleted successfully"}  # pragma: no cover

        return endpoint

    def _db_delete(self):
        """
        Creates an endpoint for hard deleting an item from the database.

        This endpoint is only added if the delete_schema is provided during initialization.
        The endpoint expects an item ID as a path parameter and uses the provided SQLAlchemy
        async session to permanently delete the item from the database.
        """

        @_apply_model_pk(**self._primary_keys_types)
        async def endpoint(db: AsyncSession = Depends(self.session), **pkeys):
            await self.crud.db_delete(db, **pkeys)
            return {
                "message": "Item permanently deleted from the database"
            }  # pragma: no cover

        return endpoint

    def _get_endpoint_path(self, operation: str):
        endpoint_name = self.endpoint_names.get(
            operation, self.default_endpoint_names.get(operation, operation)
        )
        path = f"{self.path}/{endpoint_name}" if endpoint_name else self.path

        if operation in {'read', 'update', 'delete', 'db_delete'}:
            _primary_keys_path_suffix = "/".join(
                f"{{{n}}}" for n in self.primary_key_names
            )
            path = f'{path}/{_primary_keys_path_suffix}'

        return path

    def add_routes_to_router(
        self,
        create_deps: Sequence[Callable] = [],
        read_deps: Sequence[Callable] = [],
        read_multi_deps: Sequence[Callable] = [],
        read_paginated_deps: Sequence[Callable] = [],
        update_deps: Sequence[Callable] = [],
        delete_deps: Sequence[Callable] = [],
        db_delete_deps: Sequence[Callable] = [],
        included_methods: Optional[Sequence[str]] = None,
        deleted_methods: Optional[Sequence[str]] = None,
    ):
        """
        Adds CRUD operation routes to the FastAPI router with specified dependencies for each type of operation.

        This method registers routes for create, read, update, and delete operations with the FastAPI router,
        allowing for custom dependency injection for each type of operation.

        Args:
            create_deps: List of functions to be injected as dependencies for the create endpoint.
            read_deps: List of functions to be injected as dependencies for the read endpoint.
            read_multi_deps: List of functions to be injected as dependencies for the read multiple items endpoint.
            update_deps: List of functions to be injected as dependencies for the update endpoint.
            delete_deps: List of functions to be injected as dependencies for the delete endpoint.
            db_delete_deps: List of functions to be injected as dependencies for the hard delete endpoint.
            included_methods: Optional list of methods to include. Defaults to all CRUD methods.
            deleted_methods: Optional list of methods to exclude. Defaults to None.

        Raises:
            ValueError: If both `included_methods` and `deleted_methods` are provided.

        Examples:
            Selective Endpoint Creation:
            ```python
            # Only create 'create' and 'read' endpoints
            endpoint_creator.add_routes_to_router(
                included_methods=["create", "read"]
            )
            ```

            Excluding Specific Endpoints:
            ```python
            # Create all endpoints except 'delete' and 'db_delete'
            endpoint_creator.add_routes_to_router(
                deleted_methods=["delete", "db_delete"]
            )
            ```

            With Custom Dependencies and Selective Endpoints:
            ```python
            def get_current_user(...):
                ...

            # Create only 'read' and 'update' endpoints with custom dependencies
            endpoint_creator.add_routes_to_router(
                read_deps=[get_current_user],
                update_deps=[get_current_user],
                included_methods=["read", "update"]
            )
            ```

        Note:
            This method should be called to register the endpoints with the FastAPI application.
            If 'delete_schema' is provided, a hard delete endpoint is also registered.
            This method assumes 'id' is the primary key for path parameters.
        """
        if (included_methods is not None) and (deleted_methods is not None):
            raise ValueError(
                "Cannot use both 'included_methods' and 'deleted_methods' simultaneously."
            )

        if included_methods is None:
            included_methods = [
                "create",
                "read",
                "read_multi",
                "read_paginated",
                "update",
                "delete",
                "db_delete",
            ]
        else:
            try:
                included_methods = CRUDMethods(
                    valid_methods=included_methods
                ).valid_methods
            except ValidationError as e:
                raise ValueError(f"Invalid CRUD methods in included_methods: {e}")

        if deleted_methods is None:
            deleted_methods = []
        else:
            try:
                deleted_methods = CRUDMethods(
                    valid_methods=deleted_methods
                ).valid_methods
            except ValidationError as e:
                raise ValueError(f"Invalid CRUD methods in deleted_methods: {e}")

        delete_description = "Delete a"
        if self.delete_schema:
            delete_description = "Soft delete a"

        if ("create" in included_methods) and ("create" not in deleted_methods):
            self.router.add_api_route(
                self._get_endpoint_path(operation='create'),
                self._create_item(),
                methods=["POST"],
                include_in_schema=self.include_in_schema,
                tags=self.tags,
                dependencies=_inject_dependencies(create_deps),
                description=f"Create a new {self.model.__name__} row in the database.",
            )

        if ("read" in included_methods) and ("read" not in deleted_methods):
            self.router.add_api_route(
                self._get_endpoint_path(operation='read'),
                self._read_item(),
                methods=["GET"],
                include_in_schema=self.include_in_schema,
                tags=self.tags,
                dependencies=_inject_dependencies(read_deps),
                description=f"Read a single {self.model.__name__} row from the database by its primary keys: {self.primary_key_names}.",
            )

        if ("read_multi" in included_methods) and ("read_multi" not in deleted_methods):
            self.router.add_api_route(
                self._get_endpoint_path(operation='read_multi'),
                self._read_items(),
                methods=["GET"],
                include_in_schema=self.include_in_schema,
                tags=self.tags,
                dependencies=_inject_dependencies(read_multi_deps),
                description=f"Read multiple {self.model.__name__} rows from the database with a limit and an offset.",
            )

        if ("read_paginated" in included_methods) and (
            "read_paginated" not in deleted_methods
        ):
            self.router.add_api_route(
                self._get_endpoint_path(operation='read_paginated'),
                self._read_paginated(),
                methods=["GET"],
                include_in_schema=self.include_in_schema,
                tags=self.tags,
                dependencies=_inject_dependencies(read_paginated_deps),
                description=f"Read multiple {self.model.__name__} rows from the database with pagination.",
            )

        if ("update" in included_methods) and ("update" not in deleted_methods):
            self.router.add_api_route(
                self._get_endpoint_path(operation='update'),
                self._update_item(),
                methods=["PATCH"],
                include_in_schema=self.include_in_schema,
                tags=self.tags,
                dependencies=_inject_dependencies(update_deps),
                description=f"Update an existing {self.model.__name__} row in the database by its primary keys: {self.primary_key_names}.",
            )

        if ("delete" in included_methods) and ("delete" not in deleted_methods):
            path = self._get_endpoint_path(operation='delete')
            self.router.add_api_route(
                path,
                self._delete_item(),
                methods=["DELETE"],
                include_in_schema=self.include_in_schema,
                tags=self.tags,
                dependencies=_inject_dependencies(delete_deps),
                description=f"{delete_description} {self.model.__name__} row from the database by its primary keys: {self.primary_key_names}.",
            )

        if (
            ("db_delete" in included_methods)
            and ("db_delete" not in deleted_methods)
            and self.delete_schema
        ):
            self.router.add_api_route(
                self._get_endpoint_path(operation='db_delete'),
                self._db_delete(),
                methods=["DELETE"],
                include_in_schema=self.include_in_schema,
                tags=self.tags,
                dependencies=_inject_dependencies(db_delete_deps),
                description=f"Permanently delete a {self.model.__name__} row from the database by its primary keys: {self.primary_key_names}.",
            )

    def add_custom_route(
        self,
        endpoint: Callable,
        methods: Optional[Union[set[str], list[str]]],
        path: Optional[str] = None,
        dependencies: Optional[Sequence[Callable]] = None,
        include_in_schema: bool = True,
        tags: Optional[list[Union[str, Enum]]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        response_description: str = "Successful Response",
    ) -> None:
        """
        Adds a custom route to the FastAPI router.

        Args:
            path: URL path for the custom route.
            endpoint: The endpoint function to execute when the route is called.
            methods: A list of HTTP methods for the route (e.g., ['GET', 'POST']).
            dependencies: A list of functions to be injected as dependencies for the route.
            include_in_schema: Whether to include this route in the OpenAPI schema.
            tags: Tags for grouping and categorizing the route in documentation.
            summary: A short summary of the route, for documentation.
            description: A detailed description of the route, for documentation.
            response_description: A description of the response, for documentation.

        Example:
            ```python
            async def custom_endpoint(foo: int, bar: str):
                # custom logic here
                return {"foo": foo, "bar": bar}

            endpoint_creator.add_custom_route(
                endpoint=custom_endpoint,
                path="/custom",
                methods=["GET"],
                tags=["custom"],
                summary="Custom Endpoint",
                description="This is a custom endpoint."
            )
            ```
        """
        path = path or self.path
        full_path = f"{self.path}{path}"
        self.router.add_api_route(
            path=full_path,
            endpoint=endpoint,
            methods=methods,
            dependencies=_inject_dependencies(dependencies) or [],
            include_in_schema=include_in_schema,
            tags=tags or self.tags,
            summary=summary,
            description=description,
            response_description=response_description,
        )
