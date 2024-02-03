<p align="center">
  <a href="https://igorbenav.github.io/fastcrud/">
    <img src="https://github.com/igorbenav/fastcrud/blob/main/assets/fastcrud.png?raw=true" alt="FastCRUD written in white with a drawing of a gear and inside this gear a bolt." width="45%" height="auto">
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
<p><b>Documentation</b>: <a href="https://igorbenav.github.io/fastcrud/">igorbenav.github.io/fastcrud</a></p>
<hr>
<h2>Features</h2>

- ⚡️ **Fully Async**: Leverages Python's async capabilities for non-blocking database operations.
- 📚 **SQLAlchemy 2.0**: Works with the latest SQLAlchemy version for robust database interactions.
- 🦾 **Powerful CRUD Functionality**: Full suite of efficient CRUD operations with support for joins.
- ⚙️ **Dynamic Query Building**: Supports building complex queries dynamically, including filtering, sorting, and pagination.
- 🤝 **Advanced Join Operations**: Facilitates performing SQL joins with other models with automatic join condition detection.
- 📖 **Built-in Offset Pagination**: Comes with ready-to-use offset pagination.
- ➤ **Cursor-based Pagination**: Implements efficient pagination for large datasets, ideal for infinite scrolling interfaces.
- 🤸‍♂️ **Modular and Extensible**: Designed for easy extension and customization to fit your requirements.
- 🛣️ **Auto-generated Endpoints**: Streamlines the process of adding CRUD endpoints with custom dependencies and configurations.

<h2>Requirements</h2>
<p>Before installing FastCRUD, ensure you have the following prerequisites:</p>
<ul>
  <li><b>Python:</b> Version 3.9 or newer.</li>
  <li><b>FastAPI:</b> FastCRUD is built to work with FastAPI, so having FastAPI in your project is essential.</li>
  <li><b>SQLAlchemy:</b> Version 2.0.21 or newer. FastCRUD uses SQLAlchemy for database operations.</li>
  <li><b>Pydantic:</b> Version 2.4.1 or newer. FastCRUD leverages Pydantic models for data validation and serialization.</li>
  <li><b>SQLAlchemy-Utils:</b> Optional, but recommended for additional SQLAlchemy utilities.</li>
</ul>

<h2>Installing</h2>

To install, just run:

```sh
pip install fastcrud
```

Or, if using poetry:

```sh
 poetry add fastcrud
```

<h2>Usage</h2>

FastCRUD offers two primary ways to use its functionalities:

1. By using `crud_router` for automatic endpoint creation.
2. By integrating `FastCRUD` directly into your FastAPI endpoints for more control.

Below are examples demonstrating both approaches:

<h3>Using crud_router for Automatic Endpoint Creation</h3>

> \[!WARNING\]
> For now, your primary column must be named `id` or automatic endpoint creation will not work.

Here's a quick example to get you started:

<h4>Define Your Model and Schema</h4>

**models.py**

```python
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class Item(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
```

**schemas.py**

```python
from pydantic import BaseModel

class ItemCreateSchema(BaseModel):
    name: str
    description: str

class ItemUpdateSchema(BaseModel):
    name: str
    description: str
```

<h4>Set Up FastAPI and FastCRUD</h4>

**main.py**

```python
from typing import AsyncGenerator

from fastapi import FastAPI
from fastcrud import FastCRUD, crud_router
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from yourapp.models import Base, Item
from yourapp.schemas import ItemCreateSchema, ItemUpdateSchema

# Database setup (Async SQLAlchemy)
DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Database session dependency
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

# Create tables before the app start
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

# FastAPI app
app = FastAPI(lifespan=lifespan)

# CRUD operations setup
crud = FastCRUD(Item)

# CRUD router setup
item_router = crud_router(
    session=get_session,
    model=Item,
    crud=crud,
    create_schema=ItemCreateSchema,
    update_schema=ItemUpdateSchema,
    path="/items",
    tags=["Items"],
)

app.include_router(item_router)

```

<h3>Using FastCRUD in User-Defined FastAPI Endpoints</h3>

For more control over your endpoints, you can use FastCRUD directly within your custom FastAPI route functions. Here's an example:

**main.py**

```python
from typing import AsyncGenerator

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fastcrud import FastCRUD

from models import Base, Item
from schemas import ItemCreateSchema, ItemUpdateSchema

# Database setup (Async SQLAlchemy)
DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Database session dependency
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

# Create tables before the app start
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

# FastAPI app
app = FastAPI(lifespan=lifespan)

# Instantiate FastCRUD with your model
item_crud = FastCRUD(Item)

@app.post("/custom/items/")
async def create_item(
    item_data: ItemCreateSchema, db: AsyncSession = Depends(get_session)
):
    return await item_crud.create(db, item_data)

@app.get("/custom/items/{item_id}")
async def read_item(item_id: int, db: AsyncSession = Depends(get_session)):
    item = await item_crud.get(db, id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

# You can add more routes for update and delete operations in a similar fashion
```

In this example, we define custom endpoints for creating and reading items using FastCRUD directly, providing more flexibility in how the endpoints are structured and how the responses are handled.

To read more detailed descriptions, go to the <a href="https://igorbenav.github.io/fastcrud/">documentation</a>.

## References

- This project was heavily inspired by CRUDBase in [`FastAPI Microservices`](https://github.com/Kludex/fastapi-microservices) by [@kludex](https://github.com/kludex).
- Thanks [@ada0l](https://github.com/ada0l) for the PyPI package name!

<i>"I'd love something like this for flask"</i>  
Check [flask-muck](https://github.com/dtiesling/flask-muck) by [@dtiesling](https://github.com/dtiesling) out!

## License

[`MIT`](LICENSE.md)

## Contact

Igor Magalhaes – [@igormagalhaesr](https://twitter.com/igormagalhaesr) – igormagalhaesr@gmail.com
[github.com/igorbenav](https://github.com/igorbenav/)
