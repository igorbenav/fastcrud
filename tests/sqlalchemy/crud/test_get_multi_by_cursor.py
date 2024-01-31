import pytest
from fastcrud.crud.fast_crud import FastCRUD
from ...sqlalchemy.conftest import ModelTest


@pytest.mark.asyncio
async def test_get_multi_by_cursor_initial_fetch(async_session, test_data):
    for item in test_data:
        async_session.add(ModelTest(**item))
    await async_session.commit()

    crud = FastCRUD(ModelTest)
    first_page = await crud.get_multi_by_cursor(db=async_session, limit=5)

    assert len(first_page["data"]) == 5
    assert "next_cursor" in first_page


@pytest.mark.asyncio
async def test_get_multi_by_cursor_pagination(async_session, test_data):
    for item in test_data:
        async_session.add(ModelTest(**item))
    await async_session.commit()

    crud = FastCRUD(ModelTest)
    first_page = await crud.get_multi_by_cursor(db=async_session, limit=5)
    second_page = await crud.get_multi_by_cursor(
        db=async_session, cursor=first_page["next_cursor"], limit=5
    )

    assert len(second_page["data"]) == 5
    assert second_page["data"][0]["id"] > first_page["data"][-1]["id"]


@pytest.mark.asyncio
async def test_get_multi_by_cursor_sorting(async_session, test_data):
    for item in test_data:
        async_session.add(ModelTest(**item))
    await async_session.commit()

    crud = FastCRUD(ModelTest)
    asc_page = await crud.get_multi_by_cursor(
        db=async_session, limit=5, sort_order="asc"
    )
    desc_page = await crud.get_multi_by_cursor(
        db=async_session, limit=5, sort_order="desc"
    )

    assert asc_page["data"][0]["id"] < asc_page["data"][-1]["id"]
    assert desc_page["data"][0]["id"] > desc_page["data"][-1]["id"]


@pytest.mark.asyncio
async def test_get_multi_by_cursor_filtering(async_session, test_data):
    for item in test_data:
        async_session.add(ModelTest(**item))
    await async_session.commit()

    crud = FastCRUD(ModelTest)
    filter_criteria = {"name": "SpecificName"}
    filtered_page = await crud.get_multi_by_cursor(
        db=async_session, limit=5, **filter_criteria
    )

    assert all(item["name"] == "SpecificName" for item in filtered_page["data"])


@pytest.mark.asyncio
async def test_get_multi_by_cursor_edge_cases(async_session, test_data):
    for item in test_data:
        async_session.add(ModelTest(**item))
    await async_session.commit()

    crud = FastCRUD(ModelTest)

    all_records = await crud.get_multi_by_cursor(db=async_session)
    print("All records:", all_records)

    highest_id = max(record["id"] for record in all_records["data"])

    large_cursor_result = await crud.get_multi_by_cursor(
        db=async_session, cursor=highest_id + 100, limit=5
    )
    assert len(large_cursor_result["data"]) == 0

    zero_limit_result = await crud.get_multi_by_cursor(db=async_session, limit=0)
    assert len(zero_limit_result["data"]) == 0
    assert zero_limit_result["next_cursor"] is None
