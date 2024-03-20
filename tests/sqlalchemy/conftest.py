from typing import Optional
from datetime import datetime

import pytest
import pytest_asyncio
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, relationship
from pydantic import BaseModel, ConfigDict
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastcrud.crud.fast_crud import FastCRUD
from fastcrud.endpoint.crud_router import crud_router


class Base(DeclarativeBase):
    pass


class ModelMultiPK(Base):
    __tablename__ = "multi_pk"
    # tests = relationship("ModelTest", back_populates="category")
    id1 = Column(Integer, primary_key=True)
    id2 = Column(Integer, primary_key=True)
    name = Column(String, unique=True)


class CategoryModel(Base):
    __tablename__ = "category"
    tests = relationship("ModelTest", back_populates="category")
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)


class ModelTest(Base):
    __tablename__ = "test"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    tier_id = Column(Integer, ForeignKey("tier.id"))
    category_id = Column(
        Integer, ForeignKey("category.id"), nullable=True, default=None
    )
    tier = relationship("TierModel", back_populates="tests")
    category = relationship("CategoryModel", back_populates="tests")
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True, default=None)


class TierModel(Base):
    __tablename__ = "tier"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    tests = relationship("ModelTest", back_populates="tier")


class BookingModel(Base):
    __tablename__ = "booking"
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("test.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("test.id"), nullable=False)
    booking_date = Column(DateTime, nullable=False)
    owner = relationship("ModelTest", foreign_keys=[owner_id], backref="owned_bookings")
    user = relationship("ModelTest", foreign_keys=[user_id], backref="user_bookings")


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    participants = relationship(
        "Participant",
        secondary="projects_participants_association",
        back_populates="projects",
    )


class Participant(Base):
    __tablename__ = "participants"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    role = Column(String)
    projects = relationship(
        "Project",
        secondary="projects_participants_association",
        back_populates="participants",
    )


class ProjectsParticipantsAssociation(Base):
    __tablename__ = "projects_participants_association"
    project_id = Column(Integer, ForeignKey("projects.id"), primary_key=True)
    participant_id = Column(Integer, ForeignKey("participants.id"), primary_key=True)


class CreateSchemaTest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    tier_id: int
    category_id: Optional[int] = None


class ReadSchemaTest(BaseModel):
    id: int
    name: str
    tier_id: int
    category_id: Optional[int]


class UpdateSchemaTest(BaseModel):
    name: str


class DeleteSchemaTest(BaseModel):
    pass


class TierSchemaTest(BaseModel):
    name: str


class TierDeleteSchemaTest(BaseModel):
    pass


class CategorySchemaTest(BaseModel):
    id: Optional[int] = None
    name: str


class MultiPkCreate(BaseModel):
    name: str


class MultiPkSchema(MultiPkCreate):
    id1: int
    id2: int


class BookingSchema(BaseModel):
    id: Optional[int] = None
    owner_id: int
    user_id: int
    booking_date: datetime


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


@pytest.fixture(scope="function")
def test_data_multipk() -> list[dict]:
    return [
        {"id1": 1, "id2": 1, "name": "Tech"},
        {"id1": 1, "id2": 2, "name": "Health"},
    ]


@pytest.fixture
def multi_pk_model():
    return ModelMultiPK


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
            path="/multi_pk_model",
            tags=["multi_pk_model"],
        )
    )

    return TestClient(app)
