# Using FastCRUD with SQLModel

Since SQLModel is just a combination of SQLAlchemy and Pydantic, the process simplifies as SQLModel combines the model and schema definitions.

Wherever in the docs you see a SQLAlchemy model or Pydantic schema being used, you may just replace it with SQLModel and it will work. For the quick start:

Define your SQLModel model

```python title="setup.py" hl_lines="5-8"
from sqlmodel import SQLModel, Field
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession

class Item(SQLModel):
    __tablename__ = 'items'
    id: int = Field(primary_key=True)
    name: str

class ItemCreateSchema(SQLModel):
    name: str

DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
```

Then your schemas

```python title="setup.py" hl_lines="10 11"
from sqlmodel import SQLModel, Field
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession

class Item(SQLModel):
    __tablename__ = 'items'
    id: int = Field(primary_key=True)
    name: str

class ItemCreateSchema(SQLModel):
    name: str

DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
```

And, finally, your database connection

```python title="setup.py" hl_lines="13-15"
from sqlmodel import SQLModel, Field
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession

class Item(SQLModel):
    __tablename__ = 'items'
    id: int = Field(primary_key=True)
    name: str

class ItemCreateSchema(SQLModel):
    name: str

DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
```

Use `crud_router` and include it in your `FastAPI` application

```python title="main.py" hl_lines="17-24 26"
from fastcrud import crud_router

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

item_router = crud_router(
    session=get_session,
    model=Item,
    create_schema=ItemSchema,
    update_schema=ItemSchema,
    path="/items",
    tags=["Items"]
)

app.include_router(item_router)
```

By following the above setup, FastCRUD auto-generates CRUD endpoints for your model, accessible through the `/docs` route of your FastAPI application.
