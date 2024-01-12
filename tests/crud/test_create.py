import pytest
from sqlalchemy import select
from fastcrud.crud.crud_base import CRUDBase
from pydantic import ValidationError

# Assuming your model, schema, and async session setup are defined as before


@pytest.mark.asyncio
async def test_create_successful(async_session, test_model, create_schema):
    crud = CRUDBase(test_model)
    new_data = create_schema(name="New Record")
    await crud.create(async_session, new_data)

    stmt = select(test_model).where(test_model.name == "New Record")
    result = await async_session.execute(stmt)
    fetched_record = result.scalar_one_or_none()

    assert fetched_record is not None
    assert fetched_record.name == "New Record"


@pytest.mark.asyncio
async def test_create_with_various_valid_data(async_session, test_model, create_schema):
    valid_data_samples = [{"name": "Example 1"}, {"name": "Example 2"}]

    for data in valid_data_samples:
        crud = CRUDBase(test_model)
        new_data = create_schema(**data)
        await crud.create(async_session, new_data)

        stmt = select(test_model).where(test_model.name == data["name"])
        result = await async_session.execute(stmt)
        fetched_record = result.scalar_one_or_none()

        assert fetched_record is not None
        assert fetched_record.name == data["name"]


@pytest.mark.asyncio
async def test_create_with_missing_fields(async_session, test_model, create_schema):
    crud = CRUDBase(test_model)
    with pytest.raises(ValidationError):
        await crud.create(async_session, create_schema())


@pytest.mark.asyncio
async def test_create_with_extra_fields(async_session, test_model, create_schema):
    crud = CRUDBase(test_model)
    extra_data = {"name": "Extra", "extra_field": "value"}
    with pytest.raises(ValidationError):
        await crud.create(async_session, create_schema(**extra_data))


@pytest.mark.asyncio
async def test_create_with_invalid_data_types(async_session, test_model, create_schema):
    crud = CRUDBase(test_model)
    invalid_data = {"name": 123}
    with pytest.raises(ValidationError):
        await crud.create(async_session, create_schema(**invalid_data))
