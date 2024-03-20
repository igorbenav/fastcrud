from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select


@pytest.mark.asyncio
async def test_create_item(client: TestClient, async_session, test_model, test_data):
    tester_data = {"name": test_data[0]["name"], "tier_id": test_data[0]["tier_id"]}
    response = client.post("/test/create", json=tester_data)

    assert response.status_code == 200

    stmt = select(test_model).where(test_model.name == test_data[0]["name"])

    result = await async_session.execute(stmt)
    fetched_record = result.scalar_one_or_none()

    assert fetched_record is not None, response.text
    assert fetched_record.name == test_data[0]["name"]
    assert fetched_record.tier_id == 1


@pytest.mark.asyncio
async def test_create_item_with_multiple_primary_keys(
    client: TestClient, async_session, multi_pk_model, test_data_multipk
):
    # for test_data_multipk in test_data_multipk:
    response = client.post(
        "/multi_pk/create",
        json=test_data_multipk,
    )

    assert response.status_code == 200

    stmt = select(multi_pk_model).where(
        multi_pk_model.name == test_data_multipk["name"]
    )

    result = await async_session.execute(stmt)
    fetched_record = result.scalar_one_or_none()

    assert fetched_record is not None, response.text
    assert fetched_record.name == test_data_multipk["name"]
    assert fetched_record.id == test_data_multipk["id"]
    assert fetched_record.uuid == test_data_multipk["uuid"]


@pytest.mark.asyncio
async def test_create_tier_duplicate_check(client: TestClient, async_session):
    test_tier_1 = {"name": "Premium"}
    response = client.post("/tier/create", json=test_tier_1)
    assert response.status_code == 200, response.text

    test_tier_2 = {"name": "Premium"}
    response = client.post("/tier/create", json=test_tier_2)

    assert response.status_code == 422, response.text

    assert "is already registered" in response.text, response.text
