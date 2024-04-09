from typing import Optional

import pytest
import pytest_asyncio
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from pydantic import ConfigDict
from sqlmodel import SQLModel, Field, Relationship
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.sql import func

from fastcrud.crud.fast_crud import FastCRUD
from fastcrud.endpoint.crud_router import crud_router
from fastcrud import EndpointCreator


class MultiPKModel(SQLModel, table=True):
    __tablename__ = "multi_pk"
    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: Optional[str] = Field(default=None, primary_key=True, max_length=25)
    name: str = Field(index=True)
    test_id: Optional[int] = Field(default=None, foreign_key="test.id")
    test: "ModelTest" = Relationship(back_populates="multi_pk")


class CategoryModel(SQLModel, table=True):
    __tablename__ = "category"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    tests: list["ModelTest"] = Relationship(back_populates="category")


class ModelTest(SQLModel, table=True):
    __tablename__ = "test"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    tier_id: int = Field(default=None, foreign_key="tier.id")
    category_id: Optional[int] = Field(default=None, foreign_key="category.id")
    tier: "TierModel" = Relationship(back_populates="tests")
    multi_pk: "MultiPKModel" = Relationship(back_populates="test")
    category: "CategoryModel" = Relationship(back_populates="tests")
    is_deleted: bool = Field(default=False)
    deleted_at: Optional[datetime] = Field(default=None)


class ModelTestWithTimestamp(SQLModel, table=True):
    __tablename__ = "model_test_with_timestamp"
    id: int = Field(primary_key=True)
    name: str
    tier_id: Optional[int] = Field(foreign_key="tier.id")
    category_id: Optional[int] = Field(default=None, foreign_key="category.id")
    is_deleted: bool = Field(default=False)
    deleted_at: Optional[datetime] = Field(default=None)
    updated_at: datetime = Field(default=func.now(), nullable=False)


class TierModel(SQLModel, table=True):
    __tablename__ = "tier"
    id: int = Field(primary_key=True)
    name: str = Field(unique=True)
    tests: list["ModelTest"] = Relationship(back_populates="tier")


class ProjectsParticipantsAssociation(SQLModel, table=True):
    __tablename__ = "projects_participants_association"
    project_id: int = Field(foreign_key="projects.id", primary_key=True)
    participant_id: int = Field(foreign_key="participants.id", primary_key=True)


class Project(SQLModel, table=True):
    __tablename__ = "projects"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    participants: list["Participant"] = Relationship(
        back_populates="projects", link_model=ProjectsParticipantsAssociation
    )


class Participant(SQLModel, table=True):
    __tablename__ = "participants"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    role: Optional[str] = None
    projects: list["Project"] = Relationship(
        back_populates="participants", link_model=ProjectsParticipantsAssociation
    )


class CreateSchemaTest(SQLModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    tier_id: int


class BookingModel(SQLModel, table=True):
    __tablename__ = "booking"
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(default=None, foreign_key="test.id")
    user_id: int = Field(default=None, foreign_key="test.id")
    booking_date: datetime
    owner: "ModelTest" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "BookingModel.owner_id"}
    )
    user: "ModelTest" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "BookingModel.user_id"}
    )


class ReadSchemaTest(SQLModel):
    id: int
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


class CategorySchemaTest(SQLModel):
    id: Optional[int] = None
    name: str


class BookingSchema(SQLModel):
    id: Optional[int] = None
    owner_id: int
    user_id: int
    booking_date: datetime


class MultiPkCreate(SQLModel):
    id: int
    uuid: str
    name: str
    test_id: int = None


class MultiPkSchema(SQLModel):
    name: str
    test_id: int = None


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
        {"id": 1, "name": "Charlie", "tier_id": 1, "category_id": 1},
        {"id": 2, "name": "Alice", "tier_id": 2, "category_id": 1},
        {"id": 3, "name": "Bob", "tier_id": 1, "category_id": 2},
        {"id": 4, "name": "David", "tier_id": 2, "category_id": 1},
        {"id": 5, "name": "Eve", "tier_id": 1, "category_id": 1},
        {"id": 6, "name": "Frank", "tier_id": 2, "category_id": 2},
        {"id": 7, "name": "Grace", "tier_id": 1, "category_id": 2},
        {"id": 8, "name": "Hannah", "tier_id": 2, "category_id": 1},
        {"id": 9, "name": "Ivan", "tier_id": 1, "category_id": 1},
        {"id": 10, "name": "Judy", "tier_id": 2, "category_id": 2},
        {"id": 11, "name": "Alice", "tier_id": 1, "category_id": 1},
    ]


@pytest.fixture(scope="function")
def test_data_tier() -> list[dict]:
    return [{"id": 1, "name": "Premium"}, {"id": 2, "name": "Basic"}]


@pytest.fixture(scope="function")
def test_data_category() -> list[dict]:
    return [{"id": 1, "name": "Tech"}, {"id": 2, "name": "Health"}]


@pytest.fixture(
    scope="function",
    params=[
        {"id": 1, "uuid": "a", "name": "Tech"},
        {"id": 1, "uuid": "b", "name": "Health"},
    ],
)
def test_data_multipk(request) -> list[dict]:
    return request.param


@pytest.fixture(scope="function")
def test_data_booking() -> list[dict]:
    return [
        {
            "id": 1,
            "owner_id": 1,
            "user_id": 2,
            "booking_date": datetime(2024, 3, 10, 15, 30),
        },
        {
            "id": 2,
            "owner_id": 1,
            "user_id": 3,
            "booking_date": datetime(2024, 3, 11, 10, 0),
        },
    ]


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
def read_schema():
    return ReadSchemaTest


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
def multi_pk_model():
    return MultiPKModel


@pytest.fixture
def multi_pk_test_schema():
    return MultiPkSchema


@pytest.fixture
def multi_pk_test_create_schema():
    return MultiPkCreate


@pytest.fixture
def client(
    test_model,
    tier_model,
    multi_pk_model,
    create_schema,
    update_schema,
    delete_schema,
    tier_schema,
    tier_delete_schema,
    multi_pk_test_schema,
    multi_pk_test_create_schema,
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

    app.include_router(
        crud_router(
            session=get_session_local,
            model=multi_pk_model,
            crud=FastCRUD(multi_pk_model),
            create_schema=multi_pk_test_create_schema,
            update_schema=multi_pk_test_schema,
            delete_schema=multi_pk_test_schema,
            path="/multi_pk",
            tags=["multi_pk"],
        )
    )

    return TestClient(app)


@pytest.fixture
def endpoint_creator(test_model) -> EndpointCreator:
    """Fixture to create an instance of EndpointCreator."""
    return EndpointCreator(
        session=get_session_local,
        model=ModelTest,
        crud=FastCRUD(test_model),
        create_schema=CreateSchemaTest,
        update_schema=UpdateSchemaTest,
        delete_schema=DeleteSchemaTest,
        path="/custom_test",
        tags=["custom_test"],
    )
