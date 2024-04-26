import pytest
from fastapi.testclient import TestClient
from fastcrud import FastCRUD, crud_router

from ..conftest import get_session_local


@pytest.mark.asyncio
async def test_read_items(client: TestClient, async_session, test_model, test_data):
    for data in test_data:
        new_item = test_model(**data)
        async_session.add(new_item)
    await async_session.commit()

    response = client.get("/test/get_multi")

    assert response.status_code == 200
    data = response.json()

    assert "data" in data
    assert len(data["data"]) > 0

    test_item = test_data[0]
    assert any(item["name"] == test_item["name"] for item in data["data"])


@pytest.mark.asyncio
async def test_read_items_limit0(client: TestClient, async_session, test_model, create_schema, update_schema, test_data):
    custom_router = crud_router(
        session=get_session_local,
        model=test_model,
        crud=FastCRUD(test_model),
        create_schema=create_schema,
        update_schema=update_schema,
        path="/custom",
        tags=["Test"],
        allow_limit_0=True,
    )

    client.app.include_router(custom_router)

    for data in test_data:
        new_item = test_model(**data)
        async_session.add(new_item)
    await async_session.commit()

    with pytest.raises(ValueError) as exc_info:
        response = client.get("/test/get_multi?limit=0")
    assert "0 is not a valid value for limit!" in str(exc_info.value)

    response = client.get("/custom/get_multi?limit=0")
    assert response.status_code == 200
    data = response.json()

    assert "data" in data
    assert len(data["data"]) > 0

    test_item = test_data[0]
    assert any(item["name"] == test_item["name"] for item in data["data"])
