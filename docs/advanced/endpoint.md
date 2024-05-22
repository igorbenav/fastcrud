# Advanced Use of EndpointCreator

## Available Automatic Endpoints
FastCRUD automates the creation of CRUD (Create, Read, Update, Delete) endpoints for your FastAPI application. Here's an overview of the available automatic endpoints and how they work:

### Create

- **Endpoint**: `/create`
- **Method**: `POST`
- **Description**: Creates a new item in the database.
- **Request Body**: JSON object based on the `create_schema`.
- **Example Request**: `POST /yourmodel/create` with JSON body.

### Read

- **Endpoint**: `/get/{id}`
- **Method**: `GET`
- **Description**: Retrieves a single item by its ID.
- **Path Parameters**: `id` - The ID of the item to retrieve.
- **Example Request**: `GET /yourmodel/get/1`.
- **Example Return**:
```javascript
{
    "id": 1,
    "name": "Item 1",
    "description": "Description of item 1"
}
```

### Read Multiple

- **Endpoint**: `/get_multi`
- **Method**: `GET`
- **Description**: Retrieves multiple items with optional pagination.
- **Query Parameters**:
  - `offset` (optional): The offset from where to start fetching items.
  - `limit` (optional): The maximum number of items to return.
- **Example Request**: `GET /yourmodel/get_multi?offset=3&limit=4`.
- **Example Return**:
```javascript
{
  "data": [
    {"id": 4, "name": "Item 4", "description": "Description of item 4"},
    {"id": 5, "name": "Item 5", "description": "Description of item 5"},
    {"id": 6, "name": "Item 6", "description": "Description of item 6"},
    {"id": 7, "name": "Item 7", "description": "Description of item 7"}
  ],
  "total_count": 50
}

```

### Read Paginated

- **Endpoint**: `/get_paginated`
- **Method**: `GET`
- **Description**: Retrieves multiple items with pagination.
- **Query Parameters**:
  - `page`: The page number, starting from 1.
  - `itemsPerPage`: The number of items per page.
- **Example Request**: `GET /yourmodel/get_paginated?page=1&itemsPerPage=3`.
- **Example Return**:
```javascript
{
  "data": [
    {"id": 1, "name": "Item 1", "description": "Description of item 1"},
    {"id": 2, "name": "Item 2", "description": "Description of item 2"},
    {"id": 3, "name": "Item 3", "description": "Description of item 3"}
  ],
  "total_count": 50,
  "has_more": true,
  "page": 1,
  "items_per_page": 3
}
```

### Update

- **Endpoint**: `/update/{id}`
- **Method**: `PATCH`
- **Description**: Updates an existing item by its ID.
- **Path Parameters**: `id` - The ID of the item to update.
- **Request Body**: JSON object based on the `update_schema`.
- **Example Request**: `PATCH /yourmodel/update/1` with JSON body.
- **Example Return**: `None`

### Delete

- **Endpoint**: `/delete/{id}`
- **Method**: `DELETE`
- **Description**: Deletes (soft delete if configured) an item by its ID.
- **Path Parameters**: `id` - The ID of the item to delete.
- **Example Request**: `DELETE /yourmodel/delete/1`.
- **Example Return**: `None`

### DB Delete (Hard Delete)

- **Endpoint**: `/db_delete/{id}` (Available if a `delete_schema` is provided)
- **Method**: `DELETE`
- **Description**: Permanently deletes an item by its ID, bypassing the soft delete mechanism.
- **Path Parameters**: `id` - The ID of the item to hard delete.
- **Example Request**: `DELETE /yourmodel/db_delete/1`.
- **Example Return**: `None`

## Selective CRUD Operations

You can control which CRUD operations are exposed by using `included_methods` and `deleted_methods`. These parameters allow you to specify exactly which CRUD methods should be included or excluded when setting up the router. By default, all CRUD endpoints are included.

### Using `included_methods`

Using `included_methods` you may define exactly the methods you want to be included.

```python hl_lines="10"
# Using crud_router with selective CRUD methods
my_router = crud_router(
    session=get_session,
    model=MyModel,
    crud=FastCRUD(MyModel),
    create_schema=CreateMyModel,
    update_schema=UpdateMyModel,
    path="/mymodel",
    tags=["MyModel"],
    included_methods=["create", "read", "update"]  # Only these methods will be included
)

app.include_router(my_router)
```

### Using `deleted_methods`

Using `deleted_methods` you define the methods that will not be included.

```python hl_lines="10"
# Using crud_router with selective CRUD methods
my_router = crud_router(
    session=get_session,
    model=MyModel,
    crud=FastCRUD(MyModel),
    create_schema=CreateMyModel,
    update_schema=UpdateMyModel,
    path="/mymodel",
    tags=["MyModel"],
    deleted_methods=["update", "delete"]  # All but these methods will be included
)

app.include_router(my_router)
```

!!! WARNING

        If `included_methods` and `deleted_methods` are both provided, a ValueError will be raised.

## Customizing Endpoint Names

You can customize the names of the auto generated endpoints by passing an `endpoint_names` dictionary when initializing the `EndpointCreator` or calling the `crud_router` function. This dictionary should map the CRUD operation names (`create`, `read`, `update`, `delete`, `db_delete`, `read_multi`, `read_paginated`) to your desired endpoint names.

### Example: Using `crud_router`

Here's how you can customize endpoint names using the `crud_router` function:

```python
from fastapi import FastAPI
from yourapp.crud import crud_router
from yourapp.models import YourModel
from yourapp.schemas import CreateYourModelSchema, UpdateYourModelSchema
from yourapp.database import async_session

app = FastAPI()

# Custom endpoint names
custom_endpoint_names = {
    "create": "add",
    "read": "fetch",
    "update": "modify",
    "delete": "remove",
    "read_multi": "list",
    "read_paginated": "paginate"
}

# Setup CRUD router with custom endpoint names
app.include_router(crud_router(
    session=async_session,
    model=YourModel,
    create_schema=CreateYourModelSchema,
    update_schema=UpdateYourModelSchema,
    path="/yourmodel",
    tags=["YourModel"],
    endpoint_names=custom_endpoint_names
))
```

In this example, the standard CRUD endpoints will be replaced with `/add`, `/fetch/{id}`, `/modify/{id}`, `/remove/{id}`, `/list`, and `/paginate`.

### Example: Using `EndpointCreator`

If you are using `EndpointCreator`, you can also pass the `endpoint_names` dictionary to customize the endpoint names similarly:

```python
# Custom endpoint names
custom_endpoint_names = {
    "create": "add_new",
    "read": "get_single",
    "update": "change",
    "delete": "erase",
    "db_delete": "hard_erase",
    "read_multi": "get_all",
    "read_paginated": "get_page"
}

# Initialize and use the custom EndpointCreator
endpoint_creator = EndpointCreator(
    session=async_session,
    model=YourModel,
    create_schema=CreateYourModelSchema,
    update_schema=UpdateYourModelSchema,
    path="/yourmodel",
    tags=["YourModel"],
    endpoint_names=custom_endpoint_names
)

endpoint_creator.add_routes_to_router()
app.include_router(endpoint_creator.router)
```

!!! TIP

    You only need to pass the names of the endpoints you want to change in the endpoint_names dict.

## Extending EndpointCreator

You can create a subclass of `EndpointCreator` and override or add new methods to define custom routes. Here's an example:

### Creating a Custom EndpointCreator

```python hl_lines="3 4"
from fastcrud import EndpointCreator

# Define the custom EndpointCreator
class MyCustomEndpointCreator(EndpointCreator):
    # Add custom routes or override existing methods
    def _custom_route(self):
        async def custom_endpoint():
            # Custom endpoint logic
            return {"message": "Custom route"}

        return custom_endpoint

    # override add_routes_to_router to also add the custom routes
    def add_routes_to_router(self, ...):
        # First, add standard CRUD routes if you want them
        super().add_routes_to_router(...)

        # Now, add custom routes
        self.router.add_api_route(
            path="/custom",
            endpoint=self._custom_route(),
            methods=["GET"],
            tags=self.tags,
            # Other parameters as needed
        )
```

### Adding custom routes

```python hl_lines="5-9"
from fastcrud import EndpointCreator

# Define the custom EndpointCreator
class MyCustomEndpointCreator(EndpointCreator):
    # Add custom routes or override existing methods
    def _custom_route(self):
        async def custom_endpoint():
            # Custom endpoint logic
            return {"message": "Custom route"}

        return custom_endpoint

    # override add_routes_to_router to also add the custom routes
    def add_routes_to_router(self, ...):
        # First, add standard CRUD routes if you want them
        super().add_routes_to_router(...)

        # Now, add custom routes
        self.router.add_api_route(
            path="/custom",
            endpoint=self._custom_route(),
            methods=["GET"],
            tags=self.tags,
            # Other parameters as needed
        )
```

### Overriding `add_routes_to_router`

```python hl_lines="13-25"
from fastcrud import EndpointCreator

# Define the custom EndpointCreator
class MyCustomEndpointCreator(EndpointCreator):
    # Add custom routes or override existing methods
    def _custom_route(self):
        async def custom_endpoint():
            # Custom endpoint logic
            return {"message": "Custom route"}

        return custom_endpoint

    # override add_routes_to_router to also add the custom routes
    def add_routes_to_router(self, ...):
        # First, add standard CRUD routes if you want them
        super().add_routes_to_router(...)

        # Now, add custom routes
        self.router.add_api_route(
            path="/custom",
            endpoint=self._custom_route(),
            methods=["GET"],
            tags=self.tags,
            # Other parameters as needed
        )
```

### Using the Custom EndpointCreator

```python hl_lines="6 12 18"
# Assuming MyCustomEndpointCreator was created

...

# Use the custom EndpointCreator with crud_router
my_router = crud_router(
    session=get_session,
    model=MyModel,
    crud=FastCRUD(MyModel),
    create_schema=CreateMyModel,
    update_schema=UpdateMyModel,
    endpoint_creator=MyCustomEndpointCreator,
    path="/mymodel",
    tags=["MyModel"],
    included_methods=["create", "read", "update"]  # Including selective methods
)

app.include_router(my_router)
```

## Custom Soft Delete

To implement custom soft delete columns using `EndpointCreator` and `crud_router` in FastCRUD, you need to specify the names of the columns used for indicating deletion status and the deletion timestamp in your model. FastCRUD provides flexibility in handling soft deletes by allowing you to configure these column names directly when setting up CRUD operations or API endpoints.

Here's how to specify custom soft delete columns when utilizing `EndpointCreator` and `crud_router`:

### Defining Models with Custom Soft Delete Columns

First, ensure your SQLAlchemy model is equipped with the custom soft delete columns. Here's an example model with custom columns for soft deletion:

```python
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class MyModel(Base):
    __tablename__ = 'my_model'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    archived = Column(Boolean, default=False)  # Custom soft delete column
    archived_at = Column(DateTime)  # Custom timestamp column for soft delete
```

### Using `EndpointCreator` and `crud_router` with Custom Soft Delete or Update Columns

When initializing `crud_router` or creating a custom `EndpointCreator`, you can pass the names of your custom soft delete columns through the `FastCRUD` initialization. This informs FastCRUD which columns to check and update for soft deletion operations.

Here's an example of using `crud_router` with custom soft delete columns:

```python hl_lines="11-14 20"
from fastapi import FastAPI
from fastcrud import FastCRUD, crud_router
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI()

# Assuming async_session is your AsyncSession generator
# and MyModel is your SQLAlchemy model

# Initialize FastCRUD with custom soft delete columns
my_model_crud = FastCRUD(MyModel,
                         is_deleted_column='archived',  # Custom 'is_deleted' column name
                         deleted_at_column='archived_at'  # Custom 'deleted_at' column name
                        )

# Setup CRUD router with the FastCRUD instance
app.include_router(crud_router(
    session=async_session,
    model=MyModel,
    crud=my_model_crud,
    create_schema=CreateMyModelSchema,
    update_schema=UpdateMyModelSchema,
    delete_schema=DeleteMyModelSchema,
    path="/mymodel",
    tags=["MyModel"]
))
```

You may also directly pass the names of the columns to crud_router or EndpointCreator:

```python hl_lines="9 10"
app.include_router(endpoint_creator(
    session=async_session,
    model=MyModel,
    create_schema=CreateMyModelSchema,
    update_schema=UpdateMyModelSchema,
    delete_schema=DeleteMyModelSchema,
    path="/mymodel",
    tags=["MyModel"],
    is_deleted_column='archived',
    deleted_at_column='archived_at'
))
```

You can also customize your `updated_at` column:

```python hl_lines="9"
app.include_router(endpoint_creator(
    session=async_session,
    model=MyModel,
    create_schema=CreateMyModelSchema,
    update_schema=UpdateMyModelSchema,
    delete_schema=DeleteMyModelSchema,
    path="/mymodel",
    tags=["MyModel"],
    updated_at_column='date_updated'
))
```

This setup ensures that the soft delete functionality within your application utilizes the `archived` and `archived_at` columns for marking records as deleted, rather than the default `is_deleted` and `deleted_at` fields.

By specifying custom column names for soft deletion, you can adapt FastCRUD to fit the design of your database models, providing a flexible solution for handling deleted records in a way that best suits your application's needs.

## Using Filters in FastCRUD

FastCRUD provides filtering capabilities, allowing you to filter query results based on various conditions. Filters can be applied to `read_multi` and `read_paginated` endpoints. This section explains how to configure and use filters in FastCRUD.

### Defining Filters

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

### Applying Filters to Endpoints

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

### Using Filters in Requests

Once filters are configured, you can use them in your API requests. Filters are passed as query parameters. Here's an example of how to use filters in a request to a paginated endpoint:

```http
GET /yourmodel/get_paginated?page=1&itemsPerPage=3&tier_id=1&name=Alice
```

### Custom Filter Validation

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

### Handling Invalid Filter Columns

FastCRUD ensures that filters are applied only to valid columns in your model. If an invalid filter column is specified, a `ValueError` is raised:

```python
try:
    # Example of invalid filter column
    invalid_filter_config = FilterConfig(non_existent_column=None)
except ValueError as e:
    print(e)  # Output: Invalid filter column 'non_existent_column': not found in model
```


## Conclusion

The `EndpointCreator` class in FastCRUD offers flexibility and control over CRUD operations and custom endpoint creation. By extending this class or using the `included_methods` and `deleted_methods` parameters, you can tailor your API's functionality to your specific requirements, ensuring a more customizable and streamlined experience.
