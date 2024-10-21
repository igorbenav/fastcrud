import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select


@pytest.mark.asyncio
async def test_read_item_success(
    client: TestClient, async_session, test_model, test_data
):
    tester_data = {"name": test_data[0]["name"], "tier_id": test_data[0]["tier_id"]}
    new_item = test_model(**tester_data)
    async_session.add(new_item)
    await async_session.commit()
    await async_session.refresh(new_item)

    response = client.get(f"/test/get/{new_item.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == tester_data["name"]
    assert data["tier_id"] == tester_data["tier_id"]


@pytest.mark.asyncio
async def test_read_item_not_found(client: TestClient, async_session, test_model):
    stmt = select(test_model.id).order_by(test_model.id.desc()).limit(1)
    result = await async_session.execute(stmt)
    max_id = result.scalar_one_or_none()

    non_existent_id = (max_id + 1) if max_id is not None else 1

    response = client.get(f"/test/get/{non_existent_id}")
    assert response.status_code == 404
    assert response.json() == {"detail": "Item not found"}


@pytest.mark.asyncio
async def test_read_multi_primary_key_item_success(
    client: TestClient, async_session, multi_pk_model, test_data_multipk
):
    tester_data = test_data_multipk
    new_item = multi_pk_model(**tester_data)
    async_session.add(new_item)
    await async_session.commit()
    await async_session.refresh(new_item)

    response = client.get(f"/multi_pk/get/{new_item.id}/{new_item.uuid}")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == tester_data["name"]
    assert data["id"] == tester_data["id"]
    assert data["uuid"] == tester_data["uuid"]


@pytest.mark.asyncio
async def test_read_item_with_schema(
    client_with_select_schema: TestClient,
    async_session,
    test_model,
    test_data,
    read_schema,
):
    tester_data = {"name": test_data[0]["name"], "tier_id": test_data[0]["tier_id"]}
    new_item = test_model(**tester_data)
    async_session.add(new_item)
    await async_session.commit()
    await async_session.refresh(new_item)

    response = client_with_select_schema.get(f"/test/get/{new_item.id}")

    assert response.status_code == 200
    data = response.json()
    assert read_schema.model_validate(data)
    assert data["name"] == tester_data["name"]
    assert data["tier_id"] == tester_data["tier_id"]
