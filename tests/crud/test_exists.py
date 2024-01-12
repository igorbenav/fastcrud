import pytest
from fastcrud.crud.crud_base import CRUDBase
from ..conftest import ModelTest

@pytest.mark.asyncio
async def test_exists_record_found(async_session, test_model, test_data):
    test_record = test_model(**test_data[0])
    async_session.add(test_record)
    await async_session.commit()

    crud = CRUDBase(test_model)
    exists = await crud.exists(async_session, **test_data[0])

    assert exists is True

@pytest.mark.asyncio
async def test_exists_record_not_found(async_session, test_model):
    crud = CRUDBase(test_model)
    non_existent_filter = {'name': 'NonExistentName'}
    exists = await crud.exists(async_session, **non_existent_filter)

    assert exists is False
