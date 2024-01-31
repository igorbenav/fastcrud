from typing import Optional

import pytest
import pytest_asyncio
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel, ConfigDict
from sqlmodel import SQLModel, Field, Relationship
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastcrud.crud.fast_crud import FastCRUD
from fastcrud.endpoint.crud_router import crud_router


class ModelTest(SQLModel, table=True):
    __tablename__ = "test"
    id: int = Field(primary_key=True)
    name: str
    tier_id: int = Field(foreign_key="tier.id")
    tier: "TierModel" = Relationship(back_populates="tests")
    is_deleted: bool = Field(default=False)
    deleted_at: Optional[datetime] = Field(default=None)


class TierModel(SQLModel, table=True):
    __tablename__ = "tier"
    id: int = Field(primary_key=True)
    name: str = Field(unique=True)
    tests: list["ModelTest"] = Relationship(back_populates="tier")


class CreateSchemaTest(SQLModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    tier_id: int


class UpdateSchemaTest(SQLModel):
    name: str


class DeleteSchemaTest(SQLModel):
    pass


class TierSchemaTest(SQLModel):
    name: str


class TierDeleteSchemaTest(SQLModel):
    pass


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
            await conn.run_sync(SQLModel.metadata.create_all)

        yield s

    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

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
def tier_delete_schema():
    return TierDeleteSchemaTest


@pytest.fixture
def client(
    test_model,
    tier_model,
    create_schema,
    update_schema,
    delete_schema,
    tier_schema,
    tier_delete_schema,
):
    app = FastAPI()

    app.include_router(
        crud_router(
            session=get_session_local,
            model=test_model,
            crud=FastCRUD(test_model),
            create_schema=create_schema,
            update_schema=update_schema,
            delete_schema=delete_schema,
            path="/test",
            tags=["test"],
        )
    )

    app.include_router(
        crud_router(
            session=get_session_local,
            model=tier_model,
            crud=FastCRUD(tier_model),
            create_schema=tier_schema,
            update_schema=tier_schema,
            delete_schema=tier_delete_schema,
            path="/tier",
            tags=["tier"],
        )
    )

    return TestClient(app)
