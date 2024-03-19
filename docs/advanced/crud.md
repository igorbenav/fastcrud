
# Advanced Use of FastCRUD

FastCRUD offers a flexible and powerful approach to handling CRUD operations in FastAPI applications, leveraging the SQLAlchemy ORM. Beyond basic CRUD functionality, FastCRUD provides advanced features like `allow_multiple` for updates and deletes, and support for advanced filters (e.g., less than, greater than). These features enable more complex and fine-grained data manipulation and querying capabilities.

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

#### Counting Records

```python
# Count items added in the last month
item_count = await item_crud.count(
    db=db,
    added_at__gte=datetime.datetime.now() - datetime.timedelta(days=30)
)
```

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

## Conclusion

The advanced features of FastCRUD, such as `allow_multiple` and support for advanced filters, empower developers to efficiently manage database records with complex conditions. By leveraging these capabilities, you can build more dynamic, robust, and scalable FastAPI applications that effectively interact with your data model.