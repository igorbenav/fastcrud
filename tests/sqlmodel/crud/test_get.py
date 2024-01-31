import pytest
from fastcrud.crud.fast_crud import FastCRUD
from ..conftest import ModelTest
from ..conftest import CreateSchemaTest


@pytest.mark.asyncio
async def test_get_existing_record(async_session, test_data):
    test_record = ModelTest(**test_data[0])
    async_session.add(test_record)
    await async_session.commit()

    crud = FastCRUD(ModelTest)
    fetched_record = await crud.get(async_session, **test_data[0])

    assert fetched_record is not None
    assert fetched_record["name"] == test_data[0]["name"]


@pytest.mark.asyncio
async def test_get_with_filters(async_session, test_data):
    for item in test_data:
        async_session.add(ModelTest(**item))
    await async_session.commit()

    crud = FastCRUD(ModelTest)
    for item in test_data:
        fetched_record = await crud.get(async_session, **item)
        assert fetched_record is not None
        assert fetched_record["name"] == item["name"]


@pytest.mark.asyncio
async def test_get_non_existent_record(async_session):
    crud = FastCRUD(ModelTest)
    non_existent_filter = {"name": "NonExistentName"}
    fetched_record = await crud.get(async_session, **non_existent_filter)

    assert fetched_record is None


@pytest.mark.asyncio
async def test_get_selecting_columns(async_session, test_data):
    test_record = ModelTest(**test_data[0])
    async_session.add(test_record)
    await async_session.commit()

    crud = FastCRUD(ModelTest)
    fetched_record = await crud.get(
        async_session, schema_to_select=CreateSchemaTest, **test_data[0]
    )

    assert fetched_record is not None
    assert "name" in fetched_record
