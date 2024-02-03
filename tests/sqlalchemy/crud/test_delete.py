import pytest
from sqlalchemy import select
from fastcrud.crud.fast_crud import FastCRUD


@pytest.mark.asyncio
async def test_db_delete_hard_delete(async_session, test_data_tier, tier_model):
    for tier_item in test_data_tier:
        async_session.add(tier_model(**tier_item))
    await async_session.commit()

    crud = FastCRUD(tier_model)
    some_existing_id = test_data_tier[0]["id"]
    await crud.db_delete(db=async_session, id=some_existing_id)

    deleted_record = await async_session.execute(
        select(tier_model).where(tier_model.id == some_existing_id)
    )
    assert deleted_record.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_delete_soft_delete(async_session, test_data, test_model):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    crud = FastCRUD(test_model)
    some_existing_id = test_data[0]["id"]
    await crud.delete(db=async_session, id=some_existing_id)

    soft_deleted_record = await async_session.execute(
        select(test_model).where(test_model.id == some_existing_id)
    )
    soft_deleted = soft_deleted_record.scalar_one()
    assert soft_deleted.is_deleted is True
    assert soft_deleted.deleted_at is not None


@pytest.mark.asyncio
async def test_delete_hard_delete_as_fallback(
    async_session, test_data_tier, tier_model
):
    for tier_item in test_data_tier:
        async_session.add(tier_model(**tier_item))
    await async_session.commit()

    crud = FastCRUD(tier_model)
    some_existing_id = test_data_tier[0]["id"]
    await crud.delete(db=async_session, id=some_existing_id)

    hard_deleted_record = await async_session.execute(
        select(tier_model).where(tier_model.id == some_existing_id)
    )
    assert hard_deleted_record.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_delete_multiple_records(async_session, test_data, test_model):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    crud = FastCRUD(test_model)
    with pytest.raises(Exception):
        await crud.delete(db=async_session, allow_multiple=False, tier_id=1)


@pytest.mark.asyncio
async def test_get_with_advanced_filters(async_session, test_data, test_model):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    crud = FastCRUD(test_model)
    records = await crud.get_multi(db=async_session, id__gt=5)
    for record in records["data"]:
        assert record["id"] > 5, "All fetched records should have 'id' greater than 5"


@pytest.mark.asyncio
async def test_soft_delete_with_custom_columns(async_session, test_data, test_model):
    crud = FastCRUD(
        test_model, is_deleted_column="is_deleted", deleted_at_column="deleted_at"
    )
    some_existing_id = test_data[0]["id"]

    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    await crud.delete(db=async_session, id=some_existing_id, allow_multiple=False)

    deleted_record = await async_session.execute(
        select(test_model)
        .where(test_model.id == some_existing_id)
        .where(getattr(test_model, "is_deleted") is True)
    )
    deleted_record = deleted_record.scalar_one_or_none()

    assert deleted_record is not None, "Record should exist after soft delete"
    assert (
        getattr(deleted_record, "is_deleted") is True
    ), "Record should be marked as soft deleted"
    assert (
        getattr(deleted_record, "deleted_at") is not None
    ), "Record should have a deletion timestamp"
