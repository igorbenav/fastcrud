
# Advanced Use of FastCRUD

FastCRUD offers a flexible and powerful approach to handling CRUD operations in FastAPI applications, leveraging the SQLAlchemy ORM. Beyond basic CRUD functionality, FastCRUD provides advanced features like `allow_multiple` for updates and deletes, and support for advanced filters (e.g., less than, greater than). These features enable more complex and fine-grained data manipulation and querying capabilities.

## Typing Options for `FastCRUD`

Note that when initializing `FastCRUD`, assuming you have a model like:

```python
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    archived = Column(Boolean, default=False)
    archived_at = Column(DateTime)
```

!!! WARNING

    Note that naive `datetime` such as `datetime.utcnow` is not supported by `FastCRUD` as it was [deprecated](https://github.com/python/cpython/pull/103858).
    
    Use timezone aware `datetime`, such as `datetime.now(UTC)` instead.

You could just pass it to `FastCRUD`:

```python
from fastcrud import FastCRUD

crud_user = FastCRUD(User)
```

But you also may want a more robust typing, for that purpose, you may also pass the relevant pydantic schemas in the following way:

```python
from .models.user import User
from .schemas.user import UserCreate, UserUpdate, UserUpdateInternal, UserDelete

# Just pass None if you don't have one of the schemas
CRUDUser = FastCRUD[User, UserCreate, UserUpdate, UserUpdateInternal, UserDelete]
```

Then you can initialize CRUDUser like you would any FastCRUD instance, but with the relevant types:

```python
from .models.user import User

crud_user = CRUDUser(User)
```

## Allow Multiple Updates and Deletes

One of FastCRUD's advanced features is the ability to update or delete multiple records at once based on specified conditions. This is particularly useful for batch operations where you need to modify or remove several records that match certain criteria.

### Updating Multiple Records

To update multiple records, you can set the `allow_multiple=True` parameter in the `update` method. This allows FastCRUD to apply the update to all records matching the given filters.

```python
# Assuming setup for FastCRUD instance `item_crud` and SQLAlchemy async session `db`

# Update all items priced below $10 to a new price
await item_crud.update(
    db=db,
    object={"price": 9.99},
    allow_multiple=True,
    price__lt=10
)
```

### Deleting Multiple Records

Similarly, you can delete multiple records by using the `allow_multiple=True` parameter in the `delete` or `db_delete` method, depending on whether you're performing a soft or hard delete.

```python
# Soft delete all items not sold in the last year
await item_crud.delete(
    db=db,
    allow_multiple=True,
    last_sold__lt=datetime.datetime.now() - datetime.timedelta(days=365)
)
```

## Advanced Filters

FastCRUD supports advanced filtering options, allowing you to query records using operators such as greater than (`__gt`), less than (`__lt`), and their inclusive counterparts (`__gte`, `__lte`). These filters can be used in any method that retrieves or operates on records, including `get`, `get_multi`, `exists`, `count`, `update`, and `delete`.

### Using Advanced Filters

The following examples demonstrate how to use advanced filters for querying and manipulating data:

#### Fetching Records with Advanced Filters

```python
# Fetch items priced between $5 and $20
items = await item_crud.get_multi(
    db=db,
    price__gte=5,
    price__lte=20
)
```

Currently supported filter operators are:
- __gt - greater than
- __lt - less than
- __gte - greater than or equal to
- __lte - less than or equal to
- __ne - not equal
- __in - included in (tuple, list or set)
- __not_in - not included in (tuple, list or set)

#### Counting Records

```python
# Count items added in the last month
item_count = await item_crud.count(
    db=db,
    added_at__gte=datetime.datetime.now() - datetime.timedelta(days=30)
)
```

## Skipping Database Commit

For `create`, `update`, `db_delete` and `delete` methods of `FastCRUD`, you have the option of passing `commit=False` so you don't commit the operations immediately.

```python
from fastcrud import FastCRUD

from .models.item import Item
from .database import session as db

crud_items = FastCRUD(Item)

await crud_items.delete(
    db=db, 
    commit=False, 
    id=1
)
# this will not actually delete until you run a db.commit()
```

## Unpaginated `get_multi` and `get_multi_joined`

If you pass `None` to `limit` in `get_multi` and `get_multi_joined`, you get the whole unpaginated set of data that matches the filters. Use this with caution.

```python
from fastcrud import FastCRUD

from .models.item import Item
from .database import session as db

crud_items = FastCRUD(Item)
items = await crud_items.get_multi(db=db, limit=None)
# this will return all items in the db
```

!!! CAUTION
    Be cautious when returning all the data in your database, and you should almost never allow your API user to do this.

## Using `get_joined` and `get_multi_joined` for multiple models

To facilitate complex data relationships, `get_joined` and `get_multi_joined` can be configured to handle joins with multiple models. This is achieved using the `joins_config` parameter, where you can specify a list of `JoinConfig` instances, each representing a distinct join configuration.

#### Example: Joining User, Tier, and Department Models

Consider a scenario where you want to retrieve users along with their associated tier and department information. Here's how you can achieve this using `get_multi_joined`.

Start by creating a list of the multiple models to be joined:

```python hl_lines="1 3-10 12-19" title="Join Configurations"
from fastcrud import JoinConfig

joins_config = [
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

users = await user_crud.get_multi_joined(
    db=session,
    schema_to_select=UserSchema,
    joins_config=joins_config,
    offset=0,
    limit=10,
    sort_columns='username',
    sort_orders='asc'
)
```

Then just pass this list to joins_config:

```python hl_lines="10" title="Passing to get_multi_joined"
from fastcrud import JoinConfig

joins_config = [
    ...
]

users = await user_crud.get_multi_joined(
    db=session,
    schema_to_select=UserSchema,
    joins_config=joins_config,
    offset=0,
    limit=10,
    sort_columns='username',
    sort_orders='asc'
)
```

In this example, users are joined with the `Tier` and `Department` models. The `join_on` parameter specifies the condition for the join, `join_prefix` assigns a prefix to columns from the joined models (to avoid naming conflicts), and `join_type` determines whether it's a left or inner join.

!!! WARNING

    If both single join parameters and `joins_config` are used simultaneously, an error will be raised.

### Handling One-to-One and One-to-Many Joins in FastCRUD

FastCRUD provides flexibility in handling one-to-one and one-to-many relationships through its `get_joined` and `get_multi_joined` methods, along with the ability to specify how joined data should be structured using both the `relationship_type` (default `one-to-one`) and the `nest_joins` (default `False`) parameters.

#### One-to-One Joins
**One-to-one** relationships can be efficiently managed using either `get_joined` or `get_multi_joined`. The `get_joined` method is typically used when you want to fetch a single record from the database along with its associated record from another table, such as a user and their corresponding profile details. If you're retrieving multiple records, `get_multi_joined` can also be used for one-to-one joins. The parameter that deals with it, `relationship_type`, defaults to `one-on-one`.

#### One-to-Many Joins
For **one-to-many** relationships, where a single record can be associated with multiple records in another table, `get_joined` can be used with `nest_joins` set to `True`. This setup allows the primary record to include a nested list of associated records, making it suitable for scenarios such as retrieving a user and all their blog posts. Alternatively, `get_multi_joined` is also applicable here for fetching multiple primary records, each with their nested lists of related records.

!!! WARNING

    When using `nested_joins=True`, the performance will always be a bit worse than when using `nested_joins=False`. For cases where more performance is necessary, consider using `nested_joins=False` and remodeling your database.

#### One-to-One Relationships
- **`get_joined`**: Fetch a single record and its directly associated record (e.g., a user and their profile).
- **`get_multi_joined`** (with `nest_joins=False`): Retrieve multiple records, each linked to a single related record from another table (e.g., users and their profiles).

#### One-to-Many Relationships
- **`get_joined`** (with `nest_joins=True`): Retrieve a single record with all its related records nested within it (e.g., a user and all their blog posts).
- **`get_multi_joined`** (with `nest_joins=True`): Fetch multiple primary records, each with their related records nested (e.g., multiple users and all their blog posts).

For a more detailed explanation, you may check the [joins docs](joins.md#handling-one-to-one-and-one-to-many-joins-in-fastcrud).

### Using aliases

In complex query scenarios, particularly when you need to join a table to itself or perform multiple joins on the same table for different purposes, aliasing becomes crucial. Aliasing allows you to refer to the same table in different contexts with unique identifiers, avoiding conflicts and ambiguity in your queries.

For both `get_joined` and `get_multi_joined` methods, when you need to join the same model multiple times, you can utilize the `alias` parameter within your `JoinConfig` to differentiate between the joins. This parameter expects an instance of `AliasedClass`, which can be created using the `aliased` function from SQLAlchemy (also in fastcrud for convenience).

#### Example: Joining the Same Model Multiple Times

Consider a task management application where tasks have both an owner and an assigned user, represented by the same `UserModel`. To fetch tasks with details of both users, we use aliases to join the `UserModel` twice, distinguishing between owners and assigned users.

Let's start by creating the aliases and passing them to the join configuration. Don't forget to use the alias for `join_on`:

```python hl_lines="4-5 11 15 19 23" title="Join Configurations with Aliases"
from fastcrud import FastCRUD, JoinConfig, aliased

# Create aliases for UserModel to distinguish between the owner and the assigned user
owner_alias = aliased(UserModel, name="owner")
assigned_user_alias = aliased(UserModel, name="assigned_user")

# Configure joins with aliases
joins_config = [
    JoinConfig(
        model=UserModel,
        join_on=Task.owner_id == owner_alias.id,
        join_prefix="owner_",
        schema_to_select=UserSchema,
        join_type="inner",
        alias=owner_alias  # Pass the aliased class instance
    ),
    JoinConfig(
        model=UserModel,
        join_on=Task.assigned_user_id == assigned_user_alias.id,
        join_prefix="assigned_",
        schema_to_select=UserSchema,
        join_type="inner",
        alias=assigned_user_alias  # Pass the aliased class instance
    )
]

# Initialize your FastCRUD instance for TaskModel
task_crud = FastCRUD(TaskModel)

# Fetch tasks with joined user details
tasks = await task_crud.get_multi_joined(
    db=session,
    schema_to_select=TaskSchema,
    joins_config=joins_config,
    offset=0,
    limit=10
)
```

Then just pass this joins_config to `get_multi_joined`:

```python hl_lines="17" title="Passing joins_config to get_multi_joined"
from fastcrud import FastCRUD, JoinConfig, aliased

...

# Configure joins with aliases
joins_config = [
    ...
]

# Initialize your FastCRUD instance for TaskModel
task_crud = FastCRUD(TaskModel)

# Fetch tasks with joined user details
tasks = await task_crud.get_multi_joined(
    db=session,
    schema_to_select=TaskSchema,
    joins_config=joins_config,
    offset=0,
    limit=10
)
```

In this example, `owner_alias` and `assigned_user_alias` are created from `UserModel` to distinguish between the task's owner and the assigned user within the task management system. By using aliases, you can join the same model multiple times for different purposes in your queries, enhancing expressiveness and eliminating ambiguity.

### Many-to-Many Relationships with `get_multi_joined`

FastCRUD simplifies dealing with many-to-many relationships by allowing easy fetch operations with joined models. Here, we demonstrate using `get_multi_joined` to handle a many-to-many relationship between `Project` and `Participant` models, linked through an association table.

**Note on Handling Many-to-Many Relationships:**

When using `get_multi_joined` for many-to-many relationships, it's essential to maintain a specific order in your `joins_config`: 

1. **First**, specify the main table you're querying from.
2. **Next**, include the association table that links your main table to the other table involved in the many-to-many relationship.
3. **Finally**, specify the other table that is connected via the association table.

This order ensures that the SQL joins are structured correctly to reflect the many-to-many relationship and retrieve the desired data accurately.

!!! TIP

    Note that the first one can be the model defined in `FastCRUD(Model)`.

```python
# Fetch projects with their participants via a many-to-many relationship
joins_config = [
    JoinConfig(
        model=ProjectsParticipantsAssociation,
        join_on=Project.id == ProjectsParticipantsAssociation.project_id,
        join_type="inner",
        join_prefix="pp_"
    ),
    JoinConfig(
        model=Participant,
        join_on=ProjectsParticipantsAssociation.participant_id == Participant.id,
        join_type="inner",
        join_prefix="participant_"
    )
]

crud_project = FastCRUD(Project)

projects_with_participants = await project_crud.get_multi_joined(
    db=db,
    schema_to_select=ProjectSchema,
    joins_config=joins_config
)
```

For a more detailed explanation, read [this part of the docs](joins.md#many-to-many-relationships-with-get_multi_joined).


## Enhanced Query Capabilities with Method Chaining

The `select` method in FastCRUD is designed for flexibility, enabling you to build complex queries through method chaining.

### The `select` Method

```python
async def select(
    db: AsyncSession,
    schema_to_select: Optional[type[BaseModel]] = None,
    sort_columns: Optional[Union[str, list[str]]] = None,
    sort_orders: Optional[Union[str, list[str]]] = None,
    **kwargs: Any
) -> Selectable
```

This method constructs a SQL Alchemy `Select` statement, offering optional column selection, filtering, and sorting. It's designed for flexibility, allowing you to chain additional SQLAlchemy methods for even more complex queries.

#### Features:

- **Column Selection**: Specify columns with a Pydantic schema.
- **Sorting**: Define one or more columns for sorting, along with their sort order.
- **Filtering**: Apply filters directly through keyword arguments.
- **Chaining**: Chain with other SQLAlchemy methods for advanced query construction.

#### Usage Example:

```python
stmt = await my_model_crud.select(schema_to_select=MySchema, sort_columns='name', name__like='%example%')
stmt = stmt.where(additional_conditions).limit(10)
results = await db.execute(stmt)
```

This example demonstrates selecting a subset of columns, applying a filter, and chaining additional conditions like `where` and `limit`. Note that `select` returns a `Selectable` object, allowing for further modifications before execution.

## Conclusion

The advanced features of FastCRUD, such as `allow_multiple` and support for advanced filters, empower developers to efficiently manage database records with complex conditions. By leveraging these capabilities, you can build more dynamic, robust, and scalable FastAPI applications that effectively interact with your data model.