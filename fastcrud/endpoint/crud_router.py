from typing import Type, TypeVar, Optional, Callable, List
from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase
from pydantic import BaseModel
from .endpoint_creator import EndpointCreator
from ..crud.fast_crud import FastCRUD

CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
DeleteSchemaType = TypeVar("DeleteSchemaType", bound=BaseModel)


def crud_router(
    session: AsyncSession,
    model: DeclarativeBase,
    crud: FastCRUD,
    create_schema: Type[CreateSchemaType],
    update_schema: Type[UpdateSchemaType],
    delete_schema: Optional[Type[DeleteSchemaType]] = None,
    path: str = "",
    tags: Optional[List[str]] = None,
    create_deps: List[Callable] = [],
    read_deps: List[Callable] = [],
    read_multi_deps: List[Callable] = [],
    update_deps: List[Callable] = [],
    delete_deps: List[Callable] = [],
    db_delete_deps: List[Callable] = [],
) -> APIRouter:
    """
    Creates and configures a FastAPI router with CRUD endpoints for a given model.

    Args:
        session: The SQLAlchemy async session.
        model: The SQLAlchemy model.
        crud: The FastCRUD instance.
        create_schema: Pydantic schema for creating an item.
        update_schema: Pydantic schema for updating an item.
        delete_schema: Optional Pydantic schema for deleting an item.
        path: Base path for the CRUD endpoints.
        tags: Optional list of tags for grouping endpoints in the documentation.
        create_deps: Optional list of dependency injection functions for the create endpoint.
        read_deps: Optional list of dependency injection functions for the read endpoint.
        read_multi_deps: Optional list of dependency injection functions for the read multiple items endpoint.
        update_deps: Optional list of dependency injection functions for the update endpoint.
        delete_deps: Optional list of dependency injection functions for the delete endpoint.
        db_delete_deps: Optional list of dependency injection functions for the hard delete endpoint.

    Returns:
        An APIRouter object with configured CRUD endpoints.

    Examples:
        Basic Setup:
        ```python
        router = crud_router(
            session=async_session,
            model=MyModel,
            crud=CRUDMyModel(MyModel),
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
            crud=CRUDUserModel(UserModel),
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
            crud=CRUDProductModel(ProductModel),
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
    """
    endpoint_creator = EndpointCreator(
        session=session,
        model=model,
        crud=crud,
        create_schema=create_schema,
        update_schema=update_schema,
        delete_schema=delete_schema,
        path=path,
        tags=tags,
    )

    endpoint_creator.add_routes_to_router(
        create_deps=create_deps,
        read_deps=read_deps,
        read_multi_deps=read_multi_deps,
        update_deps=update_deps,
        delete_deps=delete_deps,
        db_delete_deps=db_delete_deps,
    )

    return endpoint_creator.router
