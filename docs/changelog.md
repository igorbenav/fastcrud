# FastCRUD Changelog

## Introduction

The Changelog documents all notable changes made to FastCRUD. This includes new features, bug fixes, and improvements. It's organized by version and date, providing a clear history of the library's development.

___
## [0.14.0] - Jul 29, 2024

#### Added
- Type-checking support for SQLModel types by @kdcokenny 🚀
- Returning clause to update operations by @feluelle
- Upsert_multi functionality by @feluelle
- Simplified endpoint configurations by @JakNowy, streamlining path generation and merging pagination functionalities into a unified `_read_items` endpoint, promoting more efficient API structure and usage. Details in https://github.com/igorbenav/fastcrud/pull/105

#### Improved
- Comprehensive tests for paginated retrieval of items, maintaining 100% coverage
- Docker client check before running tests that require Docker by @feluelle

#### Fixed
- Vulnerability associated with an outdated cryptography package
- Return type inconsistency in async session fixtures by @slaarti

#### Documentation Updates
- Cleanup of documentation formatting by @slaarti
- Replacement of the Contributing section in docs with an include to file in repo root by @slaarti
- Correction of links to advanced filters in docstrings by @slaarti
- Backfill of docstring fixes across various modules by @slaarti
- Enhanced filter documentation with new AND and OR clause examples, making complex queries more accessible and understandable.

#### Models and Schemas Enhancements
- Introduction of simple and one-off models (Batch 1) by @slaarti
- Expansion to include models and schemas for Customers, Products, and Orders (Batch 2) by @slaarti

#### Code Refinements
- Resolution of missing type specifications in kwargs by @slaarti
- Collapsed space adjustments for models/schemas in `fast_crud.py` by @slaarti

#### Warnings
- **Deprecation Notice**: `_read_paginated` endpoint is set to be deprecated and merged into `_read_items`. Users are encouraged to transition to the latter, utilizing optional pagination parameters. Full details and usage instructions provided to ensure a smooth transition.
- **Future Changes Alert**: Default endpoint names in `EndpointCreator` are anticipated to be set to empty strings in a forthcoming major release, aligning with simplification efforts. Refer to https://github.com/igorbenav/fastcrud/issues/67 for more information.

#### Detailed Changes
___
##### Simplified Endpoint Configurations

In an effort to streamline FastCRUD’s API, we have reconfigured endpoint paths to avoid redundancy (great work by @JakNowy). This change allows developers to specify empty strings for endpoint names in the `crud_router` setup, which prevents the generation of unnecessary `//` in the paths. The following configurations illustrate how endpoints can now be defined more succinctly:

```python
endpoint_names = {
    "create": "",
    "read": "",
    "update": "",
    "delete": "",
    "db_delete": "",
    "read_multi": "",
    "read_paginated": "get_paginated",
}
```

Moreover, the `_read_paginated` logic has been integrated into the `_read_items` endpoint. This integration means that pagination can now be controlled via `page` and `items_per_page` query parameters, offering a unified method for both paginated and non-paginated reads:

- **Paginated read example**:

```bash
curl -X 'GET' \
  'http://localhost:8000/users/get_multi?page=2&itemsPerPage=10' \
  -H 'accept: application/json'
```

- **Non-paginated read example**:

```bash
curl -X 'GET' \
  'http://localhost:8000/users/get_multi?offset=0&limit=100' \
  -H 'accept: application/json'
```

###### Warnings

- **Deprecation Warning**: The `_read_paginated` endpoint is slated for deprecation. Developers should transition to using `_read_items` with the relevant pagination parameters.
- **Configuration Change Alert**: In a future major release, default endpoint names in `EndpointCreator` will be empty strings by default, as discussed in [Issue #67](https://github.com/igorbenav/fastcrud/issues/67).

###### Advanced Filters Documentation Update

Documentation for advanced filters has been expanded to include comprehensive examples of AND and OR clauses, enhancing the utility and accessibility of complex query constructions.

- **OR clause example**:

```python
# Fetch items priced under $5 or above $20
items = await item_crud.get_multi(
    db=db,
    price__or={'lt': 5, 'gt': 20},
)
```

- **AND clause example**:

```python
# Fetch items priced under $20 and over 2 years of warranty
items = await item_crud.get_multi(
    db=db,
    price__lt=20,
    warranty_years__gt=2,
)
```

___
##### Returning Clauses in Update Operations

###### Description
Users can now retrieve updated records immediately following an update operation. This feature streamlines the process, reducing the need for subsequent retrieval calls and increasing efficiency.

###### Changes
- **Return Columns**: Specify the columns to be returned after the update via the `return_columns` argument.
- **Schema Selection**: Optionally select a Pydantic schema to format the returned data using the `schema_to_select` argument.
- **Return as Model**: Decide if the returned data should be converted into a model using the `return_as_model` argument.
- **Single or None**: Utilize the `one_or_none` argument to ensure that either a single record is returned or none, in case the conditions do not match any records.

These additions are aligned with existing CRUD API functions, enhancing consistency across the library and making the new features intuitive for users.

###### Usage Example

###### Returning Updated Fields

```python
from fastcrud import FastCRUD
from .models.item import Item
from .database import session as db

crud_items = FastCRUD(Item)
updated_item = await crud_items.update(
    db=db,
    object={"price": 9.99},
    price__lt=10,
    return_columns=["price"]
)
# This returns the updated price of the item directly.
```

###### Returning Data as a Model

```python
from fastcrud import FastCRUD
from .models.item import Item
from .schemas.item import ItemSchema
from .database import session as db

crud_items = FastCRUD(Item)
updated_item_schema = await crud_items.update(
    db=db,
    object={"price": 9.99},
    price__lt=10,
    schema_to_select=ItemSchema,
    return_as_model=True
)
# This returns the updated item data formatted as an ItemSchema model.
```

___
##### Bulk Upsert Operations with `upsert_multi`

The `upsert_multi` method provides the ability to perform bulk upsert operations, which are optimized for different SQL dialects.

###### Changes
- **Dialect-Optimized SQL**: Uses the most efficient SQL commands based on the database's SQL dialect.
- **Support for Multiple Dialects**: Includes custom implementations for PostgreSQL, SQLite, and MySQL, with appropriate handling for each's capabilities and limitations.

###### Usage Example

###### Upserting Multiple Records

```python
from fastcrud import FastCRUD
from .models.item import Item
from .schemas.item import ItemCreateSchema, ItemSchema
from .database import session as db

crud_items = FastCRUD(Item)
items = await crud_items.upsert_multi(
    db=db,
    instances=[
        ItemCreateSchema(price=9.99),
    ],
    schema_to_select=ItemSchema,
    return_as_model=True,
)
# This will return the upserted data in the form of ItemSchema.
```

###### Implementation Details

`upsert_multi` handles different database dialects:
- **PostgreSQL**: Uses `ON CONFLICT DO UPDATE`.
- **SQLite**: Utilizes `ON CONFLICT DO UPDATE`.
- **MySQL**: Implements `ON DUPLICATE KEY UPDATE`.

###### Notes
- MySQL and MariaDB do not support certain advanced features used in other dialects, such as returning values directly after an insert or update operation. This limitation is clearly documented to prevent misuse.

#### New Contributors
- @kdcokenny made their first contribution 🌟
- @feluelle made their first contribution 🌟

**Full Changelog**: [View the full changelog](https://github.com/igorbenav/fastcrud/compare/v0.13.1...v0.14.0)


## [0.13.1] - Jun 22, 2024

#### Added
- More Advanced Filters by @JakNowy 🎉

#### Fixed
- Bug where objects with null primary key are returned with all fields set to None in nested joins #102 

#### Detailed Changes
___

### Advanced Filters

FastCRUD supports advanced filtering options, allowing you to query records using operators such as greater than (`__gt`), less than (`__lt`), and their inclusive counterparts (`__gte`, `__lte`). These filters can be used in any method that retrieves or operates on records, including `get`, `get_multi`, `exists`, `count`, `update`, and `delete`.

#### Single parameter filters

Most filter operators require a single string or integer value.

```python
# Fetch items priced above $5
items = await item_crud.get_multi(
    db=db,
    price__gte=5,
)
```

Currently supported single parameter filters are:
- __gt - greater than
- __lt - less than
- __gte - greater than or equal to
- __lte - less than or equal to
- __ne - not equal
- __is - used to test True, False, and None identity
- __is_not - negation of "is"
- __like - SQL "like" search for specific text pattern
- __notlike - negation of "like"
- __ilike - case insensitive "like"
- __notilike - case insensitive "notlike"
- __startswith - text starts with given string
- __endswith - text ends with given string
- __contains - text contains given string
- __match - database-specific match expression

#### Complex parameter filters

Some operators require multiple values. They must be passed as a python tuple, list, or set.

```python
# Fetch items priced between $5 and $20
items = await item_crud.get_multi(
    db=db,
    price__between=(5, 20),
)
```
- __between - between 2 numeric values
- __in - included in
- __not_in - not included in

#### OR parameter filters

More complex OR filters are supported. They must be passed as a dictionary, where each key is a library-supported operator to be used in OR expression and values are what get's passed as the parameter.

```python
# Fetch items priced under $5 or above $20
items = await item_crud.get_multi(
    db=db,
    price__or={'lt': 5, 'gt': 20},
)
```

#### What's Changed
- Missing sqlalchemy operators by [@JakNowy](https://github.com/JakNowy) in https://github.com/igorbenav/fastcrud/pull/85
- Null primary key bug fixed in https://github.com/igorbenav/fastcrud/pull/107

**Full Changelog**: https://github.com/igorbenav/fastcrud/compare/v0.13.0...v0.13.1

## [0.13.0] - May 28, 2024

#### Added
- Filters in Automatic Endpoints 🎉
- One-to-many support in joins
- Upsert method in FastCRUD class by @dubusster 

#### Detailed Changes
##### Using Filters in FastCRUD

FastCRUD provides filtering capabilities, allowing you to filter query results based on various conditions. Filters can be applied to `read_multi` and `read_paginated` endpoints. This section explains how to configure and use filters in FastCRUD.


##### Defining Filters

Filters are either defined using the `FilterConfig` class or just passed as a dictionary. This class allows you to specify default filter values and validate filter types. Here's an example of how to define filters for a model:

```python
from fastcrud import FilterConfig

# Define filter configuration for a model
filter_config = FilterConfig(
    tier_id=None,  # Default filter value for tier_id
    name=None  # Default filter value for name
)
```

And the same thing using a `dict`:
```python
filter_config = {
    "tier_id": None,  # Default filter value for tier_id
    "name": None,  # Default filter value for name
}
```

By using `FilterConfig` you get better error messages.

###### Applying Filters to Endpoints

You can apply filters to your endpoints by passing the `filter_config` to the `crud_router` or `EndpointCreator`. Here's an example:

```python
from fastcrud import crud_router
from yourapp.models import YourModel
from yourapp.schemas import CreateYourModelSchema, UpdateYourModelSchema
from yourapp.database import async_session

# Apply filters using crud_router
app.include_router(
    crud_router(
        session=async_session,
        model=YourModel,
        create_schema=CreateYourModelSchema,
        update_schema=UpdateYourModelSchema,
        filter_config=filter_config,  # Apply the filter configuration
        path="/yourmodel",
        tags=["YourModel"]
    )
)
```

###### Using Filters in Requests

Once filters are configured, you can use them in your API requests. Filters are passed as query parameters. Here's an example of how to use filters in a request to a paginated endpoint:

```http
GET /yourmodel/get_paginated?page=1&itemsPerPage=3&tier_id=1&name=Alice
```

###### Custom Filter Validation

The `FilterConfig` class includes a validator to check filter types. If an invalid filter type is provided, a `ValueError` is raised. You can customize the validation logic by extending the `FilterConfig` class:

```python
from fastcrud import FilterConfig
from pydantic import ValidationError

class CustomFilterConfig(FilterConfig):
    @field_validator("filters")
    def check_filter_types(cls, filters: dict[str, Any]) -> dict[str, Any]:
        for key, value in filters.items():
            if not isinstance(value, (type(None), str, int, float, bool)):
                raise ValueError(f"Invalid default value for '{key}': {value}")
        return filters

try:
    # Example of invalid filter configuration
    invalid_filter_config = CustomFilterConfig(invalid_field=[])
except ValidationError as e:
    print(e)
```

###### Handling Invalid Filter Columns

FastCRUD ensures that filters are applied only to valid columns in your model. If an invalid filter column is specified, a `ValueError` is raised:

```python
try:
    # Example of invalid filter column
    invalid_filter_config = FilterConfig(non_existent_column=None)
except ValueError as e:
    print(e)  # Output: Invalid filter column 'non_existent_column': not found in model
```

___
##### Handling One-to-One and One-to-Many Joins in FastCRUD

FastCRUD provides flexibility in handling one-to-one and one-to-many relationships through `get_joined` and `get_multi_joined` methods, along with the ability to specify how joined data should be structured using both the `relationship_type` (default `one-to-one`) and the `nest_joins` (default `False`) parameters.

###### One-to-One Relationships
- **`get_joined`**: Fetch a single record and its directly associated record (e.g., a user and their profile).
- **`get_multi_joined`** (with `nest_joins=False`): Retrieve multiple records, each linked to a single related record from another table (e.g., users and their profiles).


**Example**

Let's define two tables:

```python
class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    tier_id = Column(Integer, ForeignKey("tier.id"))

class Tier(Base):
    __tablename__ = "tier"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
```

Fetch a user and their tier:

```python
user_tier = await user_crud.get_joined(
    db=db,
    join_model=Tier,
    join_on=User.tier_id == Tier.id,
    join_type="left",
    join_prefix="tier_",
    id=1
)
```

The result will be:

```json
{
    "id": 1,
    "name": "Example",
    "tier_id": 1,
    "tier_name": "Free"
}
```

**One-to-One Relationship with Nested Joins**

To get the joined data in a nested dictionary:

```python
user_tier = await user_crud.get_joined(
    db=db,
    join_model=Tier,
    join_on=User.tier_id == Tier.id,
    join_type="left",
    join_prefix="tier_",
    nest_joins=True,
    id=1
)
```

The result will be:

```json
{
    "id": 1,
    "name": "Example",
    "tier": {
        "id": 1,
        "name": "Free"
    }
}
```


###### One-to-Many Relationships
- **`get_joined`** (with `nest_joins=True`): Retrieve a single record with all its related records nested within it (e.g., a user and all their blog posts).
- **`get_multi_joined`** (with `nest_joins=True`): Fetch multiple primary records, each with their related records nested (e.g., multiple users and all their blog posts).

> [!WARNING]
> When using `nest_joins=True`, the performance will always be a bit worse than when using `nest_joins=False`. For cases where more performance is necessary, consider using `nest_joins=False` and remodeling your database.


**Example**

To demonstrate a one-to-many relationship, let's assume `User` and `Post` tables:

```python
class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary key=True)
    name = Column(String)

class Post(Base):
    __tablename__ = "post"
    id = Column(Integer, primary key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    content = Column(String)
```

Fetch a user and all their posts:

```python
user_posts = await user_crud.get_joined(
    db=db,
    join_model=Post,
    join_on=User.id == Post.user_id,
    join_type="left",
    join_prefix="post_",
    nest_joins=True,
    id=1
)
```

The result will be:

```json
{
    "id": 1,
    "name": "Example User",
    "posts": [
        {
            "id": 101,
            "user_id": 1,
            "content": "First post content"
        },
        {
            "id": 102,
            "user_id": 1,
            "content": "Second post content"
        }
    ]
}
```


## What's Changed
- feat: ✨ add upsert method in FastCRUD class by [@dubusster](https://github.com/dubusster)
- Filters in Automatic Endpoints
- One-to-many support in joins
- tests fixed by @igorbenav
- Using the same session for all tests
- warning added to docs


**Full Changelog**: https://github.com/igorbenav/fastcrud/compare/v0.12.1...v0.13.0

## [0.12.1] - May 10, 2024

#### Added
- Deprecation Warning for dependency handling.

#### Detailed Changes
If you pass a sequence of `params.Depends` type variables to any `*_deps` parameter in `EndpointCreator` and `crud_router`, you'll get a warning. Support will be completely removed in 0.15.0.

**Full Changelog**: https://github.com/igorbenav/fastcrud/compare/v0.12.0...v0.12.1


## [0.12.0] - May 8, 2024

#### Added
- Unpaginated versions of multi-row get methods by @slaarti in #62  🎉
- Nested Join bug fixes
- Dependency handling now working as docs say
- Option to Skip commit in some fastcrud methods
- Docstring example fixes
- `__in` and `__not_in` filters by @JakNowy 🎉
- Fastapi 0.111.0 support

#### Detailed Changes
##### Unpaginated versions of multi-row get methods
Now, if you pass `None` to `limit` in `get_multi` and `get_multi_joined`, you get the whole unpaginated set of data that matches the filters. Use this with caution.

```python
from fastcrud import FastCRUD
from .models.item import Item
from .database import session as db

crud_items = FastCRUD(Item)
items = await crud_items.get_multi(db=db, limit=None)
# this will return all items in the db
```

##### Dependency handling now working as docs say
Now, you may pass dependencies to `crud_router` or `EndpointCreator` as simple functions instead of needing to wrap them in `fastapi.Depends`.

```python
from .dependencies import get_superuser
app.include_router(
    crud_router(
        session=db,
        model=Item,
        create_schema=ItemCreate,
        update_schema=ItemUpdate,
        delete_schema=ItemDelete,
        create_deps=[get_superuser],
        update_deps=[get_superuser],
        delete_deps=[get_superuser],
        path="/item",
        tags=["item"],
    )
)
```

##### Option to Skip commit in some fastcrud methods
For `create`, `update`, `db_delete` and `delete` methods of `FastCRUD`, now you have the option of passing `commit=False` so you don't commit the operations immediately.

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

##### `__in` and `__not_in` filters
You may now pass `__in` and `__not_in` to methods that accept advanced queries:

- `__gt`: greater than,
- `__lt`: less than,
- `__gte`: greater than or equal to,
- `__lte`: less than or equal to,
- `__ne`: not equal,
- `__in`: included in [tuple, list or set],
- `__not_in`: not included in [tuple, list or set].

#### What's Changed
- Add unpaginated versions of multi-row get methods (w/tests) by [@slaarti](https://github.com/slaarti) 🎉
- Join fixes
- Dependencies
- Skip commit
- Docstring fix
- feat: filter __in by [@JakNowy](https://github.com/JakNowy) 🎉
- python support for 0.111.0 added
- version bump in pyproject.toml for 0.12.0

#### New Contributors
* [@slaarti](https://github.com/slaarti) made their first contribution in https://github.com/igorbenav/fastcrud/pull/62 🎉

**Full Changelog**: https://github.com/igorbenav/fastcrud/compare/v0.11.1...v0.12.0


## [0.11.1] - Apr 22, 2024

#### Added
- `one_or_none` parameter to FastCRUD `get` method (default `False`)
- `nest_joins` parameter to FastCRUD `get_joined` and `get_multi_joined` (default `False`)

#### Detailed Changes
##### `get`
By default, the `get` method in `FastCRUD` returns the `first` object matching all the filters it finds.

If you want to ensure the `one_or_none` behavior, you may pass the parameter as `True`:

```python
crud.get(
    async_session, 
    one_or_none=True, 
    category_id=1
)
```

##### `get_joined` and `get_multi_joined`
By default, `FastCRUD` joins all the data and returns it in a single dictionary.
Let's define two tables:
```python
class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    tier_id = Column(Integer, ForeignKey("tier.id"))


class Tier(Base):
    __tablename__ = "tier"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
```

And join them with `FastCRUD`:

```python
user_tier = await user_crud.get_joined(
    db=db,
    model=Tier,
    join_on=User.tier_id == Tier.id,
    join_type="left",
    join_prefix="tier_",,
    id=1
)
```

We'll get:

```javascript
{
    "id": 1,
    "name": "Example",
    "tier_id": 1,
    "tier_name": "Free",
}
```

Now, if you want the joined data in a nested dictionary instead, you may just pass `nest_joins=True`:

```python
user_tier = await user_crud.get_joined(
    db=db,
    model=Tier,
    join_on=User.tier_id == Tier.id,
    join_type="left",
    join_prefix="tier_",
    nest_joins=True,
    id=1,
)
```

And you will get:

```javascript
{
    "id": 1,
    "name": "Example",
    "tier": {
        "id": 1,
        "name": "Free",
    },
}
```

This works for both `get_joined` and `get_multi_joined`.

!!! WARNING
    Note that the final `"_"` in the passed `"tier_"` is stripped.

#### What's Changed
- Reuse of `select` method in `FastCRUD`
- Skip count call when possible
- Add `one_or_none` parameter to FastCRUD `get` method
- Add `nest_joins` parameter to FastCRUD `get_joined` and `get_multi_joined`

#### New Contributors
- [@JakNowy](https://github.com/JakNowy) made their first contribution in PR #51.

**Full Changelog**: [View the full changelog](https://github.com/igorbenav/fastcrud/compare/v0.11.0...v0.11.1)

## [0.11.0] - Apr 7, 2024

#### Added
- Multiple primary keys support, a significant enhancement by @dubusster in #31 🎉.
- Option to disable the count in `get_multi` and `get_multi_joined` methods for performance optimization.
- Fixes for a validation bug when `return_as_model` is set to `True`.
- Resolution of a bug concerning incorrect handling of `db_row` in methods.
- Correction of the `valid_methods` bug, which previously raised the wrong error type.
- Upgrade of `FastAPI` dependency to version `0.111.0`, ensuring compatibility with the latest FastAPI features.
- Achievement of 100% test coverage, with the addition of a workflow and badge to showcase this milestone.
- Inclusion of the changelog within the project documentation, providing a comprehensive history of changes directly to users.

#### Detailed Changes

##### Multiple Primary Keys Support
FastCRUD now accommodates models with multiple primary keys, facilitating more complex database designs. For models defined with more than one primary key, the endpoint creator automatically generates paths reflecting the primary keys' order. This feature extends support to primary keys named differently than `id`, enhancing the flexibility of FastCRUD's routing capabilities.

###### Example:
For a model with multiple primary keys, FastCRUD generates specific endpoints such as `/multi_pk/get/{id}/{uuid}`, accommodating the unique identification needs of complex data models.

##### Optional Count
The `get_multi` and `get_multi_joined` methods now feature an `return_total_count=False` parameter, allowing users to opt-out of receiving the total count in responses. This option can enhance performance by skipping potentially expensive count operations.

###### Behavior:
- By default, `return_total_count=True` is assumed, returning both data and a total count.
- When set to `False`, responses contain only the data array, omitting the total count for efficiency.

#### What's Changed
- Implementation of multiple primary keys support, addressing a significant flexibility requirement for advanced use cases.
- Introduction of optional count retrieval in multi-get methods, optimizing performance by eliminating unnecessary database queries.
- Several critical bug fixes, improving the stability and reliability of FastCRUD.
- Documentation enhancements, including the addition of a changelog section, ensuring users have access to detailed release information.
- Update to FastAPI `0.111.0`, ensuring compatibility with the latest enhancements in the FastAPI ecosystem.
- Achievement of 100% test coverage, marking a significant milestone in the project's commitment to reliability and quality assurance.

#### Relevant Contributors
- [@dubusster](https://github.com/dubusster) made a notable contribution with the implementation of multiple primary keys support in PR #31.

**Full Changelog**: [View the full changelog](https://github.com/igorbenav/fastcrud/compare/v0.10.0...v0.11.0)

## [0.10.0] - Mar 30, 2024

#### Added
- `select` statement functionality, thanks to @dubusster's contribution in PR #28 🚀.
- Support for joined models in the `count` method through the `joins_config` parameter.
- Filters for joined models via the `filters` parameter in `JoinConfig`.
- Type checking workflow integrated with `mypy` alongside fixes for typing issues.
- Linting workflow established with `ruff`.

#### Detailed Changes

##### Select
The `select` method constructs a SQL Alchemy `Select` statement, offering flexibility in column selection, filtering, and sorting. It is designed to chain additional SQLAlchemy methods for complex queries.
[Docs here](https://igorbenav.github.io/fastcrud/usage/crud/#5-select) and [here](https://igorbenav.github.io/fastcrud/advanced/crud/#the-select-method).

###### Features:
- **Column Selection**: Choose columns via a Pydantic schema.
- **Sorting**: Define columns and their order for sorting.
- **Filtering**: Directly apply filters through keyword arguments.
- **Chaining**: Allow for chaining with other SQLAlchemy methods for advanced query construction.

##### Improved Joins
`JoinConfig` enhances FastCRUD queries by detailing join operations between models, offering configurations like model joining, conditions, prefixes, column selection through schemas, join types, aliases, and direct filtering. [Docs here](https://igorbenav.github.io/fastcrud/advanced/joins/).

#### Applying Joins in FastCRUD Methods
Detailed explanations and examples are provided for using joins in `count`, `get_joined`, and `get_multi_joined` methods to achieve complex data retrieval, including handling of many-to-many relationships.

#### What's Changed
- New `select` statement functionality added.
- Documentation and method improvements for select and joins.
- Integration of type checking and linting workflows.
- Version bump in pyproject.toml.

#### New Contributors
- [@dubusster](https://github.com/dubusster) made their first contribution in PR #28.

**Full Changelog**: [View the full changelog](https://github.com/igorbenav/fastcrud/compare/v0.9.1...v0.10.0)

___

## [0.9.1] - Mar 19, 2024

#### Added
- Enhanced `get_joined` and `get_multi_joined` methods to support aliases, enabling multiple joins on the same model. This improvement addresses issue #27.

#### Detailed Changes

##### Alias Support for Complex Joins
With the introduction of alias support, `get_joined` and `get_multi_joined` methods now allow for more complex queries, particularly beneficial in scenarios requiring self-joins or multiple joins on the same table. Aliases help to avoid conflicts and ambiguity by providing unique identifiers for the same model in different join contexts. [Docs here](https://igorbenav.github.io/fastcrud/advanced/joins/#complex-joins-using-joinconfig).

###### Example: Multiple Joins with Aliases
To demonstrate the use of aliases, consider a task management system where tasks are associated with both an owner and an assigned user from the same `UserModel`. Aliases enable joining the `UserModel` twice under different contexts - as an owner and an assigned user. This example showcases how to set up aliases using the `aliased` function and incorporate them into your `JoinConfig` for clear and conflict-free query construction. [Docs here](https://igorbenav.github.io/fastcrud/advanced/crud/#example-joining-the-same-model-multiple-times).

#### What's Changed
- Introduction of aliases in joins, improving query flexibility and expressiveness, as detailed by @igorbenav in PR #29.

**Full Changelog**: [View the full changelog](https://github.com/igorbenav/fastcrud/compare/v0.9.0...v0.9.1)

___

## [0.9.0] - Mar 14, 2024

#### Added
- Enhanced `get_joined` and `get_multi_joined` methods now support handling joins with multiple models.

#### Detailed Changes

##### Multi-Model Join Capabilities
The `get_joined` and `get_multi_joined` methods have been upgraded to accommodate joins involving multiple models. This functionality is facilitated through the `joins_config` parameter, allowing for the specification of multiple `JoinConfig` instances. Each instance represents a unique join configuration, broadening the scope for complex data relationship management within FastCRUD. [Docs here](https://igorbenav.github.io/fastcrud/advanced/joins/).

###### Example: Multi-Model Join
A practical example involves retrieving users alongside their corresponding tier and department details. By configuring `joins_config` with appropriate `JoinConfig` instances for the `Tier` and `Department` models, users can efficiently gather comprehensive data across related models, enhancing data retrieval operations' depth and flexibility.

!!! WARNING
    An error will occur if both single join parameters and `joins_config` are used simultaneously. It's crucial to ensure that your join configurations are correctly set to avoid conflicts.

#### What's Changed
- Introduction of multi-model join support in `get_joined` and `get_multi_joined`, enabling more complex and detailed data retrieval strategies.
- Several minor updates and fixes, including package import corrections and `pyproject.toml` updates, to improve the library's usability and stability.

#### New Contributors
- [@iridescentGray](https://github.com/iridescentGray)

**Full Changelog**: [View the full changelog](https://github.com/igorbenav/fastcrud/compare/v0.8.0...v0.9.0)

___

## [0.8.0] - Mar 4, 2024

#### Added
- Feature to customize names of auto-generated endpoints using the `endpoint_names` parameter, applicable in both `crud_router` function and `EndpointCreator`.

#### Detailed Changes

##### Custom Endpoint Naming
The introduction of the `endpoint_names` parameter offers flexibility in defining endpoint names for CRUD operations. This enhancement caters to the need for more descriptive or project-specific naming conventions, enabling developers to align the API's interface with their domain language or organizational standards. 

###### Example: Customizing Endpoint Names with `crud_router`
Customizing endpoint names is straightforward with the `crud_router` function. By providing a dictionary mapping CRUD operation names to desired endpoint names, developers can easily tailor their API's paths to fit their application's unique requirements.

###### Example: Customizing Endpoint Names with `EndpointCreator`
Similarly, when using the `EndpointCreator`, the `endpoint_names` parameter allows for the same level of customization, ensuring consistency across different parts of the application or service.

!!! TIP

    It's not necessary to specify all endpoint names; only those you wish to change need to be included in the `endpoint_names` dictionary. This flexibility ensures minimal configuration effort for maximum impact.

#### What's Changed
- Enhanced endpoint customization capabilities through `endpoint_names` parameter, supporting a more tailored and intuitive API design.
- Documentation updates to guide users through the process of customizing endpoint names.

___

## [0.7.0] - Feb 20, 2024

#### Added
- The `get_paginated` endpoint for retrieving items with pagination support.
- The `paginated` module to offer utility functions for pagination.

#### Detailed Changes

##### `get_paginated` Endpoint
This new endpoint enhances data retrieval capabilities by introducing pagination, an essential feature for handling large datasets efficiently. It supports customizable query parameters for page number and items per page, facilitating flexible data access patterns. [Docs here](https://igorbenav.github.io/fastcrud/advanced/endpoint/#read-paginated).

###### Features:
- **Endpoint and Method**: A `GET` request to `/get_paginated`.
- **Query Parameters**: Includes `page` for the page number and `itemsPerPage` for controlling the number of items per page.
- **Example Usage**: Demonstrated with a request for retrieving items with specified pagination settings.

##### `paginated` Module
The introduction of the `paginated` module brings two key utility functions, `paginated_response` and `compute_offset`, which streamline the implementation of paginated responses in the application.

###### Functions:
- **paginated_response**: Constructs a paginated response based on the input data, page number, and items per page.
- **compute_offset**: Calculates the offset for database queries, based on the current page number and the number of items per page.

#### What's Changed
- Deployment of pagination functionality, embodied in the `get_paginated` endpoint and the `paginated` module, to facilitate efficient data handling and retrieval.

**Full Changelog**: [View the full changelog](https://github.com/igorbenav/fastcrud/compare/v0.6.0...v0.7.0)

___

## [0.6.0] - Feb 11, 2024

#### Added
- The ability to use a custom `updated_at` column name in models.
- Making the passing of the `crud` parameter to `crud_router` and `EndpointCreator` optional.
- Inclusion of exceptions in the `http_exceptions` module within the broader `exceptions` module for better organization and accessibility.

#### Detailed Changes

##### Custom `updated_at` Column
FastCRUD now supports the customization of the `updated_at` column name, providing flexibility for applications with different database schema conventions or naming practices. [Docs here](https://igorbenav.github.io/fastcrud/advanced/endpoint/#using-endpointcreator-and-crud_router-with-custom-soft-delete-or-update-columns).

###### Example Configuration:
The example demonstrates how to specify a custom column name for `updated_at` when setting up the router for an endpoint, allowing for seamless integration with existing database schemas.

#### What's Changed
- Introduction of features enhancing flexibility and usability, such as custom `updated_at` column names and the optional CRUD parameter in routing configurations.

**Full Changelog**: [View the full changelog](https://github.com/igorbenav/fastcrud/compare/v0.5.0...v0.6.0)

___

## [0.5.0] - Feb 3, 2024

#### Added 
- Advanced filters inspired by Django ORM for enhanced querying capabilities.
- Optional bulk operations for update and delete methods.
- Custom soft delete mechanisms integrated into `FastCRUD`, `EndpointCreator`, and `crud_router`.
- Comprehensive test suite for the newly introduced features.

#### Detailed Changes

##### Advanced Filters
The advanced filtering system allows for sophisticated querying with support for operators like `__gt`, `__lt`, `__gte`, and `__lte`, applicable across various CRUD operations. This feature significantly enhances the flexibility and power of data retrieval and manipulation within FastCRUD. [Docs here](https://igorbenav.github.io/fastcrud/advanced/crud/#advanced-filters).

###### Examples:
- Utilization of advanced filters for precise data fetching and aggregation.
- Implementation examples for fetching records within specific criteria and counting records based on date ranges.

##### Custom Soft Delete Mechanisms
FastCRUD's soft delete functionality now supports customization, allowing developers to specify alternative column names for `is_deleted` and `deleted_at` fields. This adaptation enables seamless integration with existing database schemas that employ different naming conventions for soft deletion tracking. [Docs here](https://igorbenav.github.io/fastcrud/advanced/endpoint/#using-endpointcreator-and-crud_router-with-custom-soft-delete-or-update-columns).

###### Example Configuration:
- Setting up `crud_router` with custom soft delete column names, demonstrating the flexibility in adapting FastCRUD to various database schema requirements.

##### Bulk Operations
The introduction of optional bulk operations for updating and deleting records provides a more efficient way to handle large datasets, enabling mass modifications or removals with single method calls. This feature is particularly useful for applications that require frequent bulk data management tasks. [Docs here](https://igorbenav.github.io/fastcrud/advanced/crud/#allow-multiple-updates-and-deletes).

###### Examples:
- Demonstrating bulk update and delete operations, highlighting the capability to apply changes to multiple records based on specific criteria.

#### What's Changed
- Addition of advanced filters, bulk operations, and custom soft delete functionalities.

#### New Contributors
- [@YuriiMotov](https://github.com/YuriiMotov)

**Full Changelog**: [View the full changelog](https://github.com/igorbenav/fastcrud/compare/v0.4.0...v0.5.0)

___

## [0.4.0] - Jan 31, 2024

### Added 
- Documentation and tests for SQLModel support.
- `py.typed` file for better typing support.

### Detailed

Check the [docs for SQLModel support](https://igorbenav.github.io/fastcrud/sqlmodel/).

### What's Changed
- SQLModel support.

**Full Changelog**: [View the full changelog](https://github.com/igorbenav/fastcrud/compare/v0.3.0...v0.4.0)

___

## [0.3.0] - Jan 28, 2024

### Added
- The `CustomEndpointCreator` for advanced route creation and customization.
- The ability to selectively include or exclude CRUD operations in the `crud_router` using `included_methods` and `deleted_methods`.
- Comprehensive tests for the new features.
- Detailed documentation on utilizing the `CustomEndpointCreator` and selectively including or excluding endpoints.

### CustomEndpointCreator
This feature introduces the capability to extend the `EndpointCreator` class, enabling developers to define custom routes and incorporate complex logic into API endpoints. The documentation has been updated to include detailed examples and guidelines on implementing and using `CustomEndpointCreator` in projects. [Docs here](https://igorbenav.github.io/fastcrud/advanced/endpoint/#creating-a-custom-endpointcreator).

### Selective CRUD Operations
The `crud_router` function has been enhanced with `included_methods` and `deleted_methods` parameters, offering developers precise control over which CRUD methods are included or excluded when configuring routers. This addition provides flexibility in API design, allowing for the creation of tailored endpoint setups that meet specific project requirements. [Docs here](https://igorbenav.github.io/fastcrud/advanced/endpoint/#selective-crud-operations).

## Detailed Changes

### Extending EndpointCreator
Developers can now create a subclass of `EndpointCreator` to define custom routes or override existing methods, adding a layer of flexibility and customization to FastCRUD's routing capabilities.

#### Creating a Custom EndpointCreator
An example demonstrates how to subclass `EndpointCreator` and add custom routes or override existing methods, further illustrating how to incorporate custom endpoint logic and route configurations into the FastAPI application.

### Adding Custom Routes
The process involves overriding the `add_routes_to_router` method to include both standard CRUD routes and custom routes, showcasing how developers can extend FastCRUD's functionality to suit their application's unique needs.

### Using the Custom EndpointCreator
An example highlights how to use the custom `EndpointCreator` with `crud_router`, specifying selective methods to be included in the router setup, thereby demonstrating the practical application of custom endpoint creation and selective method inclusion.

### Selective CRUD Operations
Examples for using `included_methods` and `deleted_methods` illustrate how to specify exactly which CRUD methods should be included or excluded when setting up the router, offering developers precise control over their API's exposed functionality.

!!! WARNING
    Providing both `included_methods` and `deleted_methods` will result in a ValueError.

**Full Changelog**: [View the full changelog](https://github.com/igorbenav/fastcrud/compare/v0.2.1...v0.3.0)

___

## [0.2.1] - Jan 27, 2024

### What's Changed
- Improved type hints across the codebase, enhancing the clarity and reliability of type checking within FastCRUD.
- Documentation has been thoroughly updated and refined, including fixes for previous inaccuracies and the addition of more detailed explanations and examples.
- Descriptions have been added to automatically generated endpoints, making the API documentation more informative and user-friendly.

**Full Changelog**: [View the full changelog](https://github.com/igorbenav/fastcrud/compare/v0.2.0...v0.2.1)

___

## [0.2.0] - Jan 25, 2024

### Added
- [Docs Published!](https://igorbenav.github.io/fastcrud/)

___

## [0.1.5] - Jan 24, 2024

Readme updates, pyproject requirements

___

## [0.1.2] - Jan 23, 2024

First public release.
