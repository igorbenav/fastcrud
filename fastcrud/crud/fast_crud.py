from typing import Any, Generic, TypeVar, Union, Optional
from datetime import datetime, timezone

from pydantic import BaseModel, ValidationError
import sqlalchemy.sql.selectable
from sqlalchemy import select, update, delete, func, and_, inspect, asc, desc, true
from sqlalchemy.exc import ArgumentError
from sqlalchemy.sql import Join
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine.row import Row
from sqlalchemy.orm import DeclarativeBase

from .helper import (
    _extract_matching_columns_from_schema,
    _extract_matching_columns_from_kwargs,
    _auto_detect_join_condition,
    _add_column_with_prefix,
)

ModelType = TypeVar("ModelType", bound=DeclarativeBase)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
UpdateSchemaInternalType = TypeVar("UpdateSchemaInternalType", bound=BaseModel)
DeleteSchemaType = TypeVar("DeleteSchemaType", bound=BaseModel)


class FastCRUD(
    Generic[
        ModelType,
        CreateSchemaType,
        UpdateSchemaType,
        UpdateSchemaInternalType,
        DeleteSchemaType,
    ]
):
    """
    Base class for CRUD operations on a model.

    This class provides a set of methods for create, read, update, and delete operations on a given SQLAlchemy model,
    utilizing Pydantic schemas for data validation and serialization.

    Args:
        model: The SQLAlchemy model type.

    Methods:
        create(db: AsyncSession, object: CreateSchemaType) -> ModelType:
            Creates a new record in the database. The 'object' parameter is a Pydantic schema
            containing the data to be saved.

        get(db: AsyncSession, schema_to_select: Optional[Union[type[BaseModel], list]] = None, **kwargs: Any) -> Optional[dict]:
            Retrieves a single record based on filters. You can specify a Pydantic schema to
            select specific columns, and pass filter conditions as keyword arguments.

        exists(db: AsyncSession, **kwargs: Any) -> bool:
            Checks if a record exists based on the provided filters. Returns True if the record
            exists, False otherwise.

        count(db: AsyncSession, **kwargs: Any) -> int:
            Counts the number of records matching the provided filters. Useful for pagination
            and analytics.

        get_multi(db: AsyncSession, offset: int = 0, limit: int = 100, schema_to_select: Optional[type[BaseModel]] = None, sort_columns: Optional[Union[str, list[str]]] = None, sort_orders: Optional[Union[str, list[str]]] = None, return_as_model: bool = False, **kwargs: Any) -> dict[str, Any]:
            Fetches multiple records with optional sorting, pagination, and model conversion.
            Filters, sorting, and pagination parameters can be provided.

        get_joined(db: AsyncSession, join_model: type[ModelType], join_prefix: Optional[str] = None, join_on: Optional[Union[Join, None]] = None, schema_to_select: Optional[Union[type[BaseModel], list]] = None, join_schema_to_select: Optional[Union[type[BaseModel], list]] = None, join_type: str = "left", **kwargs: Any) -> Optional[dict[str, Any]]:
            Performs a join operation with another model. Supports custom join conditions and
            selection of specific columns using Pydantic schemas.

        get_multi_joined(db: AsyncSession, join_model: type[ModelType], join_prefix: Optional[str] = None, join_on: Optional[Join] = None, schema_to_select: Optional[type[BaseModel]] = None, join_schema_to_select: Optional[type[BaseModel]] = None, join_type: str = "left", offset: int = 0, limit: int = 100, sort_columns: Optional[Union[str, list[str]]] = None, sort_orders: Optional[Union[str, list[str]]] = None, return_as_model: bool = False, **kwargs: Any) -> dict[str, Any]:
            Similar to 'get_joined', but for fetching multiple records. Offers pagination and
            sorting functionalities for the joined tables.

        get_multi_by_cursor(db: AsyncSession, cursor: Any = None, limit: int = 100, schema_to_select: Optional[type[BaseModel]] = None, sort_column: str = "id", sort_order: str = "asc", **kwargs: Any) -> dict[str, Any]:
            Implements cursor-based pagination for fetching records. Useful for large datasets
            and infinite scrolling features.

        update(db: AsyncSession, object: Union[UpdateSchemaType, dict[str, Any]], **kwargs: Any) -> None:
            Updates an existing record. The 'object' can be a Pydantic schema or dictionary
            containing update data.

        db_delete(db: AsyncSession, **kwargs: Any) -> None:
            Hard deletes a record from the database based on provided filters.

        delete(db: AsyncSession, db_row: Optional[Row] = None, **kwargs: Any) -> None:
            Soft deletes a record if it has an "is_deleted" attribute; otherwise, performs a
            hard delete. Filters or an existing database row can be provided for deletion.

    Examples:
        Example 1: Basic Usage
        ----------------------
        Create a FastCRUD instance for a User model and perform basic CRUD operations.
        ```python
        user_crud = FastCRUD(User, UserCreateSchema, UserUpdateSchema)
        async with db_session() as db:
            # Create a new user
            new_user = await user_crud.create(db, UserCreateSchema(name="Alice"))
            # Read a user
            user = await user_crud.get(db, id=new_user.id)
            # Update a user
            await user_crud.update(db, UserUpdateSchema(email="alice@example.com"), id=new_user.id)
            # Delete a user
            await user_crud.delete(db, id=new_user.id)
        ```

        Example 2: Advanced Filtering and Pagination
        --------------------------------------------
        Use advanced filtering, sorting, and pagination for fetching records.
        ```python
        product_crud = FastCRUD(Product, ProductCreateSchema)
        async with db_session() as db:
            products = await product_crud.get_multi(
                db, offset=0, limit=10, sort_columns=['price'], sort_orders=['asc']
            )
        ```

        Example 3: Join Operations with Custom Schemas
        ----------------------------------------------
        Perform join operations between two models using custom schemas for selection.
        ```python
        order_crud = FastCRUD(Order, OrderCreateSchema, join_model=Product)
        async with db_session() as db:
            orders = await order_crud.get_multi_joined(
                db, offset=0, limit=5, schema_to_select=OrderReadSchema, join_schema_to_select=ProductReadSchema
            )
        ```

        Example 4: Cursor Pagination
        ----------------------------
        Implement cursor-based pagination for efficient data retrieval in large datasets.
        ```python
        comment_crud = FastCRUD(Comment, CommentCreateSchema)
        async with db_session() as db:
            first_page = await comment_crud.get_multi_by_cursor(db, limit=10)
            next_cursor = first_page['next_cursor']
            second_page = await comment_crud.get_multi_by_cursor(db, cursor=next_cursor, limit=10)
        ```

        Example 5: Dynamic Filtering and Counting
        -----------------------------------------
        Dynamically filter records based on various criteria and count the results.
        ```python
        task_crud = FastCRUD(Task, TaskCreateSchema)
        async with db_session() as db:
            completed_tasks = await task_crud.get_multi(db, status='completed')
            high_priority_task_count = await task_crud.count(db, priority='high')
        ```
    """

    def __init__(self, model: type[ModelType]) -> None:
        self.model = model

    def _apply_sorting(
        self,
        stmt: sqlalchemy.sql.selectable.Select,
        sort_columns: Union[str, list[str]],
        sort_orders: Optional[Union[str, list[str]]] = None,
    ) -> sqlalchemy.sql.selectable.Select:
        """
        Apply sorting to a SQLAlchemy query based on specified column names and sort orders.

        Args:
            stmt: The SQLAlchemy Select statement to which sorting will be applied.
            sort_columns: A single column name or a list of column names on which to apply sorting.
            sort_orders: A single sort order ('asc' or 'desc') or a list of sort orders corresponding
                to the columns in sort_columns. If not provided, defaults to 'asc' for each column.

        Raises:
            ValueError: Raised if sort orders are provided without corresponding sort columns,
                or if an invalid sort order is provided (not 'asc' or 'desc').
            ArgumentError: Raised if an invalid column name is provided that does not exist in the model.

        Returns:
            The modified Select statement with sorting applied.

        Examples:
            Applying ascending sort on a single column:
            >>> stmt = _apply_sorting(stmt, 'name')

            Applying descending sort on a single column:
            >>> stmt = _apply_sorting(stmt, 'age', 'desc')

            Applying mixed sort orders on multiple columns:
            >>> stmt = _apply_sorting(stmt, ['name', 'age'], ['asc', 'desc'])

            Applying ascending sort on multiple columns:
            >>> stmt = _apply_sorting(stmt, ['name', 'age'])

        Note:
            This method modifies the passed Select statement in-place by applying the order_by clause
            based on the provided column names and sort orders.
        """
        if sort_orders and not sort_columns:
            raise ValueError("Sort orders provided without corresponding sort columns.")

        if sort_columns:
            if not isinstance(sort_columns, list):
                sort_columns = [sort_columns]

            if sort_orders:
                if not isinstance(sort_orders, list):
                    sort_orders = [sort_orders] * len(sort_columns)
                if len(sort_columns) != len(sort_orders):
                    raise ValueError(
                        "The length of sort_columns and sort_orders must match."
                    )

                for idx, order in enumerate(sort_orders):
                    if order not in ["asc", "desc"]:
                        raise ValueError(
                            f"Invalid sort order: {order}. Only 'asc' or 'desc' are allowed."
                        )

            validated_sort_orders = (
                ["asc"] * len(sort_columns) if not sort_orders else sort_orders
            )

            for idx, column_name in enumerate(sort_columns):
                column = getattr(self.model, column_name, None)
                if not column:
                    raise ArgumentError(f"Invalid column name: {column_name}")

                order = validated_sort_orders[idx]
                stmt = stmt.order_by(asc(column) if order == "asc" else desc(column))

        return stmt

    async def create(self, db: AsyncSession, object: CreateSchemaType) -> ModelType:
        """
        Create a new record in the database.

        Args:
            db: The SQLAlchemy async session.
            object: The Pydantic schema containing the data to be saved.

        Returns:
            The created database object.
        """
        object_dict = object.model_dump()
        db_object: ModelType = self.model(**object_dict)
        db.add(db_object)
        await db.commit()
        return db_object

    async def get(
        self,
        db: AsyncSession,
        schema_to_select: Optional[type[BaseModel]] = None,
        **kwargs: Any,
    ) -> Optional[dict]:
        """
        Fetch a single record based on filters.

        Args:
            db: The SQLAlchemy async session.
            schema_to_select: Pydantic schema for selecting specific columns.
                Default is None to select all columns.
            **kwargs: Filters to apply to the query.

        Returns:
            The fetched database row or None if not found.
        """
        to_select = _extract_matching_columns_from_schema(
            model=self.model, schema=schema_to_select
        )
        stmt = select(*to_select).filter_by(**kwargs)

        db_row = await db.execute(stmt)
        result: Row = db_row.first()
        if result is not None:
            out: dict = dict(result._mapping)
            return out

        return None

    async def exists(self, db: AsyncSession, **kwargs: Any) -> bool:
        """
        Check if a record exists based on filters.

        Args:
            db: The SQLAlchemy async session.
            **kwargs: Filters to apply to the query.

        Returns:
            True if a record exists, False otherwise.
        """
        to_select = _extract_matching_columns_from_kwargs(
            model=self.model, kwargs=kwargs
        )
        stmt = select(*to_select).filter_by(**kwargs).limit(1)

        result = await db.execute(stmt)
        return result.first() is not None

    async def count(self, db: AsyncSession, **kwargs: Any) -> int:
        """
        Count the records based on filters.

        Args:
            db: The SQLAlchemy async session.
            **kwargs: Filters to apply to the query.

        Returns:
            Total count of records that match the applied filters.

        Note:
            This method provides a quick way to get the count of records without retrieving the actual data.
        """
        conditions = [
            getattr(self.model, key) == value for key, value in kwargs.items()
        ]
        if conditions:
            combined_conditions = and_(*conditions)
        else:
            combined_conditions = true()

        count_query = (
            select(func.count()).select_from(self.model).where(combined_conditions)
        )
        total_count: int = await db.scalar(count_query)

        return total_count

    async def get_multi(
        self,
        db: AsyncSession,
        offset: int = 0,
        limit: int = 100,
        schema_to_select: Optional[type[BaseModel]] = None,
        sort_columns: Optional[Union[str, list[str]]] = None,
        sort_orders: Optional[Union[str, list[str]]] = None,
        return_as_model: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Fetch multiple records based on filters, with optional sorting, pagination, and model conversion.

        Args:
            db: The SQLAlchemy async session.
            offset: Number of rows to skip before fetching. Must be non-negative.
            limit: Maximum number of rows to fetch. Must be non-negative.
            schema_to_select: Pydantic schema for selecting specific columns.
            sort_columns: Single column name or a list of column names for sorting.
            sort_orders: Single sort direction ('asc' or 'desc') or a list of directions corresponding to the columns in sort_columns. Defaults to 'asc'.
            return_as_model: If True, returns the data as instances of the Pydantic model.
            **kwargs: Filters to apply to the query.

        Returns:
            A dictionary containing the fetched rows under 'data' key and total count under 'total_count'.

        Raises:
            ValueError: If limit or offset is negative, or if schema_to_select is required but not provided or invalid.

        Examples:
            Fetch the first 10 users:
            ```python
            users = await crud.get_multi(db, 0, 10)
            ```

            Fetch next 10 users with sorting:
            ```python
            users = await crud.get_multi(db, 10, 10, sort_columns='username', sort_orders='desc')
            ```

            Fetch users with filtering and multiple column sorting:
            ```python
            users = await crud.get_multi(db, 0, 10, is_active=True, sort_columns=['username', 'email'], sort_orders=['asc', 'desc'])
            ```
        """
        if limit < 0 or offset < 0:
            raise ValueError("Limit and offset must be non-negative.")

        to_select = _extract_matching_columns_from_schema(self.model, schema_to_select)
        stmt = select(*to_select).filter_by(**kwargs)

        if sort_columns:
            stmt = self._apply_sorting(stmt, sort_columns, sort_orders)

        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        data = [dict(row) for row in result.mappings()]

        if return_as_model:
            if not schema_to_select:
                raise ValueError(
                    "schema_to_select must be provided when return_as_model is True."
                )
            try:
                data = [schema_to_select.model_construct(**row) for row in data]
            except ValidationError as e:
                raise ValueError(
                    f"Data validation error for schema {schema_to_select.__name__}: {e}"
                )

        total_count = await self.count(db=db, **kwargs)
        return {"data": data, "total_count": total_count}

    async def get_joined(
        self,
        db: AsyncSession,
        join_model: type[ModelType],
        join_prefix: Optional[str] = None,
        join_on: Optional[Union[Join, None]] = None,
        schema_to_select: Optional[type[BaseModel]] = None,
        join_schema_to_select: Optional[type[BaseModel]] = None,
        join_type: str = "left",
        **kwargs: Any,
    ) -> Optional[dict[str, Any]]:
        """
        Fetches a single record with a join on another model. If 'join_on' is not provided, the method attempts
        to automatically detect the join condition using foreign key relationships.

        Args:
            db: The SQLAlchemy async session.
            join_model: The model to join with.
            join_prefix: Optional prefix to be added to all columns of the joined model. If None, no prefix is added.
            join_on: SQLAlchemy Join object for specifying the ON clause of the join. If None, the join condition is
                auto-detected based on foreign keys.
            schema_to_select: Pydantic schema for selecting specific columns from the primary model.
            join_schema_to_select: Pydantic schema for selecting specific columns from the joined model.
            join_type: Specifies the type of join operation to perform. Can be "left" for a left outer join or "inner" for an inner join.
            **kwargs: Filters to apply to the query.

        Returns:
            The fetched database row or None if not found.

        Examples:
            Simple example: Joining User and Tier models without explicitly providing join_on
            ```python
            result = await crud_user.get_joined(
                db=session,
                join_model=Tier,
                schema_to_select=UserSchema,
                join_schema_to_select=TierSchema
            )
            ```

            Complex example: Joining with a custom join condition, additional filter parameters, and a prefix
            ```python
            from sqlalchemy import and_
            result = await crud_user.get_joined(
                db=session,
                join_model=Tier,
                join_prefix="tier_",
                join_on=and_(User.tier_id == Tier.id, User.is_superuser == True),
                schema_to_select=UserSchema,
                join_schema_to_select=TierSchema,
                username="john_doe"
            )
            ```

            Return example: prefix added, no schema_to_select or join_schema_to_select
            ```python
            {
                "id": 1,
                "name": "John Doe",
                "username": "john_doe",
                "email": "johndoe@example.com",
                "hashed_password": "hashed_password_example",
                "profile_image_url": "https://profileimageurl.com/default.jpg",
                "uuid": "123e4567-e89b-12d3-a456-426614174000",
                "created_at": "2023-01-01T12:00:00",
                "updated_at": "2023-01-02T12:00:00",
                "deleted_at": null,
                "is_deleted": false,
                "is_superuser": false,
                "tier_id": 2,
                "tier_name": "Premium",
                "tier_created_at": "2022-12-01T10:00:00",
                "tier_updated_at": "2023-01-01T11:00:00"
            }
            ```
        """
        if join_on is None:
            join_on = _auto_detect_join_condition(self.model, join_model)

        primary_select = _extract_matching_columns_from_schema(
            model=self.model, schema=schema_to_select
        )
        join_select = []

        if join_schema_to_select:
            columns = _extract_matching_columns_from_schema(
                model=join_model, schema=join_schema_to_select
            )
        else:
            columns = inspect(join_model).c

        for column in columns:
            labeled_column = _add_column_with_prefix(column, join_prefix)
            if f"{join_prefix}{column.name}" not in [
                col.name for col in primary_select
            ]:
                join_select.append(labeled_column)

        if join_type == "left":
            stmt = select(*primary_select, *join_select).outerjoin(join_model, join_on)
        elif join_type == "inner":
            stmt = select(*primary_select, *join_select).join(join_model, join_on)
        else:
            raise ValueError(
                f"Invalid join type: {join_type}. Only 'left' or 'inner' are valid."
            )

        for key, value in kwargs.items():
            if hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)

        db_row = await db.execute(stmt)
        result: Row = db_row.first()
        if result:
            out: dict = dict(result._mapping)
            return out

        return None

    async def get_multi_joined(
        self,
        db: AsyncSession,
        join_model: type[ModelType],
        join_prefix: Optional[str] = None,
        join_on: Optional[Join] = None,
        schema_to_select: Optional[type[BaseModel]] = None,
        join_schema_to_select: Optional[type[BaseModel]] = None,
        join_type: str = "left",
        offset: int = 0,
        limit: int = 100,
        sort_columns: Optional[Union[str, list[str]]] = None,
        sort_orders: Optional[Union[str, list[str]]] = None,
        return_as_model: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Fetch multiple records with a join on another model, allowing for pagination, optional sorting, and model conversion.

        Args:
            db: The SQLAlchemy async session.
            join_model: The model to join with.
            join_prefix: Optional prefix to be added to all columns of the joined model. If None, no prefix is added.
            join_on: SQLAlchemy Join object for specifying the ON clause of the join. If None, the join condition is auto-detected based on foreign keys.
            schema_to_select: Pydantic schema for selecting specific columns from the primary model.
            join_schema_to_select: Pydantic schema for selecting specific columns from the joined model.
            join_type: Specifies the type of join operation to perform. Can be "left" for a left outer join or "inner" for an inner join.
            offset: The offset (number of records to skip) for pagination.
            limit: The limit (maximum number of records to return) for pagination.
            sort_columns: A single column name or a list of column names on which to apply sorting.
            sort_orders: A single sort order ('asc' or 'desc') or a list of sort orders corresponding to the columns in sort_columns. If not provided, defaults to 'asc' for each column.
            return_as_model: If True, converts the fetched data to Pydantic models based on schema_to_select. Defaults to False.
            **kwargs: Filters to apply to the primary query.

        Returns:
            A dictionary containing the fetched rows under 'data' key and total count under 'total_count'.

        Raises:
            ValueError: If limit or offset is negative, or if schema_to_select is required but not provided or invalid.

        Examples:
            Fetching multiple User records joined with Tier records, using left join, returning raw data:
            >>> users = await crud_user.get_multi_joined(
                    db=session,
                    join_model=Tier,
                    join_prefix="tier_",
                    schema_to_select=UserSchema,
                    join_schema_to_select=TierSchema,
                    offset=0,
                    limit=10
                )

            Fetching and sorting by username in descending order, returning as Pydantic model:
            >>> users = await crud_user.get_multi_joined(
                    db=session,
                    join_model=Tier,
                    join_prefix="tier_",
                    schema_to_select=UserSchema,
                    join_schema_to_select=TierSchema,
                    offset=0,
                    limit=10,
                    sort_columns=['username'],
                    sort_orders=['desc'],
                    return_as_model=True
                )

            Fetching with complex conditions and custom join, returning as Pydantic model:
            >>> users = await crud_user.get_multi_joined(
                    db=session,
                    join_model=Tier,
                    join_prefix="tier_",
                    join_on=User.tier_id == Tier.id,
                    schema_to_select=UserSchema,
                    join_schema_to_select=TierSchema,
                    offset=0,
                    limit=10,
                    is_active=True,
                    return_as_model=True
                )
        """
        if limit < 0 or offset < 0:
            raise ValueError("Limit and offset must be non-negative.")

        if join_on is None:
            join_on = _auto_detect_join_condition(self.model, join_model)

        primary_select = _extract_matching_columns_from_schema(
            model=self.model, schema=schema_to_select
        )
        join_select = []

        if join_schema_to_select:
            columns = _extract_matching_columns_from_schema(
                model=join_model, schema=join_schema_to_select
            )
        else:
            columns = inspect(join_model).c

        for column in columns:
            labeled_column = _add_column_with_prefix(column, join_prefix)
            if f"{join_prefix}{column.name}" not in [
                col.name for col in primary_select
            ]:
                join_select.append(labeled_column)

        if join_type == "left":
            stmt = select(*primary_select, *join_select).outerjoin(join_model, join_on)
        elif join_type == "inner":
            stmt = select(*primary_select, *join_select).join(join_model, join_on)
        else:
            raise ValueError(
                f"Invalid join type: {join_type}. Only 'left' or 'inner' are valid."
            )

        for key, value in kwargs.items():
            if hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)

        if sort_columns:
            stmt = self._apply_sorting(stmt, sort_columns, sort_orders)

        stmt = stmt.offset(offset).limit(limit)

        db_rows = await db.execute(stmt)
        data = [dict(row._mapping) for row in db_rows]

        if return_as_model and schema_to_select:
            data = [schema_to_select.model_construct(**row) for row in data]

        total_count = await self.count(db=db, **kwargs)

        return {"data": data, "total_count": total_count}

    async def get_multi_by_cursor(
        self,
        db: AsyncSession,
        cursor: Any = None,
        limit: int = 100,
        schema_to_select: Optional[type[BaseModel]] = None,
        sort_column: str = "id",
        sort_order: str = "asc",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Fetch multiple records based on a cursor for pagination, with optional sorting.

        Args:
            db: The SQLAlchemy async session.
            cursor: The cursor value to start fetching records from. Defaults to None.
            limit: Maximum number of rows to fetch.
            schema_to_select: Pydantic schema for selecting specific columns.
            sort_column: Column name to use for sorting and cursor pagination.
            sort_order: Sorting direction, either 'asc' or 'desc'.
            **kwargs: Additional filters to apply to the query.

        Returns:
            A dictionary containing the fetched rows under 'data' key and the next cursor value under 'next_cursor'.

        Usage Examples:
            # Fetch the first set of records (e.g., the first page in an infinite scrolling scenario)
            >>> first_page = await crud.get_multi_by_cursor(db, limit=10, sort_column='created_at', sort_order='desc')

            # Fetch the next set of records using the cursor from the first page
            >>> next_cursor = first_page['next_cursor']
            >>> second_page = await crud.get_multi_by_cursor(db, cursor=next_cursor, limit=10, sort_column='created_at', sort_order='desc')

        Note:
            This method is designed for efficient pagination in large datasets and is ideal for infinite scrolling features.
            Make sure the column used for cursor pagination is indexed for performance.
            This method assumes that your records can be ordered by a unique, sequential field (like `id` or `created_at`).
        """
        if limit == 0:
            return {"data": [], "next_cursor": None}

        to_select = _extract_matching_columns_from_schema(self.model, schema_to_select)
        stmt = select(*to_select).filter_by(**kwargs)

        if cursor:
            if sort_order == "asc":
                stmt = stmt.where(getattr(self.model, sort_column) > cursor)
            else:
                stmt = stmt.where(getattr(self.model, sort_column) < cursor)

        stmt = stmt.order_by(
            asc(getattr(self.model, sort_column))
            if sort_order == "asc"
            else desc(getattr(self.model, sort_column))
        )
        stmt = stmt.limit(limit)

        result = await db.execute(stmt)
        data = [dict(row) for row in result.mappings()]

        next_cursor = None
        if len(data) == limit:
            next_cursor = data[-1][sort_column]

        return {"data": data, "next_cursor": next_cursor}

    async def update(
        self,
        db: AsyncSession,
        object: Union[UpdateSchemaType, dict[str, Any]],
        **kwargs: Any,
    ) -> None:
        """
        Update an existing record in the database.

        Args:
            db: The SQLAlchemy async session.
            object: The Pydantic schema or dictionary containing the data to be updated.
            **kwargs: Filters for the update.

        Returns:
            None

        Raises:
            ValueError: If extra fields not present in the model are provided in the update data.
        """
        if isinstance(object, dict):
            update_data = object
        else:
            update_data = object.model_dump(exclude_unset=True)

        if "updated_at" in update_data.keys():
            update_data["updated_at"] = datetime.now(timezone.utc)

        model_columns = {column.name for column in inspect(self.model).c}
        extra_fields = set(update_data) - model_columns
        if extra_fields:
            raise ValueError(f"Extra fields provided: {extra_fields}")

        stmt = update(self.model).filter_by(**kwargs).values(update_data)

        await db.execute(stmt)
        await db.commit()

    async def db_delete(self, db: AsyncSession, **kwargs: Any) -> None:
        """
        Delete a record in the database.

        Args:
            db: The SQLAlchemy async session.
            **kwargs: Filters for the delete.

        Returns:
            None
        """
        stmt = delete(self.model).filter_by(**kwargs)
        await db.execute(stmt)
        await db.commit()

    async def delete(
        self, db: AsyncSession, db_row: Optional[Row] = None, **kwargs: Any
    ) -> None:
        """
        Soft delete a record if it has "is_deleted" attribute, otherwise perform a hard delete.

        Args:
            db: The SQLAlchemy async session.
            db_row: Existing database row to delete. If None, it will be fetched based on `kwargs`. Default is None.
            **kwargs: Filters for fetching the database row if not provided.

        Returns:
            None
        """
        db_row = db_row or await self.exists(db=db, **kwargs)
        if db_row:
            if "is_deleted" in self.model.__table__.columns:
                object_dict = {
                    "is_deleted": True,
                    "deleted_at": datetime.now(timezone.utc),
                }
                stmt = update(self.model).filter_by(**kwargs).values(object_dict)

                await db.execute(stmt)
                await db.commit()

            else:
                stmt = delete(self.model).filter_by(**kwargs)
                await db.execute(stmt)
                await db.commit()
