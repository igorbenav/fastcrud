import pytest
from fastcrud.crud.fast_crud import FastCRUD


@pytest.mark.asyncio
async def test_exists_record_found(async_session, test_model, test_data):
    test_record = test_model(**test_data[0])
    async_session.add(test_record)
    await async_session.commit()

    crud = FastCRUD(test_model)
    exists = await crud.exists(async_session, **test_data[0])

    assert exists is True


@pytest.mark.asyncio
async def test_exists_record_not_found(async_session, test_model):
    crud = FastCRUD(test_model)
    non_existent_filter = {"name": "NonExistentName"}
    exists = await crud.exists(async_session, **non_existent_filter)

    assert exists is False


@pytest.mark.asyncio
async def test_exists_with_advanced_filters(async_session, test_model, test_data):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    crud = FastCRUD(test_model)
    exists_gt = await crud.exists(db=async_session, id__gt=1)
    assert exists_gt is True, "Should find records with ID greater than 1"

    advanced_filter_lt = {"id__lt": max([d["id"] for d in test_data])}
    exists_lt = await crud.exists(async_session, **advanced_filter_lt)
    assert exists_lt is True, "Should find records with ID less than the max ID"


@pytest.mark.asyncio
async def test_exists_multiple_records_match(async_session, test_model, test_data):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    duplicate_tier_id = test_data[0]["tier_id"]
    crud = FastCRUD(test_model)
    exists = await crud.exists(async_session, tier_id=duplicate_tier_id)
    assert (
        exists is True
    ), "Should return True if multiple records match the filter criteria"
