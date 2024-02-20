import pytest
from fastapi.testclient import TestClient


@pytest.mark.asyncio
async def test_read_paginated(client: TestClient, async_session, test_model, test_data):
    for data in test_data:
        new_item = test_model(**data)
        async_session.add(new_item)
    await async_session.commit()

    page = 1
    items_per_page = 5

    response = client.get(
        f"/test/get_paginated?page={page}&itemsPerPage={items_per_page}"
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

    test_item = test_data[0]
    assert any(item["name"] == test_item["name"] for item in data["data"])

    assert data["page"] == page
    assert data["items_per_page"] == items_per_page
