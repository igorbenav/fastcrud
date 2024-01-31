import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select


@pytest.mark.asyncio
async def test_delete_item(client: TestClient, async_session, test_model, test_data):
    for data in test_data:
        new_item = test_model(**data)
        async_session.add(new_item)
    await async_session.commit()

    stmt = select(test_model.id).order_by(test_model.id.asc()).limit(1)
    result = await async_session.execute(stmt)
    min_id = result.scalar_one_or_none()

    response = client.delete(f"/test/delete/{min_id}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data == {"message": "Item deleted successfully"}

    db_item = await async_session.get(test_model, min_id)
    assert db_item.is_deleted is True


@pytest.mark.asyncio
async def test_db_delete_item(client: TestClient, async_session, test_model, test_data):
    for data in test_data:
        new_item = test_model(**data)
        async_session.add(new_item)
    await async_session.commit()

    stmt = select(test_model.id).order_by(test_model.id.asc()).limit(1)
    result = await async_session.execute(stmt)
    min_id = result.scalar_one_or_none()

    response = client.delete(f"/test/db_delete/{min_id}")

    assert response.status_code == 200, response.text
    data = response.json()
    assert data == {"message": "Item permanently deleted from the database"}

    db_item = await async_session.get(test_model, min_id)
    assert db_item is None
