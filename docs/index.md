<style>
    .md-typeset h1,
    .md-content__button {
        display: none;
    }
</style>

<p align="center">
  <a href="https://github.com/igorbenav/fastcrud">
    <img src="assets/fastcrud.png?raw=true" alt="FastCRUD written in white with a drawing of a gear and inside this gear a bolt." width="45%" height="auto">
  </a>
</p>
<p align="center" markdown=1>
  <i>Powerful CRUD methods and automatic endpoint creation for FastAPI.</i>
</p>
<p align="center" markdown=1>
<a href="https://github.com/igorbenav/fastcrud/actions/workflows/tests.yml">
  <img src="https://github.com/igorbenav/fastcrud/actions/workflows/tests.yml/badge.svg" alt="Tests"/>
</a>
<a href="https://pypi.org/project/fastcrud/">
  <img src="https://img.shields.io/pypi/v/fastcrud?color=%2334D058&label=pypi%20package" alt="PyPi Version"/>
</a>
<a href="https://pypi.org/project/fastcrud/">
  <img src="https://img.shields.io/pypi/pyversions/fastcrud.svg?color=%2334D058" alt="Supported Python Versions"/>
</a>
</p>
<hr>
<p align="justify">
<b>FastCRUD</b> is a Python package for <b>FastAPI</b>, offering robust async CRUD operations and flexible endpoint creation utilities, streamlined through advanced features like <b>auto-detected join</b> conditions, <b>dynamic sorting</b>, and offset and cursor <b>pagination</b>.
</p>
<hr>

## Features

- **Fully Async**: Leverages Python's async capabilities for non-blocking database operations.
- **SQLAlchemy 2.0**: Works with the latest SQLAlchemy version for robust database interactions.
- **SQLModel Support**: You can optionally use SQLModel 0.14 or newer instead of SQLAlchemy.
- **Powerful CRUD Functionality**: Full suite of efficient CRUD operations with support for joins.
- **Dynamic Query Building**: Supports building complex queries dynamically, including filtering, sorting, and pagination.
- **Advanced Join Operations**: Facilitates performing SQL joins with other models with automatic join condition detection.
- **Built-in Offset Pagination**: Comes with ready-to-use offset pagination.
- **Cursor-based Pagination**: Implements efficient pagination for large datasets, ideal for infinite scrolling interfaces.
- **Modular and Extensible**: Designed for easy extension and customization to fit your requirements.
- **Auto-generated Endpoints**: Streamlines the process of adding CRUD endpoints with custom dependencies and configurations.

## Minimal Example
Assuming you have your model, schemas and database connection:

```python
# imports here

# define your model
class Item(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True)
    name = Column(String)

# your schemas
class ItemSchema(BaseModel):
    name: str

# database connection
DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(DATABASE_URL, echo=True)
session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
```

Use `crud_router` and include it in your `FastAPI` application

```python
from fastcrud import FastCRUD, crud_router

app = FastAPI()

item_router = crud_router(
    session=session,
    model=Item,
    crud=FastCRUD(Item),
    create_schema=ItemSchema,
    update_schema=ItemSchema,
    path="/items",
    tags=["Items"]
)

app.include_router(item_router)
```

And it's all done, just go to `/docs` and the crud endpoints are created.

## Requirements
<p>Before installing FastCRUD, ensure you have the following prerequisites:</p>
<ul>
  <li><b>Python:</b> Version 3.9 or newer.</li>
  <li><b>FastAPI:</b> FastCRUD is built to work with FastAPI, so having FastAPI in your project is essential.</li>
  <li><b>SQLAlchemy or SQLModel:</b> FastCRUD uses SQLAlchemy 2.0 for database operations, so you need SQLAlchemy 2.0 or newer or SQLModel 0.14 or newer.</li>
  <li><b>Pydantic V2 or SQLModel:</b> FastCRUD leverages Pydantic models for data validation and serialization, so you need Pydantic 2.0 or newer or SQLModel 0.14 or newer.</li>
</ul>

## Installing

 To install, just run:
 ```sh
 pip install fastcrud
 ```

Or, if using poetry:

```sh
poetry add fastcrud
```

## Usage

FastCRUD offers two primary ways to use its functionalities: 

1. By using `crud_router` for automatic endpoint creation.
2. By integrating `FastCRUD` directly into your FastAPI endpoints for more control.

Below are examples demonstrating both approaches:

### Using crud_router for Automatic Endpoint Creation

!!! WARNING
    For now, your primary column must be named `id` or automatic endpoint creation will not work.

Here's a quick example to get you started:

#### Define Your Model and Schema

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

#### Set Up FastAPI and FastCRUD

```python title="main.py"
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

### Using FastCRUD in User-Defined FastAPI Endpoints

For more control over your endpoints, you can use FastCRUD directly within your custom FastAPI route functions. Here's an example:

```python title="api/v1/item.py" hl_lines="10 14 18"
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastcrud import FastCRUD
from yourapp.models import Item
from yourapp.schemas import ItemCreateSchema, ItemUpdateSchema

# Assume async_session is already set up as per the previous example

# Instantiate FastCRUD with your model
item_crud = FastCRUD(Item)

@app.post("/custom/items/")
async def create_item(item_data: ItemCreateSchema, db: AsyncSession = Depends(async_session)):
    return await item_crud.create(db, item_data)

@app.get("/custom/items/{item_id}")
async def read_item(item_id: int, db: AsyncSession = Depends(async_session)):
    item = await item_crud.get(db, id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

# You can add more routes for update and delete operations in a similar fashion
```

## License

[`MIT`](community/LICENSE.md)