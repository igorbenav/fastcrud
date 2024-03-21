import pytest
from fastcrud.crud.fast_crud import FastCRUD
from sqlalchemy import Selectable, select, func


def format_statement(stmt: Selectable):
    return str(stmt.compile(compile_kwargs={"literal_binds": True}))


@pytest.mark.asyncio
async def test_select(async_session, test_model, test_data):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    crud = FastCRUD(test_model)

    stmt = await crud.select()
    assert format_statement(stmt) == format_statement(select(crud.model))

    stmt = stmt.filter_by(id=1)
    res = await async_session.execute(stmt)
    select_elmts = [dict(r) for r in res.mappings()]
    crud_elmts = await crud.get_multi(async_session, id=1)
    assert crud_elmts["data"] == select_elmts

    stmt = await crud.select(id__gte=5)
    res = await async_session.execute(stmt)
    select_elmts = [dict(r) for r in res.mappings()]
    crud_elmts = await crud.get_multi(async_session, id__gte=5)
    assert crud_elmts["data"] == select_elmts

    stmt = await crud.select(sort_columns="name")
    res = await async_session.execute(stmt)
    select_elmts = [dict(r) for r in res.mappings()]
    crud_elmts = await crud.get_multi(async_session, sort_columns="name")
    assert crud_elmts["data"] == select_elmts
