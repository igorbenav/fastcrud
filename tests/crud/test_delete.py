import pytest
from sqlalchemy import select
from fastcrud.crud.crud_base import CRUDBase


@pytest.mark.asyncio
async def test_db_delete_hard_delete(async_session, test_data_tier, tier_model):
    for tier_item in test_data_tier:
        async_session.add(tier_model(**tier_item))
    await async_session.commit()

    crud = CRUDBase(tier_model)
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

    crud = CRUDBase(test_model)
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

    crud = CRUDBase(tier_model)
    some_existing_id = test_data_tier[0]["id"]
    await crud.delete(db=async_session, id=some_existing_id)

    hard_deleted_record = await async_session.execute(
        select(tier_model).where(tier_model.id == some_existing_id)
    )
    assert hard_deleted_record.scalar_one_or_none() is None
