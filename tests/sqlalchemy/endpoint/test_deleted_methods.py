import pytest
from fastapi.testclient import TestClient
from fastcrud import FastCRUD, crud_router

from ...sqlalchemy.conftest import get_session_local


@pytest.mark.asyncio
async def test_deleted_methods(
    client: TestClient, async_session, test_model, create_schema, update_schema
):
    custom_router = crud_router(
        session=get_session_local,
        model=test_model,
        crud=FastCRUD(test_model),
        create_schema=create_schema,
        update_schema=update_schema,
        deleted_methods=["delete"],
        path="/test_custom",
        tags=["Test"],
    )

    client.app.include_router(custom_router)

    response = client.post(
        "/test_custom/create", json={"name": "Test Item", "tier_id": 1}
    )
    assert response.status_code == 200

    item_id = response.json()["id"]
    response = client.delete(f"/test_custom/delete/{item_id}")
    assert response.status_code == 404
