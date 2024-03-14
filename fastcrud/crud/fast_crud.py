from typing import Any, Generic, TypeVar, Union, Optional
from datetime import datetime, timezone

from pydantic import BaseModel, ValidationError
from sqlalchemy import select, update, delete, func, inspect, asc, desc
from sqlalchemy.exc import ArgumentError, MultipleResultsFound, NoResultFound

from sqlalchemy.sql import Join
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine.row import Row
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql.elements import BinaryExpression
from sqlalchemy.sql.selectable import Select

from .helper import (
    _extract_matching_columns_from_schema,
    _auto_detect_join_condition,
    _add_column_with_prefix,
    JoinConfig,
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
        is_deleted_column: Optional column name to use for indicating a soft delete. Defaults to "is_deleted".
        deleted_at_column: Optional column name to use for storing the timestamp of a soft delete. Defaults to "deleted_at".
        updated_at_column: Optional column name to use for storing the timestamp of an update. Defaults to "updated_at".

    Methods:
        create:
            Creates a new record in the database from the provided Pydantic schema.

        get:
            Retrieves a single record based on filters. Supports advanced filtering through comparison operators like '__gt', '__lt', etc.

        exists:
            Checks if a record exists based on the provided filters.

        count:
            Counts the number of records matching the provided filters.

        get_multi:
            Fetches multiple records with optional sorting, pagination, and model conversion.

        get_joined:
            Performs a join operation with another model, supporting custom join conditions and selection of specific columns.

        get_multi_joined:
            Fetches multiple records with a join on another model, offering pagination and sorting for the joined tables.

        get_multi_by_cursor:
            Implements cursor-based pagination for fetching records, ideal for large datasets and infinite scrolling features.

        update:
            Updates an existing record or multiple records based on specified filters.

        db_delete:
            Hard deletes a record or multiple records from the database based on provided filters.

        delete:
            Soft deletes a record if it has an "is_deleted" attribute; otherwise, performs a hard delete.

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

        Example 6: Using Custom Column Names for Soft Delete
        ----------------------------------------------------
        If your model uses different column names for indicating a soft delete and its timestamp, you can specify these when creating the FastCRUD instance.
        ```python
        custom_user_crud = FastCRUD(User, UserCreateSchema, UserUpdateSchema, is_deleted_column="archived", deleted_at_column="archived_at")
        # Now 'archived' and 'archived_at' will be used for soft delete operations.
        ```
    """

    def __init__(
        self,
        model: type[ModelType],
        is_deleted_column: str = "is_deleted",
        deleted_at_column: str = "deleted_at",
        updated_at_column: str = "updated_at",
    ) -> None:
        self.model = model
        self.is_deleted_column = is_deleted_column
        self.deleted_at_column = deleted_at_column
        self.updated_at_column = updated_at_column

    def _parse_filters(self, **kwargs) -> list[BinaryExpression]:
        filters = []
        for key, value in kwargs.items():
            if "__" in key:
                field_name, op = key.rsplit("__", 1)
                column = getattr(self.model, field_name, None)
                if column is None:
                    raise ValueError(f"Invalid filter column: {field_name}")

                if op == "gt":
                    filters.append(column > value)
                elif op == "lt":
                    filters.append(column < value)
                elif op == "gte":
                    filters.append(column >= value)
                elif op == "lte":
                    filters.append(column <= value)
                elif op == "ne":
                    filters.append(column != value)
            else:
                column = getattr(self.model, key, None)
                if column is not None:
                    filters.append(column == value)

        return filters

    def _apply_sorting(
        self,
        stmt: Select,
        sort_columns: Union[str, list[str]],
        sort_orders: Optional[Union[str, list[str]]] = None,
    ) -> Select:
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
        return_as_model: bool = False,
        **kwargs: Any,
    ) -> Optional[Union[dict, BaseModel]]:
        """
        Fetches a single record based on specified filters.
        This method allows for advanced filtering through comparison operators, enabling queries to be refined beyond simple equality checks.
        Supported operators include:
            '__gt' (greater than),
            '__lt' (less than),
            '__gte' (greater than or equal to),
            '__lte' (less than or equal to), and
            '__ne' (not equal).

        Args:
            db: The database session to use for the operation.
            schema_to_select: Optional Pydantic schema for selecting specific columns.
            **kwargs: Filters to apply to the query, using field names for direct matches or appending comparison operators for advanced queries.

        Raises:
            ValueError: If return_as_model is True but schema_to_select is not provided.

        Returns:
            A dictionary or a Pydantic model instance of the fetched database row, or None if no match is found.

        Examples:
            Fetch a user by ID:
            ```python
            user = await crud.get(db, id=1)
            ```

            Fetch a user with an age greater than 30:
            ```python
            user = await crud.get(db, age__gt=30)
            ```

            Fetch a user with a registration date before Jan 1, 2020:
            ```python
            user = await crud.get(db, registration_date__lt=datetime(2020, 1, 1))
            ```

            Fetch a user not equal to a specific username:
            ```python
            user = await crud.get(db, username__ne='admin')
            ```
        """
        to_select = _extract_matching_columns_from_schema(
            model=self.model, schema=schema_to_select
        )
        filters = self._parse_filters(**kwargs)
        stmt = select(*to_select).filter(*filters)

        db_row = await db.execute(stmt)
        result: Row = db_row.first()
        if result is not None:
            out: dict = dict(result._mapping)
            if return_as_model:
                if not schema_to_select:
                    raise ValueError(
                        "schema_to_select must be provided when return_as_model is True."
                    )
                return schema_to_select(**out)
            return out

        return None

    async def exists(self, db: AsyncSession, **kwargs: Any) -> bool:
        """
        Checks if any records exist that match the given filter conditions.
        This method supports advanced filtering with comparison operators:
            '__gt' (greater than),
            '__lt' (less than),
            '__gte' (greater than or equal to),
            '__lte' (less than or equal to), and
            '__ne' (not equal).

        Args:
            db: The database session to use for the operation.
            **kwargs: Filters to apply to the query, supporting both direct matches and advanced comparison operators for refined search criteria.

        Returns:
            True if at least one record matches the filter conditions, False otherwise.

        Examples:
            Fetch a user by ID exists:
            ```python
            exists = await crud.exists(db, id=1)
            ```

            Check if any user is older than 30:
            ```python
            exists = await crud.exists(db, age__gt=30)
            ```

            Check if any user registered before Jan 1, 2020:
            ```python
            exists = await crud.exists(db, registration_date__lt=datetime(2020, 1, 1))
            ```

            Check if a username other than 'admin' exists:
            ```python
            exists = await crud.exists(db, username__ne='admin')
            ```
        """
        filters = self._parse_filters(**kwargs)
        stmt = select(self.model).filter(*filters).limit(1)

        result = await db.execute(stmt)
        return result.first() is not None

    async def count(self, db: AsyncSession, **kwargs: Any) -> int:
        """
        Counts records that match specified filters, supporting advanced filtering through comparison operators:
            '__gt' (greater than),
            '__lt' (less than),
            '__gte' (greater than or equal to),
            '__lte' (less than or equal to), and
            '__ne' (not equal).

        Args:
            db: The database session to use for the operation.
            **kwargs: Filters to apply for the count, including field names for equality checks or with comparison operators for advanced queries.

        Returns:
            The total number of records matching the filter conditions.

        Examples:
            Count users by ID:
            ```python
            exists = await crud.count(db, id=1)
            ```

            Count users older than 30:
            ```python
            exists = await crud.count(db, age__gt=30)
            ```

            Count users who registered before Jan 1, 2020:
            ```python
            exists = await crud.count(db, registration_date__lt=datetime(2020, 1, 1))
            ```

            Count users with a username other than 'admin':
            ```python
            exists = await crud.count(db, username__ne='admin')
            ```
        """
        filters = self._parse_filters(**kwargs)
        if filters:
            count_query = select(func.count()).select_from(self.model).filter(*filters)
        else:
            count_query = select(func.count()).select_from(self.model)

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
        Fetches multiple records based on filters, supporting sorting, pagination, and advanced filtering with comparison operators:
            '__gt' (greater than),
            '__lt' (less than),
            '__gte' (greater than or equal to),
            '__lte' (less than or equal to), and
            '__ne' (not equal).

        Args:
            db: The database session to use for the operation.
            offset: Starting index for records to fetch, useful for pagination.
            limit: Maximum number of records to fetch in one call.
            schema_to_select: Optional Pydantic schema for selecting specific columns. Required if `return_as_model` is True.
            sort_columns: Column names to sort the results by.
            sort_orders: Corresponding sort orders ('asc', 'desc') for each column in sort_columns.
            return_as_model: If True, returns data as instances of the specified Pydantic model.
            **kwargs: Filters to apply to the query, including advanced comparison operators for more detailed querying.

        Returns:
            A dictionary containing 'data' with fetched records and 'total_count' indicating the total number of records matching the filters.

        Raises:
            ValueError: If limit or offset is negative, or if schema_to_select is required but not provided or invalid.

        Examples:
            Fetch the first 10 users:
            ```python
            users = await crud.get_multi(db, 0, 10)
            ```

            Fetch next 10 users with sorted by username:
            ```python
            users = await crud.get_multi(db, 10, 10, sort_columns='username', sort_orders='desc')
            ```

            Fetch 10 users older than 30, sorted by age in descending order:
            ```python
            get_multi(db, offset=0, limit=10, age__gt=30, sort_columns='age', sort_orders='desc')
            ```

            Fetch 10 users with a registration date before Jan 1, 2020:
            ```python
            get_multi(db, offset=0, limit=10, registration_date__lt=datetime(2020, 1, 1))
            ```

            Fetch 10 users with a username other than 'admin', returning as model instances (ensure appropriate schema is passed):
            ```python
            get_multi(db, offset=0, limit=10, username__ne='admin', schema_to_select=UserSchema, return_as_model=True)
            ```

            Fetch users with filtering and multiple column sorting:
            ```python
            users = await crud.get_multi(db, 0, 10, is_active=True, sort_columns=['username', 'email'], sort_orders=['asc', 'desc'])
            ```
        """
        if limit < 0 or offset < 0:
            raise ValueError("Limit and offset must be non-negative.")

        to_select = _extract_matching_columns_from_schema(self.model, schema_to_select)
        filters = self._parse_filters(**kwargs)
        stmt = select(*to_select).filter(*filters)

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
        join_model: Optional[type[DeclarativeBase]] = None,
        join_prefix: Optional[str] = None,
        join_on: Optional[Union[Join, BinaryExpression]] = None,
        schema_to_select: Optional[type[BaseModel]] = None,
        join_schema_to_select: Optional[type[BaseModel]] = None,
        join_type: str = "left",
        joins_config: Optional[list[JoinConfig]] = None,
        **kwargs: Any,
    ) -> Optional[dict[str, Any]]:
        """
        Fetches a single record with one or multiple joins on other models. If 'join_on' is not provided, the method attempts
        to automatically detect the join condition using foreign key relationships. For multiple joins, use 'joins_config' to
        specify each join configuration. Advanced filters supported:
            '__gt' (greater than),
            '__lt' (less than),
            '__gte' (greater than or equal to),
            '__lte' (less than or equal to), and
            '__ne' (not equal).

        Args:
            db: The SQLAlchemy async session.
            join_model: The model to join with.
            join_prefix: Optional prefix to be added to all columns of the joined model. If None, no prefix is added.
            join_on: SQLAlchemy Join object for specifying the ON clause of the join. If None, the join condition is auto-detected based on foreign keys.
            schema_to_select: Pydantic schema for selecting specific columns from the primary model. Required if `return_as_model` is True.
            join_schema_to_select: Pydantic schema for selecting specific columns from the joined model.
            join_type: Specifies the type of join operation to perform. Can be "left" for a left outer join or "inner" for an inner join.
            joins_config: A list of JoinConfig instances, each specifying a model to join with, join condition, optional prefix for column names, schema for selecting specific columns, and the type of join. This parameter enables support for multiple joins.
            **kwargs: Filters to apply to the primary model query, supporting advanced comparison operators for refined searching.

        Returns:
            A dictionary representing the joined record, or None if no record matches the criteria.

        Raises:
            ValueError: If both single join parameters and 'joins_config' are used simultaneously.
            ArgumentError: If any provided model in 'joins_config' is not recognized or invalid.
            NoResultFound: If no record matches the criteria with the provided filters.

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

            Fetch a user and their associated tier, filtering by user ID:
            ```python
            get_joined(db, User, Tier, schema_to_select=UserSchema, join_schema_to_select=TierSchema, id=1)
            ```

            Fetch a user and their associated tier, where the user's age is greater than 30:
            ```python
            get_joined(db, User, Tier, schema_to_select=UserSchema, join_schema_to_select=TierSchema, age__gt=30)
            ```

            Fetch a user and their associated tier, excluding users with the 'admin' username:
            ```python
            get_joined(db, User, Tier, schema_to_select=UserSchema, join_schema_to_select=TierSchema, username__ne='admin')
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

            Example of using 'joins_config' for multiple joins:
            ```python
            from fastcrud import JoinConfig

            result = await crud_user.get_joined(
                db=session,
                schema_to_select=UserSchema,
                joins_config=[
                    JoinConfig(
                        model=Tier,
                        join_on=User.tier_id == Tier.id,
                        join_prefix="tier_",
                        schema_to_select=TierSchema,
                        join_type="left",
                    ),
                    JoinConfig(
                        model=Department,
                        join_on=User.department_id == Department.id,
                        join_prefix="dept_",
                        schema_to_select=DepartmentSchema,
                        join_type="inner",
                    )
                ]
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
        if joins_config and (
            join_model or join_prefix or join_on or join_schema_to_select
        ):
            raise ValueError(
                "Cannot use both single join parameters and joinsConfig simultaneously."
            )
        elif not joins_config and not join_model:
            raise ValueError("You need one of join_model or joins_config.")

        primary_select = _extract_matching_columns_from_schema(
            model=self.model, schema=schema_to_select
        )
        stmt: Select = select(*primary_select)

        join_definitions = joins_config if joins_config else []
        if join_model:
            join_definitions.append(
                JoinConfig(
                    model=join_model,
                    join_on=join_on,
                    join_prefix=join_prefix,
                    schema_to_select=join_schema_to_select,
                    join_type=join_type,
                )
            )

        for join in join_definitions:
            join_select = _extract_matching_columns_from_schema(
                join.model, join.schema_to_select
            )

            if join.join_prefix:
                join_select = [
                    _add_column_with_prefix(column, join.join_prefix)
                    for column in join_select
                ]

            if join.join_type == "left":
                stmt = stmt.outerjoin(join.model, join.join_on).add_columns(
                    *join_select
                )
            elif join.join_type == "inner":
                stmt = stmt.join(join.model, join.join_on).add_columns(*join_select)
            else:
                raise ValueError(f"Unsupported join type: {join.join_type}.")

        filters = self._parse_filters(**kwargs)
        if filters:
            stmt = stmt.filter(*filters)

        db_row = await db.execute(stmt)
        result: Row = db_row.first()
        if result:
            out: dict = dict(result._mapping)
            return out

        return None

    async def get_multi_joined(
        self,
        db: AsyncSession,
        join_model: Optional[type[ModelType]] = None,
        join_prefix: Optional[str] = None,
        join_on: Optional[Any] = None,
        schema_to_select: Optional[type[BaseModel]] = None,
        join_schema_to_select: Optional[type[BaseModel]] = None,
        join_type: str = "left",
        offset: int = 0,
        limit: int = 100,
        sort_columns: Optional[Union[str, list[str]]] = None,
        sort_orders: Optional[Union[str, list[str]]] = None,
        return_as_model: bool = False,
        joins_config: Optional[list[JoinConfig]] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Fetch multiple records with a join on another model, allowing for pagination, optional sorting, and model conversion,
        supporting advanced filtering with comparison operators:
            '__gt' (greater than),
            '__lt' (less than),
            '__gte' (greater than or equal to),
            '__lte' (less than or equal to), and
            '__ne' (not equal).

        Args:
            db: The SQLAlchemy async session.
            join_model: The model to join with.
            join_prefix: Optional prefix to be added to all columns of the joined model. If None, no prefix is added.
            join_on: SQLAlchemy Join object for specifying the ON clause of the join. If None, the join condition is auto-detected based on foreign keys.
            schema_to_select: Pydantic schema for selecting specific columns from the primary model. Required if `return_as_model` is True.
            join_schema_to_select: Pydantic schema for selecting specific columns from the joined model.
            join_type: Specifies the type of join operation to perform. Can be "left" for a left outer join or "inner" for an inner join.
            offset: The offset (number of records to skip) for pagination.
            limit: The limit (maximum number of records to return) for pagination.
            sort_columns: A single column name or a list of column names on which to apply sorting.
            sort_orders: A single sort order ('asc' or 'desc') or a list of sort orders corresponding to the columns in sort_columns. If not provided, defaults to 'asc' for each column.
            return_as_model: If True, converts the fetched data to Pydantic models based on schema_to_select. Defaults to False.
            joins_config: List of JoinConfig instances for specifying multiple joins. Each instance defines a model to join with, join condition, optional prefix for column names, schema for selecting specific columns, and join type.
            **kwargs: Filters to apply to the primary query, including advanced comparison operators for refined searching.

        Returns:
            A dictionary containing the fetched rows under 'data' key and total count under 'total_count'.

        Raises:
            ValueError: If limit or offset is negative, or if schema_to_select is required but not provided or invalid.
                        Also if both 'joins_config' and any of the single join parameters are provided or none of 'joins_config' and 'join_model' is provided.

        Examples:
            Fetching multiple User records joined with Tier records, using left join, returning raw data:
            ```python
            users = await crud_user.get_multi_joined(
                db=session,
                join_model=Tier,
                join_prefix="tier_",
                schema_to_select=UserSchema,
                join_schema_to_select=TierSchema,
                offset=0,
                limit=10
            )
            ```

            Fetch users joined with their tiers, sorted by username, where user's age is greater than 30:
            ```python
            users = get_multi_joined(
                db,
                User,
                Tier,
                schema_to_select=UserSchema,
                join_schema_to_select=TierSchema,
                age__gt=30,
                sort_columns='username',
                sort_orders='asc'
            )
            ```

            Fetch users joined with their tiers, excluding users with 'admin' username, returning as model instances:
            ```python
            users = get_multi_joined(
                db,
                User,
                Tier,
                schema_to_select=UserSchema,
                join_schema_to_select=TierSchema,
                username__ne='admin',
                return_as_model=True
            )
            ```

            Fetching and sorting by username in descending order, returning as Pydantic model:
            ```python
            users = await crud_user.get_multi_joined(
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
            ```

            Fetching with complex conditions and custom join, returning as Pydantic model:
            ```python
            users = await crud_user.get_multi_joined(
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
            ```

            Example using 'joins_config' for multiple joins:
            ```python
            from fastcrud import JoinConfig

            users = await crud_user.get_multi_joined(
                db=session,
                schema_to_select=UserSchema,
                joins_config=[
                    JoinConfig(
                        model=Tier,
                        join_on=User.tier_id == Tier.id,
                        join_prefix="tier_",
                        schema_to_select=TierSchema,
                        join_type="left",
                    ),
                    JoinConfig(
                        model=Department,
                        join_on=User.department_id == Department.id,
                        join_prefix="dept_",
                        schema_to_select=DepartmentSchema,
                        join_type="inner",
                    )
                ],
                offset=0,
                limit=10,
                sort_columns='username',
                sort_orders='asc'
            )
            ```
        """
        if joins_config and (
            join_model or join_prefix or join_on or join_schema_to_select
        ):
            raise ValueError(
                "Cannot use both single join parameters and joinsConfig simultaneously."
            )
        elif not joins_config and not join_model:
            raise ValueError("You need one of join_model or joins_config.")

        if limit < 0 or offset < 0:
            raise ValueError("Limit and offset must be non-negative.")

        joins: list[JoinConfig] = []
        if join_model is not None:
            joins.append(
                JoinConfig(
                    model=join_model,
                    join_on=join_on
                    or _auto_detect_join_condition(self.model, join_model),
                    join_prefix=join_prefix,
                    schema_to_select=join_schema_to_select,
                    join_type=join_type,
                )
            )
        elif joins_config:
            joins.extend(joins_config)

        primary_select = _extract_matching_columns_from_schema(
            model=self.model, schema=schema_to_select
        )
        stmt: Select = select(*primary_select)

        for join in joins:
            if join.schema_to_select:
                join_select = _extract_matching_columns_from_schema(
                    join.model, join.schema_to_select
                )
            else:
                join_select = inspect(join.model).c

            if join.join_prefix:
                join_select = [
                    _add_column_with_prefix(column, join.join_prefix)
                    for column in join_select
                ]

            if join.join_type == "left":
                stmt = stmt.outerjoin(join.model, join.join_on).add_columns(
                    *join_select
                )
            elif join.join_type == "inner":
                stmt = stmt.join(join.model, join.join_on).add_columns(*join_select)
            else:
                raise ValueError(f"Unsupported join type: {join.join_type}.")

        filters = self._parse_filters(**kwargs)
        if filters:
            stmt = stmt.filter(*filters)

        if sort_columns:
            stmt = self._apply_sorting(stmt, sort_columns, sort_orders)

        stmt = stmt.offset(offset).limit(limit)

        result = await db.execute(stmt)
        data = [dict(row) for row in result.mappings().all()]

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
        Implements cursor-based pagination for fetching records. This method is designed for efficient data retrieval in large datasets and is ideal for features like infinite scrolling.
        It supports advanced filtering with comparison operators:
            '__gt' (greater than),
            '__lt' (less than),
            '__gte' (greater than or equal to),
            '__lte' (less than or equal to), and
            '__ne' (not equal).

        Args:
            db: The SQLAlchemy async session.
            cursor: The cursor value to start fetching records from. Defaults to None.
            limit: Maximum number of rows to fetch.
            schema_to_select: Pydantic schema for selecting specific columns.
            sort_column: Column name to use for sorting and cursor pagination.
            sort_order: Sorting direction, either 'asc' or 'desc'.
            **kwargs: Filters to apply to the query, including advanced comparison operators for detailed querying.

        Returns:
            A dictionary containing the fetched rows under 'data' key and the next cursor value under 'next_cursor'.

        Examples:
            Fetch the first set of records (e.g., the first page in an infinite scrolling scenario)
            ```python
            first_page = await crud.get_multi_by_cursor(db, limit=10, sort_column='created_at', sort_order='desc')

            Fetch the next set of records using the cursor from the first page
            next_cursor = first_page['next_cursor']
            second_page = await crud.get_multi_by_cursor(db, cursor=next_cursor, limit=10, sort_column='created_at', sort_order='desc')
            ```

            Fetch records with age greater than 30 using cursor-based pagination:
            ```python
            get_multi_by_cursor(db, limit=10, sort_column='age', sort_order='asc', age__gt=30)
            ```

            Fetch records excluding a specific username using cursor-based pagination:
            ```python
            get_multi_by_cursor(db, limit=10, sort_column='username', sort_order='asc', username__ne='admin')
            ```

        Note:
            This method is designed for efficient pagination in large datasets and is ideal for infinite scrolling features.
            Make sure the column used for cursor pagination is indexed for performance.
            This method assumes that your records can be ordered by a unique, sequential field (like `id` or `created_at`).
        """
        if limit == 0:
            return {"data": [], "next_cursor": None}

        to_select = _extract_matching_columns_from_schema(self.model, schema_to_select)
        filters = self._parse_filters(**kwargs)

        stmt = select(*to_select)
        if filters:
            stmt = stmt.filter(*filters)

        if cursor:
            if sort_order == "asc":
                stmt = stmt.filter(getattr(self.model, sort_column) > cursor)
            else:
                stmt = stmt.filter(getattr(self.model, sort_column) < cursor)

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
            if sort_order == "asc":
                next_cursor = data[-1][sort_column]
            else:
                data[0][sort_column]

        return {"data": data, "next_cursor": next_cursor}

    async def update(
        self,
        db: AsyncSession,
        object: Union[UpdateSchemaType, dict[str, Any]],
        allow_multiple: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        Updates an existing record or multiple records in the database based on specified filters. This method allows for precise targeting of records to update.
        It supports advanced filtering through comparison operators:
            '__gt' (greater than),
            '__lt' (less than),
            '__gte' (greater than or equal to),
            '__lte' (less than or equal to), and
            '__ne' (not equal).

        Args:
            db: The database session to use for the operation.
            object: A Pydantic schema or dictionary containing the update data.
            allow_multiple: If True, allows updating multiple records that match the filters. If False, raises an error if more than one record matches the filters.
            **kwargs: Filters to identify the record(s) to update, supporting advanced comparison operators for refined querying.

        Returns:
            None

        Raises:
            MultipleResultsFound: If `allow_multiple` is False and more than one record matches the filters.
            ValueError: If extra fields not present in the model are provided in the update data.

        Examples:
            Update a user's email based on their ID:
            ```python
            update(db, {'email': 'new_email@example.com'}, id=1)
            ```

            Update users' statuses to 'inactive' where age is greater than 30 and allow updates to multiple records:
            ```python
            update(db, {'status': 'inactive'}, allow_multiple=True, age__gt=30)
            ```

            Update a user's username excluding specific user ID and prevent multiple updates:
            ```python
            update(db, {'username': 'new_username'}, id__ne=1, allow_multiple=False)
            ```
        """
        total_count = await self.count(db, **kwargs)
        if not allow_multiple and total_count > 1:
            raise MultipleResultsFound(
                f"Expected exactly one record to update, found {total_count}."
            )

        if isinstance(object, dict):
            update_data = object
        else:
            update_data = object.model_dump(exclude_unset=True)

        updated_at_col = getattr(self.model, self.updated_at_column, None)
        if updated_at_col and updated_at_col in update_data.keys():
            update_data[updated_at_col] = datetime.now(timezone.utc)

        model_columns = {column.name for column in inspect(self.model).c}
        extra_fields = set(update_data) - model_columns
        if extra_fields:
            raise ValueError(f"Extra fields provided: {extra_fields}")

        filters = self._parse_filters(**kwargs)
        stmt = update(self.model).filter(*filters).values(update_data)

        await db.execute(stmt)
        await db.commit()

    async def db_delete(
        self, db: AsyncSession, allow_multiple: bool = False, **kwargs: Any
    ) -> None:
        """
        Deletes a record or multiple records from the database based on specified filters, with support for advanced filtering through comparison operators:
            '__gt' (greater than),
            '__lt' (less than),
            '__gte' (greater than or equal to),
            '__lte' (less than or equal to), and
            '__ne' (not equal).

        Args:
            db: The database session to use for the operation.
            allow_multiple: If True, allows deleting multiple records that match the filters. If False, raises an error if more than one record matches the filters.
            **kwargs: Filters to identify the record(s) to delete, including advanced comparison operators for detailed querying.

        Returns:
            None

        Raises:
            MultipleResultsFound: If `allow_multiple` is False and more than one record matches the filters.

        Examples:
            Delete a user based on their ID:
            ```python
            db_delete(db, id=1)
            ```

            Delete users older than 30 years and allow deletion of multiple records:
            ```python
            db_delete(db, allow_multiple=True, age__gt=30)
            ```

            Delete a user with a specific username, ensuring only one record is deleted:
            ```python
            db_delete(db, username='unique_username', allow_multiple=False)
            ```
        """
        total_count = await self.count(db, **kwargs)
        if not allow_multiple and total_count > 1:
            raise MultipleResultsFound(
                f"Expected exactly one record to delete, found {total_count}."
            )

        filters = self._parse_filters(**kwargs)
        stmt = delete(self.model).filter(*filters)
        await db.execute(stmt)
        await db.commit()

    async def delete(
        self,
        db: AsyncSession,
        db_row: Optional[Row] = None,
        allow_multiple: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        Soft deletes a record or optionally multiple records if it has an "is_deleted" attribute, otherwise performs a hard delete, based on specified filters.
        Supports advanced filtering through comparison operators:
            '__gt' (greater than),
            '__lt' (less than),
            '__gte' (greater than or equal to),
            '__lte' (less than or equal to), and
            '__ne' (not equal).

        Args:
            db: The database session to use for the operation.
            db_row: Optional existing database row to delete. If provided, the method will attempt to delete this specific row, ignoring other filters.
            allow_multiple: If True, allows deleting multiple records that match the filters. If False, raises an error if more than one record matches the filters.
            **kwargs: Filters to identify the record(s) to delete, supporting advanced comparison operators for refined querying.

        Raises:
            MultipleResultsFound: If `allow_multiple` is False and more than one record matches the filters.
            NoResultFound: If no record matches the filters.

        Returns:
            None

        Examples:
            Soft delete a specific user by ID:
            ```python
            delete(db, id=1)
            ```

            Hard delete users with account creation dates before 2020, allowing deletion of multiple records:
            ```python
            delete(db, allow_multiple=True, creation_date__lt=datetime(2020, 1, 1))
            ```

            Soft delete a user with a specific email, ensuring only one record is deleted:
            ```python
            delete(db, email='unique@example.com', allow_multiple=False)
            ```
        """
        filters = self._parse_filters(**kwargs)
        if db_row:
            if hasattr(db_row, self.is_deleted_column):
                is_deleted_col = getattr(self.model, self.is_deleted_column)
                deleted_at_col = getattr(self.model, self.deleted_at_column, None)

                update_values = {
                    is_deleted_col: True,
                    deleted_at_col: datetime.now(timezone.utc),
                }
                update_stmt = (
                    update(self.model).filter(*filters).values(**update_values)
                )
                await db.execute(update_stmt)
            else:
                await db.delete(db_row)
                await db.commit()

        total_count = await self.count(db, **kwargs)
        if total_count == 0:
            raise NoResultFound("No record found to delete.")
        if not allow_multiple and total_count > 1:
            raise MultipleResultsFound(
                f"Expected exactly one record to delete, found {total_count}."
            )

        if self.is_deleted_column in self.model.__table__.columns:
            update_stmt = (
                update(self.model)
                .filter(*filters)
                .values(is_deleted=True, deleted_at=datetime.now(timezone.utc))
            )
            await db.execute(update_stmt)
        else:
            delete_stmt = delete(self.model).filter(*filters)
            await db.execute(delete_stmt)

        await db.commit()
