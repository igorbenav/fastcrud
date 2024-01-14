import pytest
import pytest_asyncio

from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, relationship
from pydantic import BaseModel, ConfigDict

from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastcrud.endpoint_creator import EndpointCreator
from fastcrud.crud.crud_base import CRUDBase


class Base(DeclarativeBase):
    pass


class ModelTest(Base):
    __tablename__ = "test"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    tier_id = Column(Integer, ForeignKey("tier.id"))
    tier = relationship("TierModel", back_populates="tests")
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True, default=None)


class TierModel(Base):
    __tablename__ = "tier"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    tests = relationship("ModelTest", back_populates="tier")


class CreateSchemaTest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    tier_id: int


class UpdateSchemaTest(BaseModel):
    name: str


class DeleteSchemaTest(BaseModel):
    pass


class TierSchemaTest(BaseModel):
    name: str


async_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:", echo=True, future=True
)


local_session = sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)


def get_session_local():
    yield local_session()


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


@pytest.fixture(scope="function")
def test_data() -> list[dict]:
    return [
        {"id": 1, "name": "Charlie", "tier_id": 1},
        {"id": 2, "name": "Alice", "tier_id": 2},
        {"id": 3, "name": "Bob", "tier_id": 1},
        {"id": 4, "name": "David", "tier_id": 2},
        {"id": 5, "name": "Eve", "tier_id": 1},
        {"id": 6, "name": "Frank", "tier_id": 2},
        {"id": 7, "name": "Grace", "tier_id": 1},
        {"id": 8, "name": "Hannah", "tier_id": 2},
        {"id": 9, "name": "Ivan", "tier_id": 1},
        {"id": 10, "name": "Judy", "tier_id": 2},
    ]


@pytest.fixture(scope="function")
def test_data_tier() -> list[dict]:
    return [{"id": 1, "name": "Premium"}, {"id": 2, "name": "Basic"}]


@pytest.fixture
def test_model():
    return ModelTest


@pytest.fixture
def tier_model():
    return TierModel


@pytest.fixture
def create_schema():
    return CreateSchemaTest


@pytest.fixture
def tier_schema():
    return TierSchemaTest


@pytest.fixture
def update_schema():
    return UpdateSchemaTest


@pytest.fixture
def delete_schema():
    return DeleteSchemaTest


@pytest.fixture
def client(test_model, create_schema, update_schema, delete_schema):
    app = FastAPI()
    crud = CRUDBase(test_model)
    endpoint_creator = EndpointCreator(
        session=get_session_local,
        model=test_model,
        crud=crud,
        create_schema=create_schema,
        update_schema=update_schema,
        delete_schema=delete_schema,
        path="/test",
        tags=["test"],
    )
    endpoint_creator.add_routes_to_router()
    app.include_router(endpoint_creator.router)
    return TestClient(app)
