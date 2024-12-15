import pytest
from fastapi.testclient import TestClient


@pytest.mark.asyncio
async def test_read_items_with_pagination(
    client: TestClient, async_session, test_model, test_data
):
    for data in test_data:
        new_item = test_model(**data)
        async_session.add(new_item)
    await async_session.commit()

    page = 1
    items_per_page = 5

    response = client.get(f"/test/get_multi?page={page}&itemsPerPage={items_per_page}")

    assert response.status_code == 200

    data = response.json()

    assert "data" in data
    assert "total_count" in data
    assert "page" in data
    assert "items_per_page" in data
    assert "has_more" in data

    assert len(data["data"]) > 0
    assert len(data["data"]) <= items_per_page

    test_item = test_data[0]
    assert any(item["name"] == test_item["name"] for item in data["data"])

    assert data["page"] == page
    assert data["items_per_page"] == items_per_page


@pytest.mark.asyncio
async def test_read_items_with_pagination_and_filters(
    filtered_client: TestClient, async_session, test_model, test_data
):
    for data in test_data:
        new_item = test_model(**data)
        async_session.add(new_item)
    await async_session.commit()

    page = 1
    items_per_page = 5

    tier_id = 1
    response = filtered_client.get(
        f"/test/get_multi?page={page}&itemsPerPage={items_per_page}&tier_id={tier_id}"
    )

    assert response.status_code == 200
    data = response.json()

    assert "data" in data
    assert "total_count" in data
    assert "page" in data
    assert "items_per_page" in data
    assert "has_more" in data

    assert len(data["data"]) > 0
    assert len(data["data"]) <= items_per_page

    for item in data["data"]:
        assert item["tier_id"] == tier_id

    name = "Alice"
    response = filtered_client.get(
        f"/test/get_multi?page={page}&itemsPerPage={items_per_page}&name={name}"
    )

    assert response.status_code == 200
    data = response.json()

    assert "data" in data
    assert "total_count" in data
    assert "page" in data
    assert "items_per_page" in data
    assert "has_more" in data

    assert len(data["data"]) > 0
    assert len(data["data"]) <= items_per_page

    for item in data["data"]:
        assert item["name"] == name


@pytest.mark.asyncio
async def test_read_items_with_only_items_per_page_on_pagination(
    client: TestClient, async_session, test_model, test_data
):
    for data in test_data:
        new_item = test_model(**data)
        async_session.add(new_item)
    await async_session.commit()

    items_per_page = 1

    response = client.get(f"/test/get_multi?&itemsPerPage={items_per_page}")

    assert response.status_code == 200

    data = response.json()

    assert "data" in data
    assert "total_count" in data
    assert "page" in data
    assert "items_per_page" in data
    assert "has_more" in data

    assert len(data["data"]) > 0
    assert len(data["data"]) <= items_per_page

    test_item = test_data[0]
    assert any(item["name"] == test_item["name"] for item in data["data"])

    assert data["page"] == 1
    assert data["items_per_page"] == items_per_page


@pytest.mark.asyncio
async def test_read_items_with_only_page_on_pagination(
    client: TestClient, async_session, test_model, test_data
):
    for data in test_data:
        new_item = test_model(**data)
        async_session.add(new_item)
    await async_session.commit()

    page = 1

    response = client.get(f"/test/get_multi?&page={page}")

    assert response.status_code == 200

    data = response.json()

    assert "data" in data
    assert "total_count" in data
    assert "page" in data
    assert "items_per_page" in data
    assert "has_more" in data

    assert len(data["data"]) > 0
    assert len(data["data"]) <= 10

    test_item = test_data[0]
    assert any(item["name"] == test_item["name"] for item in data["data"])

    assert data["page"] == page
    assert data["items_per_page"] == 10