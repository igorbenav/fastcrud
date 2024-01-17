from fastcrud.crud.crud_base import CRUDBase
from fastcrud.endpoint.endpoint_creator import EndpointCreator
from fastapi import FastAPI

from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, relationship
from pydantic import BaseModel, ConfigDict


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
    name = Column(String, unique=True)
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


class TierDeleteSchemaTest(BaseModel):
    pass


async_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:", echo=True, future=True
)


local_session = sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)


def get_session_local():
    yield local_session()


async def async_session() -> AsyncSession:
    session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

    async with session() as s:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        yield s

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await async_engine.dispose()


async def startup_event():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


app = FastAPI()

test_crud: CRUDBase = CRUDBase(ModelTest)
test_endpoint_creator = EndpointCreator(
    session=get_session_local,
    model=ModelTest,
    crud=test_crud,
    create_schema=CreateSchemaTest,
    update_schema=UpdateSchemaTest,
    delete_schema=DeleteSchemaTest,
    path="/test",
    tags=["test"],
)
test_endpoint_creator.add_routes_to_router()
app.include_router(test_endpoint_creator.router)

tier_crud: CRUDBase = CRUDBase(TierModel)
tier_endpoint_creator = EndpointCreator(
    session=get_session_local,
    model=TierModel,
    crud=tier_crud,
    create_schema=TierSchemaTest,
    update_schema=TierSchemaTest,
    delete_schema=TierDeleteSchemaTest,
    path="/tier",
    tags=["tier"],
)
tier_endpoint_creator.add_routes_to_router()
app.include_router(tier_endpoint_creator.router)
app.add_event_handler("startup", startup_event)
