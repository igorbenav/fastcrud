import pytest
from fastcrud.crud.fast_crud import FastCRUD
from sqlalchemy import Selectable, select


def format_statement(stmt: Selectable):
    return str(stmt.compile(compile_kwargs={"literal_binds": True}))


@pytest.mark.asyncio
async def test_select_default(async_session, test_model, test_data):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    crud = FastCRUD(test_model)
    stmt = await crud.select()
    assert format_statement(stmt) == format_statement(select(crud.model))


@pytest.mark.asyncio
async def test_select_with_filter(async_session, test_model, test_data):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    crud = FastCRUD(test_model)
    stmt = await crud.select(id=1)
    res = await async_session.execute(stmt)
    select_elmts = [dict(r) for r in res.mappings()]
    crud_elmts = await crud.get_multi(async_session, id=1)
    assert crud_elmts["data"] == select_elmts


@pytest.mark.asyncio
async def test_select_with_gte_filter(async_session, test_model, test_data):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    crud = FastCRUD(test_model)
    stmt = await crud.select(id__gte=5)
    res = await async_session.execute(stmt)
    select_elmts = [dict(r) for r in res.mappings()]
    crud_elmts = await crud.get_multi(async_session, id__gte=5)
    assert crud_elmts["data"] == select_elmts


@pytest.mark.asyncio
async def test_select_with_sorting(async_session, test_model, test_data):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    crud = FastCRUD(test_model)
    stmt = await crud.select(sort_columns="name")
    res = await async_session.execute(stmt)
    select_elmts = [dict(r) for r in res.mappings()]
    crud_elmts = await crud.get_multi(async_session, sort_columns="name")
    assert crud_elmts["data"] == select_elmts


@pytest.mark.asyncio
async def test_select_with_greater_than_filter(async_session, test_model, test_data):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    crud = FastCRUD(test_model)

    stmt = await crud.select(name__gt='Charlie')
    res = await async_session.execute(stmt)
    filtered_items = [dict(r) for r in res.mappings()]
    expected_items = [item for item in test_data if item['name'] > 'Charlie']

    assert len(filtered_items) == len(expected_items), "Filtering with greater than operator failed"


@pytest.mark.asyncio
async def test_select_with_less_than_or_equal_filter(async_session, test_model, test_data):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()
    
    crud = FastCRUD(test_model)

    stmt = await crud.select(id__lte=5)
    res = await async_session.execute(stmt)
    filtered_items = [dict(r) for r in res.mappings()]
    expected_items = [item for item in test_data if item['id'] <= 5]

    assert len(filtered_items) == len(expected_items), "Filtering with less than or equal operator failed"


@pytest.mark.asyncio
async def test_select_with_descending_sort(async_session, test_model, test_data):
    for item in test_data:
        item.setdefault('is_deleted', False)
        item.setdefault('deleted_at', None)
        async_session.add(test_model(**item))
    await async_session.commit()

    crud = FastCRUD(test_model)

    stmt = await crud.select(sort_columns="name", sort_orders="desc")
    res = await async_session.execute(stmt)
    sorted_items = [dict(r) for r in res.mappings()]

    assert sorted_items == sorted(test_data, key=lambda x: x['name'], reverse=True), "Sorting in descending order failed"


@pytest.mark.asyncio
async def test_select_combining_filters_and_sorting(async_session, test_model, test_data):
    for item in test_data:
        item.setdefault('is_deleted', False)
        item.setdefault('deleted_at', None)
        async_session.add(test_model(**item))
    await async_session.commit()

    crud = FastCRUD(test_model)

    stmt = await crud.select(name__gte='Eve', sort_columns="id", sort_orders="asc")
    res = await async_session.execute(stmt)
    filtered_and_sorted_items = [dict(r) for r in res.mappings()]
    expected_items = sorted([item for item in test_data if item['name'] >= 'Eve'], key=lambda x: x['id'])

    assert filtered_and_sorted_items == expected_items, "Combining filters and sorting failed"
