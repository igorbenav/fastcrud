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
