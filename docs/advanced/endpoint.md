# Advanced Use of EndpointCreator

In FastCRUD, the `EndpointCreator` class simplifies the process of creating standard CRUD endpoints. However, for more advanced use cases, you might want to add custom routes that go beyond the basic CRUD operations. This can be achieved by extending the `EndpointCreator` class.

## Selective CRUD Operations

You can control which CRUD operations are exposed by using `included_methods` and `deleted_methods`. These parameters allow you to specify exactly which CRUD methods should be included or excluded when setting up the router.

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

## Conclusion

The `EndpointCreator` class in FastCRUD offers flexibility and control over CRUD operations and custom endpoint creation. By extending this class or using the `included_methods` and `deleted_methods` parameters, you can tailor your API's functionality to your specific requirements, ensuring a more customizable and streamlined experience.
