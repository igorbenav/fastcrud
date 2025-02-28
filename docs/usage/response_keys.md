# Response Key Configuration

FastCRUD allows you to customize the key used for list responses through the `multi_response_key` parameter. This guide demonstrates both default and custom configurations.

## Default Configuration

By default, FastCRUD uses `"data"` as the response key:

```python
from fastcrud import FastCRUD
from .models import MyModel
from .database import session as db

# Default initialization
crud = FastCRUD(MyModel)

# Get multiple items
result = await crud.get_multi(db, limit=2)
```

Response structure:
```json
{
    "data": [
        {"id": 1, "name": "Item 1"},
        {"id": 2, "name": "Item 2"}
    ],
    "total_count": 10,
    "has_more": true,
    "page": 1,
    "items_per_page": 2
}
```

## Custom Response Key

You can customize the response key using `multi_response_key`:

```python
from fastcrud import FastCRUD
from .models import MyModel
from .database import session as db

# Custom response key initialization
crud = FastCRUD(MyModel, multi_response_key="items")

# Get multiple items
result = await crud.get_multi(db, limit=2)
```

Response structure:
```json
{
    "items": [
        {"id": 1, "name": "Item 1"},
        {"id": 2, "name": "Item 2"}
    ],
    "total_count": 10,
    "has_more": true,
    "page": 1,
    "items_per_page": 2
}
```

## Using with EndpointCreator

When using `EndpointCreator`, the response key configuration is automatically inherited:

```python
from fastcrud import FastCRUD, EndpointCreator
from .models import MyModel
from .schemas import CreateSchema, UpdateSchema

# Custom response key
crud = FastCRUD(MyModel, multi_response_key="items")

endpoint_creator = EndpointCreator(
    session=async_session,
    model=MyModel,
    create_schema=CreateSchema,
    update_schema=UpdateSchema,
    crud=crud  # The response key setting is inherited
)
```

The API endpoints created will use the configured response key in their responses.

## Response Models

When using Pydantic response models with custom response keys, make sure to define them accordingly:

```python
from pydantic import BaseModel

# For default "data" key
class DefaultResponse(BaseModel):
    data: list[YourSchema]
    total_count: int
    has_more: bool
    page: int | None = None
    items_per_page: int | None = None

# For custom "items" key
class CustomResponse(BaseModel):
    items: list[YourSchema]
    total_count: int
    has_more: bool
    page: int | None = None
    items_per_page: int | None = None
```

!!! note
    FastCRUD automatically handles the response model creation when using `EndpointCreator` or `crud_router`, 
    so manual response model definition is only needed for custom implementations.