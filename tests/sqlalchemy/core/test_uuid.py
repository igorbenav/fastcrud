import pytest
from uuid import UUID, uuid4

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.types import TypeDecorator
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastcrud import crud_router, FastCRUD
from pydantic import BaseModel

from ..conftest import Base


class UUIDModel(Base):
    __tablename__ = "uuid_test"
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String)


class CustomUUID(TypeDecorator):
    """Custom UUID type for testing."""

    impl = String
    cache_ok = True

    def __init__(self):
        super().__init__(36)
        self.__visit_name__ = "uuid"

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return UUID(value)


class CustomUUIDModel(Base):
    __tablename__ = "custom_uuid_test"
    id = Column(CustomUUID(), primary_key=True, default=uuid4)
    name = Column(String)


class UUIDSchema(BaseModel):
    id: UUID
    name: str

    model_config = {"from_attributes": True}


class CreateUUIDSchema(BaseModel):
    name: str

    model_config = {"from_attributes": True}


class UpdateUUIDSchema(BaseModel):
    name: str

    model_config = {"from_attributes": True}


@pytest.fixture
def uuid_client(async_session):
    app = FastAPI()

    app.include_router(
        crud_router(
            session=lambda: async_session,
            model=UUIDModel,
            crud=FastCRUD(UUIDModel),
            create_schema=CreateUUIDSchema,
            update_schema=UpdateUUIDSchema,
            path="/uuid-test",
            tags=["uuid-test"],
            endpoint_names={
                "create": "create",
                "read": "get",
                "update": "update",
                "delete": "delete",
                "read_multi": "get_multi",
            },
        )
    )

    app.include_router(
        crud_router(
            session=lambda: async_session,
            model=CustomUUIDModel,
            crud=FastCRUD(CustomUUIDModel),
            create_schema=CreateUUIDSchema,
            update_schema=UpdateUUIDSchema,
            path="/custom-uuid-test",
            tags=["custom-uuid-test"],
            endpoint_names={
                "create": "create",
                "read": "get",
                "update": "update",
                "delete": "delete",
                "read_multi": "get_multi",
            },
        )
    )

    return TestClient(app)


@pytest.mark.asyncio
@pytest.mark.dialect("postgresql")
async def test_native_uuid_crud(uuid_client):
    response = uuid_client.post("/uuid-test/create", json={"name": "test"})
    assert response.status_code == 200
    data = response.json()
    uuid_id = data["id"]

    try:
        UUID(uuid_id)
    except ValueError:
        pytest.fail("Invalid UUID format")

    response = uuid_client.get(f"/uuid-test/get/{uuid_id}")
    assert response.status_code == 200
    assert response.json()["id"] == uuid_id
    assert response.json()["name"] == "test"

    update_response = uuid_client.patch(
        f"/uuid-test/update/{uuid_id}", json={"name": "updated"}
    )
    response = uuid_client.get(f"/uuid-test/get/{uuid_id}")
    assert update_response.status_code == 200
    assert response.status_code == 200
    assert response.json()["name"] == "updated"

    assert response.status_code == 200
    assert response.json()["name"] == "updated"

    response = uuid_client.delete(f"/uuid-test/delete/{uuid_id}")
    assert response.status_code == 200

    response = uuid_client.get(f"/uuid-test/get/{uuid_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.dialect("sqlite")
async def test_custom_uuid_crud(uuid_client):
    response = uuid_client.post("/custom-uuid-test/create", json={"name": "test"})
    assert (
        response.status_code == 200
    ), f"Creation failed with response: {response.text}"

    try:
        data = response.json()
        assert "id" in data, f"Response does not contain 'id': {data}"
        uuid_id = data["id"]
    except Exception as e:
        pytest.fail(f"Failed to process response: {response.text}. Error: {str(e)}")

    try:
        UUID(uuid_id)
    except ValueError:
        pytest.fail("Invalid UUID format")

    response = uuid_client.get(f"/custom-uuid-test/get/{uuid_id}")
    assert response.status_code == 200
    assert response.json()["id"] == uuid_id
    assert response.json()["name"] == "test"

    update_response = uuid_client.patch(
        f"/custom-uuid-test/update/{uuid_id}", json={"name": "updated"}
    )
    response = uuid_client.get(f"/custom-uuid-test/get/{uuid_id}")

    assert update_response.status_code == 200
    assert response.status_code == 200
    assert response.json()["name"] == "updated"

    response = uuid_client.delete(f"/custom-uuid-test/delete/{uuid_id}")
    assert response.status_code == 200

    response = uuid_client.get(f"/custom-uuid-test/get/{uuid_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_invalid_uuid_handling(uuid_client):
    invalid_uuid = "not-a-uuid"

    response = uuid_client.get(f"/uuid-test/get/{invalid_uuid}")
    assert response.status_code == 422

    response = uuid_client.get(f"/custom-uuid-test/get/{invalid_uuid}")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_uuid_list_endpoint(uuid_client):
    created_ids = []
    for i in range(3):
        response = uuid_client.post("/uuid-test/create", json={"name": f"test_{i}"})
        assert response.status_code == 200
        created_ids.append(response.json()["id"])

    response = uuid_client.get("/uuid-test/get_multi")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 3

    for item in data:
        try:
            UUID(item["id"])
        except ValueError:
            pytest.fail("Invalid UUID format in list response")
