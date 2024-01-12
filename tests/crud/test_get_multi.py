import pytest
from fastcrud.crud.crud_base import CRUDBase
from sqlalchemy import select, func


@pytest.mark.asyncio
async def test_get_multi_basic(async_session, test_model, test_data):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    total_count_query = await async_session.execute(
        select(func.count()).select_from(test_model)
    )
    total_count = total_count_query.scalar()

    crud = CRUDBase(test_model)
    result = await crud.get_multi(async_session)

    assert len(result["data"]) <= 100
    assert result["total_count"] == total_count


@pytest.mark.asyncio
async def test_get_multi_pagination(async_session, test_model, test_data):
    for item in test_data:
        record = test_model(**item)
        async_session.add(record)
    await async_session.commit()

    total_count_query = await async_session.execute(
        select(func.count()).select_from(test_model)
    )
    total_count = total_count_query.scalar()

    crud = CRUDBase(test_model)
    result_page_1 = await crud.get_multi(async_session, offset=0, limit=5)
    result_page_2 = await crud.get_multi(async_session, offset=5, limit=5)

    assert len(result_page_1["data"]) == min(5, total_count)
    assert len(result_page_2["data"]) == min(5, max(0, total_count - 5))


@pytest.mark.asyncio
async def test_get_multi_sorting(async_session, test_model, test_data):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    total_count_query = await async_session.execute(
        select(func.count()).select_from(test_model)
    )
    total_count = total_count_query.scalar()

    crud = CRUDBase(test_model)
    result = await crud.get_multi(
        async_session, sort_columns=["name"], sort_orders=["asc"]
    )

    sorted_data = sorted(test_data, key=lambda x: x["name"])
    assert [item["name"] for item in result["data"]] == [
        item["name"] for item in sorted_data
    ][:total_count]


@pytest.mark.asyncio
async def test_get_multi_filtering(async_session, test_model, test_data):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    crud = CRUDBase(test_model)
    filter_criteria = {"name": "SpecificName"}
    result = await crud.get_multi(async_session, **filter_criteria)

    assert all(item["name"] == "SpecificName" for item in result["data"])


@pytest.mark.asyncio
async def test_get_multi_edge_cases(async_session, test_model, test_data):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    total_count_query = await async_session.execute(
        select(func.count()).select_from(test_model)
    )
    total_count = total_count_query.scalar()

    crud = CRUDBase(test_model)

    with pytest.raises(ValueError):
        await crud.get_multi(async_session, offset=-1)
    with pytest.raises(ValueError):
        await crud.get_multi(async_session, limit=-1)

    large_offset_result = await crud.get_multi(async_session, offset=total_count + 10)
    assert len(large_offset_result["data"]) == 0


@pytest.mark.asyncio
async def test_get_multi_return_model(
    async_session, test_model, test_data, create_schema
):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    crud = CRUDBase(test_model)
    result = await crud.get_multi(
        async_session, return_as_model=True, schema_to_select=create_schema
    )

    assert all(isinstance(item, create_schema) for item in result["data"])
