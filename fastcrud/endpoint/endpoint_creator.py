from typing import Type, TypeVar, Optional, Callable

from fastapi import Depends, Body, Query, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase
from pydantic import BaseModel, ValidationError

from ..exceptions.http_exceptions import NotFoundException
from ..crud.fast_crud import FastCRUD
from ..exceptions.http_exceptions import DuplicateValueException
from .helper import CRUDMethods, _get_primary_key, _extract_unique_columns

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
        crud: The CRUD base instance.
        create_schema: Pydantic schema for creating an item.
        update_schema: Pydantic schema for updating an item.
        delete_schema: Optional Pydantic schema for deleting an item.
        include_in_schema: Whether to include the created endpoints in the OpenAPI schema.
        path: Base path for the CRUD endpoints.
        tags: List of tags for grouping endpoints in the documentation.
        is_deleted_column: Optional column name to use for indicating a soft delete. Defaults to "is_deleted".
        deleted_at_column: Optional column name to use for storing the timestamp of a soft delete. Defaults to "deleted_at".

    Raises:
        ValueError: If both `included_methods` and `deleted_methods` are provided.

    Examples:
        Basic Setup:
        ```python
        from fastapi import FastAPI
        from fastcrud import EndpointCreator

        from myapp.models import MyModel
        from myapp.schemas import CreateMyModel, UpdateMyModel
        from myapp.crud import CRUDMyModel
        from myapp.database import async_session

        app = FastAPI()
        my_model_crud = CRUDMyModel(MyModel)
        endpoint_creator = EndpointCreator(
            session=async_session,
            model=MyModel,
            crud=my_model_crud,
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
    """

    def __init__(
        self,
        session: AsyncSession,
        model: DeclarativeBase,
        crud: FastCRUD,
        create_schema: Type[CreateSchemaType],
        update_schema: Type[UpdateSchemaType],
        include_in_schema: bool = True,
        delete_schema: Optional[Type[DeleteSchemaType]] = None,
        path: str = "",
        tags: Optional[list[str]] = None,
        is_deleted_column: str = "is_deleted",
        deleted_at_column: str = "deleted_at",
    ) -> None:
        self.primary_key_name = _get_primary_key(model)
        self.session = session
        self.crud = crud or FastCRUD(
            model=model,
            is_deleted_column=is_deleted_column,
            deleted_at_column=deleted_at_column,
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
                    if exists:
                        raise DuplicateValueException(
                            f"Value {value} is already registered"
                        )

            return await self.crud.create(db, item)

        return endpoint

    def _read_item(self):
        """Creates an endpoint for reading a single item from the database."""

        async def endpoint(id: int, db: AsyncSession = Depends(self.session)):
            item = await self.crud.get(db, id=id)
            if not item:
                raise NotFoundException(detail="Item not found")
            return item

        return endpoint

    def _read_items(self):
        """Creates an endpoint for reading multiple items from the database with optional pagination."""

        async def endpoint(
            db: AsyncSession = Depends(self.session),
            offset: int = Query(0),
            limit: int = Query(100),
        ):
            return await self.crud.get_multi(db, offset=offset, limit=limit)

        return endpoint

    def _update_item(self):
        """Creates an endpoint for updating an existing item in the database."""

        async def endpoint(
            id: int,
            item: self.update_schema = Body(...),  # type: ignore
            db: AsyncSession = Depends(self.session),
        ):
            return await self.crud.update(db, item, id=id)

        return endpoint

    def _delete_item(self):
        """Creates an endpoint for deleting an item from the database."""

        async def endpoint(id: int, db: AsyncSession = Depends(self.session)):
            await self.crud.delete(db, id=id)
            return {"message": "Item deleted successfully"}

        return endpoint

    def _db_delete(self):
        """
        Creates an endpoint for hard deleting an item from the database.

        This endpoint is only added if the delete_schema is provided during initialization.
        The endpoint expects an item ID as a path parameter and uses the provided SQLAlchemy
        async session to permanently delete the item from the database.
        """

        async def endpoint(id: int, db: AsyncSession = Depends(self.session)):
            await self.crud.db_delete(db, id=id)
            return {"message": "Item permanently deleted from the database"}

        return endpoint

    def add_routes_to_router(
        self,
        create_deps: list[Callable] = [],
        read_deps: list[Callable] = [],
        read_multi_deps: list[Callable] = [],
        update_deps: list[Callable] = [],
        delete_deps: list[Callable] = [],
        db_delete_deps: list[Callable] = [],
        included_methods: Optional[list[str]] = None,
        deleted_methods: Optional[list[str]] = None,
    ):
        """
        Adds CRUD operation routes to the FastAPI router with specified dependencies for each type of operation.

        This method registers routes for create, read, update, and delete operations with the FastAPI router,
        allowing for custom dependency injection for each type of operation.

        Args:
            create_deps: List of dependency injection functions for the create endpoint.
            read_deps: List of dependency injection functions for the read endpoint.
            read_multi_deps: List of dependency injection functions for the read multiple items endpoint.
            update_deps: List of dependency injection functions for the update endpoint.
            delete_deps: List of dependency injection functions for the delete endpoint.
            db_delete_deps: List of dependency injection functions for the hard delete endpoint.
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
                f"{self.path}/create",
                self._create_item(),
                methods=["POST"],
                include_in_schema=self.include_in_schema,
                tags=self.tags,
                dependencies=create_deps,
                description=f"Create a new {self.model.__name__} row in the database.",
            )

        if ("read" in included_methods) and ("read" not in deleted_methods):
            self.router.add_api_route(
                f"{self.path}/get/{{{self.primary_key_name}}}",
                self._read_item(),
                methods=["GET"],
                include_in_schema=self.include_in_schema,
                tags=self.tags,
                dependencies=read_deps,
                description=f"Read a single {self.model.__name__} row from the database by its primary key: {self.primary_key_name}.",
            )

        if ("read_multi" in included_methods) and ("read_multi" not in deleted_methods):
            self.router.add_api_route(
                f"{self.path}/get_multi",
                self._read_items(),
                methods=["GET"],
                include_in_schema=self.include_in_schema,
                tags=self.tags,
                dependencies=read_multi_deps,
                description=f"Read multiple {self.model.__name__} rows from the database with optional pagination.",
            )

        if ("update" in included_methods) and ("update" not in deleted_methods):
            self.router.add_api_route(
                f"{self.path}/update/{{{self.primary_key_name}}}",
                self._update_item(),
                methods=["PATCH"],
                include_in_schema=self.include_in_schema,
                tags=self.tags,
                dependencies=update_deps,
                description=f"Update an existing {self.model.__name__} row in the database by its primary key: {self.primary_key_name}.",
            )

        if ("delete" in included_methods) and ("delete" not in deleted_methods):
            self.router.add_api_route(
                f"{self.path}/delete/{{{self.primary_key_name}}}",
                self._delete_item(),
                methods=["DELETE"],
                include_in_schema=self.include_in_schema,
                tags=self.tags,
                dependencies=delete_deps,
                description=f"{delete_description} {self.model.__name__} row from the database by its primary key: {self.primary_key_name}.",
            )

        if (
            ("db_delete" in included_methods)
            and ("db_delete" not in deleted_methods)
            and self.delete_schema
        ):
            self.router.add_api_route(
                f"{self.path}/db_delete/{{{self.primary_key_name}}}",
                self._db_delete(),
                methods=["DELETE"],
                include_in_schema=self.include_in_schema,
                tags=self.tags,
                dependencies=db_delete_deps,
                description=f"Permanently delete a {self.model.__name__} row from the database by its primary key: {self.primary_key_name}.",
            )

    def add_custom_route(
        self,
        endpoint: Callable,
        methods: list[str],
        path: Optional[str] = None,
        dependencies: Optional[list[Callable]] = None,
        include_in_schema: bool = True,
        tags: Optional[list[str]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        response_description: Optional[str] = None,
    ) -> None:
        """
        Adds a custom route to the FastAPI router.

        Args:
            path: URL path for the custom route.
            endpoint: The endpoint function to execute when the route is called.
            methods: A list of HTTP methods for the route (e.g., ['GET', 'POST']).
            dependencies: A list of dependency injection functions for the route.
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
            dependencies=dependencies or [],
            include_in_schema=include_in_schema,
            tags=tags or self.tags,
            summary=summary,
            description=description,
            response_description=response_description,
        )
