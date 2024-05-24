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
from sqlalchemy.sql import func

from fastcrud.crud.fast_crud import FastCRUD
from fastcrud.endpoint.crud_router import crud_router
from fastcrud import EndpointCreator, FilterConfig


class Base(DeclarativeBase):
    pass


class MultiPkModel(Base):
    __tablename__ = "multi_pk"
    id = Column(Integer, primary_key=True)
    uuid = Column(String(32), primary_key=True)
    name = Column(String, unique=True)
    test_id = Column(Integer, ForeignKey("test.id"))
    test = relationship("ModelTest", back_populates="multi_pk")


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
    multi_pk = relationship("MultiPkModel", back_populates="test")
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True, default=None)


class ModelTestWithTimestamp(Base):
    __tablename__ = "model_test_with_timestamp"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    tier_id = Column(Integer, ForeignKey("tier.id"))
    category_id = Column(
        Integer, ForeignKey("category.id"), nullable=True, default=None
    )
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True, default=None)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )


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


class Card(Base):
    __tablename__ = "cards"
    id = Column(Integer, primary_key=True)
    title = Column(String)


class Article(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    card_id = Column(Integer, ForeignKey("cards.id"))
    card = relationship("Card", back_populates="articles")


Card.articles = relationship("Article", order_by=Article.id, back_populates="card")


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


class MultiPkSchema(BaseModel):
    id: int
    uuid: str
    name: str


class MultiPkCreate(MultiPkSchema):
    pass


class BookingSchema(BaseModel):
    id: Optional[int] = None
    owner_id: int
    user_id: int
    booking_date: datetime


class ArticleSchema(BaseModel):
    id: int
    title: str
    card_id: int


class CardSchema(BaseModel):
    id: int
    title: str
    articles: Optional[list[ArticleSchema]] = []


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
    return MultiPkModel


@pytest.fixture
def multi_pk_test_schema():
    return MultiPkSchema


@pytest.fixture
def multi_pk_test_create_schema():
    return MultiPkCreate


async def test_read_dep():
    pass


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
            read_deps=[test_read_dep],
            path="/multi_pk",
            tags=["multi_pk"],
        )
    )

    return TestClient(app)


@pytest.fixture
def filtered_client(
    test_model,
    create_schema,
    update_schema,
    delete_schema,
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
            filter_config=FilterConfig(tier_id=None, name=None),
            path="/test",
            tags=["test"],
        )
    )

    return TestClient(app)


@pytest.fixture
def dict_filtered_client(
    test_model,
    create_schema,
    update_schema,
    delete_schema,
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
            filter_config={"tier_id": None, "name": None},
            path="/test",
            tags=["test"],
        )
    )

    return TestClient(app)


@pytest.fixture
def invalid_filtered_client(
    test_model,
    create_schema,
    update_schema,
    delete_schema,
):
    filter_config = {"invalid_column": None}

    with pytest.raises(
        ValueError, match="Invalid filter column 'invalid_column': not found in model"
    ):
        EndpointCreator(
            session=get_session_local,
            model=test_model,
            create_schema=create_schema,
            update_schema=update_schema,
            delete_schema=delete_schema,
            filter_config=filter_config,
            path="/test",
            tags=["test"],
        )


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
