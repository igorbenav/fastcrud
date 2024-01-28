
# Advanced Use of EndpointCreator

In FastCRUD, the `EndpointCreator` class simplifies the process of creating standard CRUD endpoints. However, for more advanced use cases, you might want to add custom routes that go beyond the basic CRUD operations. This can be achieved by extending the `EndpointCreator` class.

## Selective CRUD Operations

You can control which CRUD operations are exposed by using `included_methods` and `deleted_methods`. These parameters allow you to specify exactly which CRUD methods should be included or excluded when setting up the router.

### Using `included_methods`
Using `included_methods` you may define exactly the methods you want to be included.

```python hl_lines="10"
# Using crud_router with selective CRUD methods
my_router = crud_router(
    session=async_session,
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
    session=async_session,
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
    session=async_session,
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

## Conclusion

The `EndpointCreator` class in FastCRUD offers flexibility and control over CRUD operations and custom endpoint creation. By extending this class or using the `included_methods` and `deleted_methods` parameters, you can tailor your API's functionality to your specific requirements, ensuring a more customizable and streamlined experience.
