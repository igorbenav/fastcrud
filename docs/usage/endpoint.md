# Automatic Endpoint Creation with crud_router

This section of the documentation explains how to use the `crud_router` utility function from the FastCRUD package for automatic endpoint creation in a FastAPI application. The `crud_router` simplifies the process of creating standard CRUD (Create, Read, Update, Delete) endpoints for your models.

## Prerequisites

Before proceeding, ensure you have FastAPI and FastCRUD installed in your environment. FastCRUD streamlines interactions with the database using SQLAlchemy models and Pydantic schemas.

!!! WARNING
        For now, your primary column in the database model must be named `id`. 

___

## Using `crud_router`

### Step 1: Define Your Model and Schema

First, define your SQLAlchemy model and corresponding Pydantic schemas for creating and updating data.

```python title="models/item.py"
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import DeclarativeBase
from pydantic import BaseModel

class Base(DeclarativeBase):
    pass

class Item(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)

class ItemCreateSchema(BaseModel):
    name: str
    description: str

class ItemUpdateSchema(BaseModel):
    name: str
    description: str
```

### Step 2: Set Up FastAPI and FastCRUD

Next, set up your FastAPI application and FastCRUD instances. This involves configuring the database connection and creating a CRUD instance for your model.

```python
from fastapi import FastAPI
from fastcrud import FastCRUD, crud_router
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Database setup (Async SQLAlchemy)
DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# FastAPI app
app = FastAPI()

# CRUD operations setup
crud = FastCRUD(Item)

# CRUD router setup
item_router = crud_router(
    session=async_session,
    model=Item,
    crud=crud,
    create_schema=ItemCreateSchema,
    update_schema=ItemUpdateSchema,
    path="/items",
    tags=["Items"]
)

app.include_router(item_router)
```

## Usage and Testing

Once the application is running, you can test the automatically created endpoints using tools like Swagger UI, which FastAPI provides by default. The endpoints for creating, reading, updating, and deleting Item instances are now accessible at /items.

___

## Using `EndpointCreator` Directly

Using the `EndpointCreator` class in FastCRUD is a more flexible way to add CRUD endpoints to a FastAPI application. This guide covers how to use `EndpointCreator` for more customized endpoint creation.

### Step 1: Define Your Model and Schema

Define your SQLAlchemy models and corresponding Pydantic schemas for data validation.

```python title="models/item.py"
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import DeclarativeBase
from pydantic import BaseModel

class Base(DeclarativeBase):
    pass

class Item(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)

class ItemCreateSchema(BaseModel):
    name: str
    description: str

class ItemUpdateSchema(BaseModel):
    name: str
    description: str
```

### Step 2: Set Up FastAPI and FastCRUD

Next, set up your FastAPI application and FastCRUD instances. This involves configuring the database connection and creating a CRUD instance for your model.

```python
from fastapi import FastAPI
from fastcrud import FastCRUD, crud_router
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Database setup (Async SQLAlchemy)
DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# FastAPI app
app = FastAPI()

# CRUD operations setup
crud = FastCRUD(Item)
```

### Step 3: Initialize `EndpointCreator`
Create an instance of EndpointCreator by passing the necessary parameters, including your model, session, CRUD instance, and schemas.

```python
from fastcrud import EndpointCreator

# Initialize EndpointCreator
endpoint_creator = EndpointCreator(
    session=async_session,
    model=YourModel,
    crud=your_crud_instance,
    create_schema=YourCreateSchema,
    update_schema=YourUpdateSchema,
    delete_schema=YourDeleteSchema,
    path="/yourmodelpath",
    tags=["YourModelTag"]
)
```

### Step 4: Add Custom Endpoints

Add custom endpoints using the EndpointCreator. You can inject dependencies as needed.

```python
# Example of adding custom dependencies
endpoint_creator.add_routes_to_router(
    read_deps=[custom_dependency],
    update_deps=[another_custom_dependency]
)

```

### Step 5: Include the Router in Your Application
Finally, include the router from the EndpointCreator in your FastAPI application.

```python
app.include_router(endpoint_creator.router)

```

## Advanced Customization

You can override the default methods in EndpointCreator for more control over the CRUD operations. This allows for implementing custom business logic.

### Custom Endpoint Logic
Override methods like _create_item, _read_item, etc., in your EndpointCreator instance to customize the behavior of each endpoint.

### Handling Complex Scenarios
For complex scenarios like nested resources, you can manually define additional endpoints and add them to the EndpointCreator router.


## Conclusion

By following these steps, you can quickly set up CRUD endpoints for your models in a FastAPI application using crud_router or EndpointCreator. This utility function reduces boilerplate code and increases development efficiency by automating the creation of standard API endpoints.