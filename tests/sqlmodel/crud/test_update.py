import pytest

from sqlalchemy import select
from sqlalchemy.exc import MultipleResultsFound

from fastcrud.crud.fast_crud import FastCRUD
from ...sqlalchemy.conftest import ModelTest


@pytest.mark.asyncio
async def test_update_successful(async_session, test_data):
    for item in test_data:
        async_session.add(ModelTest(**item))
    await async_session.commit()

    crud = FastCRUD(ModelTest)
    some_existing_id = test_data[0]["id"]
    updated_data = {"name": "Updated Name"}
    await crud.update(db=async_session, object=updated_data, id=some_existing_id)

    updated_record = await async_session.execute(
        select(ModelTest).where(ModelTest.id == some_existing_id)
    )
    assert updated_record.scalar_one().name == "Updated Name"


@pytest.mark.asyncio
async def test_update_various_data(async_session, test_data):
    for item in test_data:
        async_session.add(ModelTest(**item))
    await async_session.commit()

    crud = FastCRUD(ModelTest)
    some_existing_id = test_data[0]["id"]
    updated_data = {"name": "Different Name"}
    await crud.update(db=async_session, object=updated_data, id=some_existing_id)

    updated_record = await async_session.execute(
        select(ModelTest).where(ModelTest.id == some_existing_id)
    )
    assert updated_record.scalar_one().name == "Different Name"


@pytest.mark.asyncio
async def test_update_non_existent_record(async_session, test_data):
    for item in test_data:
        async_session.add(ModelTest(**item))
    await async_session.commit()

    crud = FastCRUD(ModelTest)
    non_existent_id = 99999
    updated_data = {"name": "New Name"}
    await crud.update(db=async_session, object=updated_data, id=non_existent_id)

    record = await async_session.execute(
        select(ModelTest).where(ModelTest.id == non_existent_id)
    )
    assert record.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_update_invalid_filters(async_session, test_data):
    for item in test_data:
        async_session.add(ModelTest(**item))
    await async_session.commit()

    crud = FastCRUD(ModelTest)
    updated_data = {"name": "New Name"}

    non_matching_filter = {"name": "NonExistingName"}
    await crud.update(db=async_session, object=updated_data, **non_matching_filter)

    for item in test_data:
        record = await async_session.execute(
            select(ModelTest).where(ModelTest.id == item["id"])
        )
        fetched_record = record.scalar_one()
        assert fetched_record.name != "New Name"


@pytest.mark.asyncio
async def test_update_additional_fields(async_session, test_data):
    for item in test_data:
        async_session.add(ModelTest(**item))
    await async_session.commit()

    crud = FastCRUD(ModelTest)
    some_existing_id = test_data[0]["id"]
    updated_data = {"name": "Updated Name", "extra_field": "Extra"}

    with pytest.raises(ValueError) as exc_info:
        await crud.update(db=async_session, object=updated_data, id=some_existing_id)

    assert "Extra fields provided" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_with_advanced_filters(async_session, test_data):
    for item in test_data:
        async_session.add(ModelTest(**item))
    await async_session.commit()

    advanced_filter = {"id__gt": 5}
    updated_data = {"name": "Updated for Advanced Filter"}

    crud = FastCRUD(ModelTest)
    await crud.update(
        db=async_session, object=updated_data, allow_multiple=True, **advanced_filter
    )

    updated_records = await async_session.execute(
        select(ModelTest).where(ModelTest.id > 5)
    )
    assert all(
        record.name == "Updated for Advanced Filter"
        for record in updated_records.scalars()
    )


@pytest.mark.asyncio
async def test_update_multiple_records(async_session, test_data):
    for item in test_data:
        async_session.add(ModelTest(**item))
    await async_session.commit()

    crud = FastCRUD(ModelTest)
    updated_data = {"name": "Updated Multiple"}
    await crud.update(
        db=async_session, object=updated_data, allow_multiple=True, tier_id=2
    )

    updated_records = await async_session.execute(
        select(ModelTest).where(ModelTest.tier_id == 2)
    )
    assert all(
        record.name == "Updated Multiple" for record in updated_records.scalars()
    )


@pytest.mark.asyncio
async def test_update_multiple_records_restriction(async_session, test_data):
    for item in test_data:
        async_session.add(ModelTest(**item))
    await async_session.commit()

    crud = FastCRUD(ModelTest)
    updated_data = {"name": "Should Fail"}

    with pytest.raises(MultipleResultsFound) as exc_info:
        await crud.update(db=async_session, object=updated_data, id__lt=10)

    assert "Expected exactly one record to update" in str(exc_info.value)
