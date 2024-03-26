import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select


@pytest.mark.asyncio
async def test_update_item(client: TestClient, async_session, test_model, test_data):
    for data in test_data:
        new_item = test_model(**data)
        async_session.add(new_item)
    await async_session.commit()
    updated_data = {"name": "Updated Name"}

    stmt = select(test_model.id).order_by(test_model.id.asc()).limit(1)
    result = await async_session.execute(stmt)
    min_id = result.scalar_one_or_none()

    update_response = client.patch(f"/test/update/{min_id}", json=updated_data)
    assert update_response.status_code == 200

    stmt = select(test_model).filter_by(id=min_id)
    result = await async_session.execute(stmt)
    data = result.scalar_one_or_none()

    assert data.name == updated_data["name"]
