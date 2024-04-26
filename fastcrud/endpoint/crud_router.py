from typing import Type, TypeVar, Optional, Union, Sequence, Callable
from enum import Enum

from fastapi import APIRouter, params
from sqlalchemy.orm import DeclarativeBase
from pydantic import BaseModel

from .endpoint_creator import EndpointCreator
from ..crud.fast_crud import FastCRUD

CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
DeleteSchemaType = TypeVar("DeleteSchemaType", bound=BaseModel)


def crud_router(
    session: Callable,
    model: type[DeclarativeBase],
    create_schema: Type[CreateSchemaType],
    update_schema: Type[UpdateSchemaType],
    crud: Optional[FastCRUD] = None,
    delete_schema: Optional[Type[DeleteSchemaType]] = None,
    path: str = "",
    tags: Optional[list[Union[str, Enum]]] = None,
    include_in_schema: bool = True,
    create_deps: Sequence[params.Depends] = [],
    read_deps: Sequence[params.Depends] = [],
    read_multi_deps: Sequence[params.Depends] = [],
    read_paginated_deps: Sequence[params.Depends] = [],
    update_deps: Sequence[params.Depends] = [],
    delete_deps: Sequence[params.Depends] = [],
    db_delete_deps: Sequence[params.Depends] = [],
    included_methods: Optional[list[str]] = None,
    deleted_methods: Optional[list[str]] = None,
    endpoint_creator: Optional[Type[EndpointCreator]] = None,
    is_deleted_column: str = "is_deleted",
    deleted_at_column: str = "deleted_at",
    updated_at_column: str = "updated_at",
    endpoint_names: Optional[dict[str, str]] = None,
    allow_limit_0: bool = False,
) -> APIRouter:
    """
    Creates and configures a FastAPI router with CRUD endpoints for a given model.

    This utility function streamlines the process of setting up a router for CRUD operations,
    using a custom `EndpointCreator` if provided, and managing dependency injections as well
    as selective method inclusions or exclusions.

    Args:
        session: The SQLAlchemy async session.
        model: The SQLAlchemy model.
        crud: An optional FastCRUD instance. If not provided, uses FastCRUD(model).
        create_schema: Pydantic schema for creating an item.
        update_schema: Pydantic schema for updating an item.
        delete_schema: Optional Pydantic schema for deleting an item.
        path: Base path for the CRUD endpoints.
        tags: Optional list of tags for grouping endpoints in the documentation.
        include_in_schema: Whether to include the created endpoints in the OpenAPI schema.
        create_deps: Optional list of dependency injection functions for the create endpoint.
        read_deps: Optional list of dependency injection functions for the read endpoint.
        read_multi_deps: Optional list of dependency injection functions for the read multiple items endpoint.
        update_deps: Optional list of dependency injection functions for the update endpoint.
        delete_deps: Optional list of dependency injection functions for the delete endpoint.
        db_delete_deps: Optional list of dependency injection functions for the hard delete endpoint.
        included_methods: Optional list of CRUD methods to include. If None, all methods are included.
        deleted_methods: Optional list of CRUD methods to exclude.
        endpoint_creator: Optional custom class derived from EndpointCreator for advanced customization.
        is_deleted_column: Optional column name to use for indicating a soft delete. Defaults to "is_deleted".
        deleted_at_column: Optional column name to use for storing the timestamp of a soft delete. Defaults to "deleted_at".
        updated_at_column: Optional column name to use for storing the timestamp of an update. Defaults to "updated_at".
        endpoint_names: Optional dictionary to customize endpoint names for CRUD operations. Keys are operation types
                        ("create", "read", "update", "delete", "db_delete", "read_multi", "read_paginated"), and
                        values are the custom names to use. Unspecified operations will use default names.
        allow_limit_0: Whether multi-get endpoints allow 0 as a limit parameter, fetching all rows. Public APIs should probably keep this set to False, which will cause a ValueError to be raised if someone tries it.

    Returns:
        Configured APIRouter instance with the CRUD endpoints.

    Raises:
        ValueError: If both 'included_methods' and 'deleted_methods' are provided.

    Examples:
        Basic Setup:
        ```python
        router = crud_router(
            session=async_session,
            model=MyModel,
            create_schema=CreateMyModelSchema,
            update_schema=UpdateMyModelSchema,
            path="/mymodel",
            tags=["MyModel"]
        )
        ```

        With Custom Dependencies:
        ```python
        def get_current_user(token: str = Depends(oauth2_scheme)):
            # Implement user retrieval logic
            return ...

        router = crud_router(
            session=async_session,
            model=UserModel,
            create_schema=CreateUserSchema,
            update_schema=UpdateUserSchema,
            read_deps=[get_current_user],
            update_deps=[get_current_user],
            path="/users",
            tags=["Users"]
        )
        ```

        Adding Delete Endpoints:
        ```python
        router = crud_router(
            session=async_session,
            model=ProductModel,
            create_schema=CreateProductSchema,
            update_schema=UpdateProductSchema,
            delete_schema=DeleteProductSchema,
            path="/products",
            tags=["Products"]
        )
        ```

        Customizing Path and Tags:
        ```python
        router = crud_router(
            session=async_session,
            model=OrderModel,
            crud=CRUDOrderModel(OrderModel),
            create_schema=CreateOrderSchema,
            update_schema=UpdateOrderSchema,
            path="/orders",
            tags=["Orders", "Sales"]
        )
        ```

        Integrating Multiple Models:
        ```python
        product_router = crud_router(
            session=async_session,
            model=ProductModel,
            crud=CRUDProductModel(ProductModel),
            create_schema=CreateProductSchema,
            update_schema=UpdateProductSchema,
            path="/products",
            tags=["Inventory"]
        )

        customer_router = crud_router(
            session=async_session,
            model=CustomerModel,
            crud=CRUDCustomerModel(CustomerModel),
            create_schema=CreateCustomerSchema,
            update_schema=UpdateCustomerSchema,
            path="/customers",
            tags=["CRM"]
        )
        ```

        With Selective CRUD Methods:
        ```python
        # Only include 'create' and 'read' methods
        router = crud_router(
            session=async_session,
            model=MyModel,
            crud=CRUDMyModel(MyModel),
            create_schema=CreateMyModel,
            update_schema=UpdateMyModel,
            included_methods=["create", "read"],
            path="/mymodel",
            tags=["MyModel"]
        )
        ```

        Using a Custom EndpointCreator:
        ```python
        class CustomEndpointCreator(EndpointCreator):
            def _custom_route(self):
                async def custom_endpoint():
                    # Custom endpoint logic
                    return {"message": "Custom route"}

                return custom_endpoint

                async def add_routes_to_router(self, ...):
                    # First, add standard CRUD routes
                    super().add_routes_to_router(...)

                    # Now, add custom routes
                    self.router.add_api_route(
                        path="/custom",
                        endpoint=self._custom_route(),
                        methods=["GET"],
                        tags=self.tags,
                        # Other parameters as needed
                    )

        router = crud_router(
            session=async_session,
            model=MyModel,
            crud=CRUDMyModel(MyModel),
            create_schema=CreateMyModel,
            update_schema=UpdateMyModel,
            endpoint_creator=CustomEndpointCreator,
            path="/mymodel",
            tags=["MyModel"]
        )

        app.include_router(my_router)
        ```

        Customizing Endpoint Names:
        ```python
        router = crud_router(
            session=async_session,
            model=TaskModel,
            create_schema=CreateTaskSchema,
            update_schema=UpdateTaskSchema,
            path="/tasks",
            tags=["Task Management"],
            endpoint_names={
                "create": "add_task",
                "read": "get_task",
                "update": "modify_task",
                "delete": "remove_task",
                "db_delete": "permanently_remove_task",
                "read_multi": "list_tasks",
                "read_paginated": "paginate_tasks"
            }
        )
        ```
    """
    crud = crud or FastCRUD(
        model=model,
        is_deleted_column=is_deleted_column,
        deleted_at_column=deleted_at_column,
        updated_at_column=updated_at_column,
    )

    endpoint_creator_class = endpoint_creator or EndpointCreator
    endpoint_creator_instance = endpoint_creator_class(
        session=session,
        model=model,
        crud=crud,
        create_schema=create_schema,
        update_schema=update_schema,
        include_in_schema=include_in_schema,
        delete_schema=delete_schema,
        path=path,
        tags=tags,
        is_deleted_column=is_deleted_column,
        deleted_at_column=deleted_at_column,
        updated_at_column=updated_at_column,
        endpoint_names=endpoint_names,
        allow_limit_0=allow_limit_0,
    )

    endpoint_creator_instance.add_routes_to_router(
        create_deps=create_deps,
        read_deps=read_deps,
        read_multi_deps=read_multi_deps,
        read_paginated_deps=read_paginated_deps,
        update_deps=update_deps,
        delete_deps=delete_deps,
        db_delete_deps=db_delete_deps,
        included_methods=included_methods,
        deleted_methods=deleted_methods,
    )

    return endpoint_creator_instance.router
