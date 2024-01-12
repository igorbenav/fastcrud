import pytest
from fastcrud.crud.crud_base import CRUDBase


@pytest.mark.asyncio
async def test_count_no_filters(async_session, test_model, test_data):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    crud = CRUDBase(test_model)
    count = await crud.count(async_session)

    assert count == len(test_data)


@pytest.mark.asyncio
async def test_count_with_filters(async_session, test_model, test_data):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    filter_criteria = test_data[0]
    crud = CRUDBase(test_model)
    count = await crud.count(async_session, **filter_criteria)

    assert count == 1


@pytest.mark.asyncio
async def test_count_no_matching_records(async_session, test_model):
    non_existent_filter = {"name": "NonExistentName"}
    crud = CRUDBase(test_model)
    count = await crud.count(async_session, **non_existent_filter)

    assert count == 0
