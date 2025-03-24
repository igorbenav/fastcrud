import pytest
from sqlalchemy import select
from fastcrud.crud.fast_crud import FastCRUD
from sqlalchemy.exc import MultipleResultsFound, NoResultFound


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
        .where(getattr(test_model, "is_deleted") == True)  # noqa
    )
    deleted_record = deleted_record.scalar_one_or_none()

    assert deleted_record is not None, "Record should exist after soft delete"
    assert (
        getattr(deleted_record, "is_deleted") == True  # noqa
    ), "Record should be marked as soft deleted"
    assert getattr(deleted_record, "deleted_at") is not None, (
        "Record should have a deletion timestamp"
    )


@pytest.mark.asyncio
async def test_soft_delete_custom_columns(async_session, test_model, test_data):
    crud = FastCRUD(
        test_model,
        is_deleted_column="custom_is_deleted",
        deleted_at_column="custom_deleted_at",
    )
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    existing_record = await crud.get(async_session, id=test_data[0]["id"])
    assert existing_record is not None, "Record should exist before deletion"

    await crud.delete(async_session, id=test_data[0]["id"], allow_multiple=False)

    deleted_record = await crud.get(async_session, id=test_data[0]["id"])
    assert deleted_record is None, (
        "Custom columns not found, so record should be deleted."
    )


@pytest.mark.asyncio
async def test_db_delete_disallow_multiple_matches(
    async_session, test_data, test_model
):
    tier_id_for_multiple_records = 1
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    crud = FastCRUD(test_model)

    with pytest.raises(MultipleResultsFound):
        await crud.db_delete(
            db=async_session, allow_multiple=False, tier_id=tier_id_for_multiple_records
        )

    remaining_records = await async_session.execute(
        select(test_model).where(test_model.tier_id == tier_id_for_multiple_records)
    )
    assert remaining_records.scalars().all(), "No records should have been deleted"


@pytest.mark.asyncio
async def test_soft_delete_db_row_provided(async_session, test_data, test_model):
    test_record = test_model(**test_data[0])
    async_session.add(test_record)
    await async_session.commit()

    crud = FastCRUD(
        test_model, is_deleted_column="is_deleted", deleted_at_column="deleted_at"
    )

    db_row = await async_session.get(test_model, test_record.id)

    await crud.delete(db=async_session, db_row=db_row)

    soft_deleted_record = await async_session.get(test_model, test_record.id)
    assert soft_deleted_record.is_deleted
    assert soft_deleted_record.deleted_at is not None


@pytest.mark.asyncio
async def test_hard_delete_db_row_provided(async_session, test_data_tier, tier_model):
    test_record = tier_model(**test_data_tier[0])
    async_session.add(test_record)
    await async_session.commit()

    crud = FastCRUD(tier_model)
    db_row = await async_session.get(tier_model, test_record.id)

    await crud.delete(db=async_session, db_row=db_row)

    deleted_record = await async_session.get(tier_model, test_record.id)
    assert deleted_record is None


@pytest.mark.asyncio
async def test_delete_no_records_match_filters_raises_no_result_found(
    async_session, test_data, test_model
):
    crud = FastCRUD(test_model)
    non_matching_filter_criteria = {"id": 99999}

    with pytest.raises(NoResultFound):
        await crud.delete(db=async_session, **non_matching_filter_criteria)
