import pytest
from sqlalchemy import select
from sqlalchemy.exc import ArgumentError
from fastcrud.crud.fast_crud import FastCRUD


@pytest.mark.asyncio
async def test_apply_sorting_single_column_asc(async_session, test_model, test_data):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    crud = FastCRUD(test_model)
    stmt = select(test_model)
    sorted_stmt = crud._apply_sorting(stmt, "name")

    result = await async_session.execute(sorted_stmt)
    sorted_data = result.scalars().all()

    expected_sorted_names_asc = sorted([item["name"] for item in test_data])
    assert [item.name for item in sorted_data] == expected_sorted_names_asc


@pytest.mark.asyncio
async def test_apply_sorting_single_column_desc(async_session, test_model, test_data):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    crud = FastCRUD(test_model)
    stmt = select(test_model)
    sorted_stmt = crud._apply_sorting(stmt, "name", "desc")

    result = await async_session.execute(sorted_stmt)
    sorted_data = result.scalars().all()

    expected_sorted_names_desc = sorted(
        [item["name"] for item in test_data], reverse=True
    )
    assert [item.name for item in sorted_data] == expected_sorted_names_desc


@pytest.mark.asyncio
async def test_apply_sorting_multiple_columns_mixed_order(
    async_session, test_model, test_data
):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    crud = FastCRUD(test_model)
    stmt = select(test_model)
    sorted_stmt = crud._apply_sorting(stmt, ["name", "id"], ["asc", "desc"])

    result = await async_session.execute(sorted_stmt)
    sorted_data = result.scalars().all()

    sorted_data_manual = sorted(test_data, key=lambda x: (x["name"], -x["id"]))
    expected_sorted_names_mixed = [item["name"] for item in sorted_data_manual]
    assert [item.name for item in sorted_data] == expected_sorted_names_mixed


@pytest.mark.asyncio
async def test_apply_sorting_invalid_column(async_session, test_model, test_data):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    crud = FastCRUD(test_model)
    stmt = select(test_model)

    with pytest.raises(ArgumentError):
        crud._apply_sorting(stmt, "invalid_column")


@pytest.mark.asyncio
async def test_apply_sorting_invalid_sort_order(async_session, test_model, test_data):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    crud = FastCRUD(test_model)
    stmt = select(test_model)

    with pytest.raises(ValueError):
        crud._apply_sorting(stmt, "name", "invalid_order")


@pytest.mark.asyncio
async def test_apply_sorting_mismatched_lengths(async_session, test_model, test_data):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    crud = FastCRUD(test_model)
    stmt = select(test_model)

    with pytest.raises(ValueError):
        crud._apply_sorting(stmt, ["name", "id"], ["asc"])


@pytest.mark.asyncio
async def test_apply_sorting_sort_orders_without_columns(async_session, test_model):
    crud = FastCRUD(test_model)
    stmt = select(test_model)

    with pytest.raises(ValueError) as exc_info:
        crud._apply_sorting(stmt, None, ["asc"])

    assert str(exc_info.value) == "Sort orders provided without corresponding sort columns."
