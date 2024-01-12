import pytest
import pytest_asyncio
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from pydantic import BaseModel, ConfigDict


class Base(DeclarativeBase):
    pass


class ModelTest(Base):
    __tablename__ = "test"
    id = Column(Integer, primary_key=True)
    name = Column(String)


class CreateSchemaTest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str


class UpdateSchemaTest(BaseModel):
    name: str


class DeleteSchemaTest(BaseModel):
    pass


async_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:", echo=True, future=True
)


@pytest_asyncio.fixture(scope="function")
async def async_session() -> AsyncSession:
    session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

    async with session() as s:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        yield s

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await async_engine.dispose()


local_session = sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="function")
def test_data() -> list[dict]:
    return [
        {"id": 1, "name": "Charlie"},
        {"id": 2, "name": "Alice"},
        {"id": 3, "name": "Bob"},
        {"id": 4, "name": "Alice"},
        {"id": 5, "name": "Charlie"},
        {"id": 6, "name": "Bob"},
        {"id": 7, "name": "Alice"},
        {"id": 8, "name": "Charlie"},
        {"id": 9, "name": "Bob"},
        {"id": 10, "name": "Alice"},
    ]


@pytest.fixture
def test_model():
    return ModelTest


@pytest.fixture
def create_schema():
    return CreateSchemaTest


@pytest.fixture
def update_schema():
    return UpdateSchemaTest


@pytest.fixture
def delete_schema():
    return DeleteSchemaTest
