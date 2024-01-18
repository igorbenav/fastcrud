from typing import Type, TypeVar, Optional, Callable

from fastapi import Depends, Body, Query, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase
from pydantic import BaseModel

from ..exceptions.http_exceptions import NotFoundException
from ..crud.fast_crud import FastCRUD
from ..exceptions.http_exceptions import DuplicateValueException
from .helper import _get_primary_key, _extract_unique_columns

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
    This method assumes 'id' is the primary key for path parameters.

    Attributes:
        session: The SQLAlchemy async session.
        model: The SQLAlchemy model.
        crud: The CRUD base instance.
        create_schema: Pydantic schema for creating an item.
        update_schema: Pydantic schema for updating an item.
        delete_schema: Optional Pydantic schema for deleting an item.
        include_in_schema (bool): Whether to include the created endpoints in the OpenAPI schema.
        path: Base path for the CRUD endpoints.
        tags: List of tags for grouping endpoints in the documentation.

    Usage Examples:
        Example 1 - Basic Setup:
            from fastapi import FastAPI
            from myapp.models import MyModel
            from myapp.schemas import CreateMyModel, UpdateMyModel
            from myapp.crud import CRUDMyModel
            from myapp.database import async_session
            from myapp.api import EndpointCreator

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

        Example 2 - With Custom Dependencies:
            from fastapi.security import OAuth2PasswordBearer

            oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

            def get_current_user(token: str = Depends(oauth2_scheme)):
                # Implement user retrieval
                return ...

            endpoint_creator.add_routes_to_router(
                read_deps=[get_current_user],
                update_deps=[get_current_user]
            )

        Example 3 - Integrating with Multiple Models:
            # Assuming definitions for OtherModel, CRUDOtherModel, CreateOtherModel, UpdateOtherModel

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
    ) -> None:
        self.primary_key_name = _get_primary_key(model)
        self.session = session
        self.crud = crud
        self.model = model
        self.create_schema = create_schema
        self.update_schema = update_schema
        self.delete_schema = delete_schema
        self.include_in_schema = include_in_schema
        self.path = path
        self.tags = tags or []
        self.router = APIRouter()

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

        The dependencies are callables that FastAPI can use to inject dependencies into the path operation functions.

        Usage Examples:
            Example 1 - Basic Setup Without Additional Dependencies:
                endpoint_creator = EndpointCreator(...)
                endpoint_creator.add_routes_to_router()

            Example 2 - With Custom Dependencies for Authentication:
                from fastapi.security import OAuth2PasswordBearer

                oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

                def get_current_user(token: str = Depends(oauth2_scheme)):
                    # Implement user retrieval logic
                    return ...

                endpoint_creator.add_routes_to_router(
                    create_deps=[get_current_user],
                    read_deps=[get_current_user],
                    update_deps=[get_current_user],
                    delete_deps=[get_current_user]
                )

            Example 3 - Different Dependencies for Different Endpoints:
                def validate_admin_user(...):
                    # Admin validation logic
                    ...

                endpoint_creator.add_routes_to_router(
                    create_deps=[get_current_user, validate_admin_user],
                    read_multi_deps=[get_current_user],
                    update_deps=[get_current_user, validate_admin_user],
                    delete_deps=[get_current_user, validate_admin_user]
                )

        Note:
            This method should be called to register the endpoints with the FastAPI application.
            If 'delete_schema' is provided, a hard delete endpoint is also registered.
            This method assumes 'id' is the primary key for path parameters.
        """
        self.router.add_api_route(
            f"{self.path}/create",
            self._create_item(),
            methods=["POST"],
            include_in_schema=self.include_in_schema,
            tags=self.tags,
            dependencies=create_deps,
        )
        self.router.add_api_route(
            f"{self.path}/get/{{{self.primary_key_name}}}",
            self._read_item(),
            methods=["GET"],
            include_in_schema=self.include_in_schema,
            tags=self.tags,
            dependencies=read_deps,
        )
        self.router.add_api_route(
            f"{self.path}/get_multi",
            self._read_items(),
            methods=["GET"],
            include_in_schema=self.include_in_schema,
            tags=self.tags,
            dependencies=read_multi_deps,
        )
        self.router.add_api_route(
            f"{self.path}/update/{{{self.primary_key_name}}}",
            self._update_item(),
            methods=["PATCH"],
            include_in_schema=self.include_in_schema,
            tags=self.tags,
            dependencies=update_deps,
        )
        self.router.add_api_route(
            f"{self.path}/delete/{{{self.primary_key_name}}}",
            self._delete_item(),
            methods=["DELETE"],
            include_in_schema=self.include_in_schema,
            tags=self.tags,
            dependencies=delete_deps,
        )

        if self.delete_schema:
            self.router.add_api_route(
                f"{self.path}/db_delete/{{{self.primary_key_name}}}",
                self._db_delete(),
                methods=["DELETE"],
                include_in_schema=self.include_in_schema,
                tags=self.tags,
                dependencies=db_delete_deps,
            )
