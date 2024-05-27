import pytest
from fastapi.testclient import TestClient


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
async def test_read_items_with_filters(
    filtered_client: TestClient, async_session, test_model, test_data
):
    for data in test_data:
        new_item = test_model(**data)
        async_session.add(new_item)
    await async_session.commit()

    tier_id = 1
    response = filtered_client.get(f"/test/get_multi?tier_id={tier_id}")

    assert response.status_code == 200
    data = response.json()

    assert "data" in data
    assert len(data["data"]) > 0

    for item in data["data"]:
        assert item["tier_id"] == tier_id

    name = "Alice"
    response = filtered_client.get(f"/test/get_multi?name={name}")

    assert response.status_code == 200
    data = response.json()

    assert "data" in data
    assert len(data["data"]) > 0

    for item in data["data"]:
        assert item["name"] == name


@pytest.mark.asyncio
async def test_read_items_with_dict_filter_config(
    dict_filtered_client: TestClient, async_session, test_model, test_data
):
    for data in test_data:
        new_item = test_model(**data)
        async_session.add(new_item)
    await async_session.commit()

    name = "Alice"
    response = dict_filtered_client.get(f"/test/get_multi?name={name}")

    assert response.status_code == 200
    data = response.json()

    assert "data" in data
    assert len(data["data"]) > 0

    for item in data["data"]:
        assert item["name"] == name


@pytest.mark.asyncio
async def test_invalid_filter_column(invalid_filtered_client):
    pass
