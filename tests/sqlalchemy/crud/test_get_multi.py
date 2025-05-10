import pytest
from typing import Annotated
from pydantic import BaseModel, Field
from fastcrud.crud.fast_crud import FastCRUD
from sqlalchemy import select, func


class CustomCreateSchemaTest(BaseModel):
    name: Annotated[str, Field(max_length=20)]
    tier_id: int


@pytest.mark.asyncio
async def test_get_multi_basic(async_session, test_model, test_data):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    total_count_query = await async_session.execute(
        select(func.count()).select_from(test_model)
    )
    total_count = total_count_query.scalar()

    crud = FastCRUD(test_model)
    result = await crud.get_multi(async_session)

    assert len(result["data"]) <= 100
    assert result["total_count"] == total_count


@pytest.mark.asyncio
async def test_get_multi_pagination(async_session, test_model, test_data):
    for item in test_data:
        record = test_model(**item)
        async_session.add(record)
    await async_session.commit()

    total_count_query = await async_session.execute(
        select(func.count()).select_from(test_model)
    )
    total_count = total_count_query.scalar()

    crud = FastCRUD(test_model)
    result_page_1 = await crud.get_multi(async_session, offset=0, limit=5)
    result_page_2 = await crud.get_multi(async_session, offset=5, limit=5)

    assert len(result_page_1["data"]) == min(5, total_count)
    assert len(result_page_2["data"]) == min(5, max(0, total_count - 5))


@pytest.mark.asyncio
async def test_get_multi_unpaginated(async_session, test_model, test_data):
    for item in test_data:
        record = test_model(**item)
        async_session.add(record)
    await async_session.commit()

    total_count_query = await async_session.execute(
        select(func.count()).select_from(test_model)
    )
    total_count = total_count_query.scalar()

    crud = FastCRUD(test_model)
    results = await crud.get_multi(async_session, offset=0, limit=None)

    assert len(results["data"]) == total_count


@pytest.mark.asyncio
async def test_get_multi_sorting(async_session, test_model, test_data):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    total_count_query = await async_session.execute(
        select(func.count()).select_from(test_model)
    )
    total_count = total_count_query.scalar()

    crud = FastCRUD(test_model)
    result = await crud.get_multi(
        async_session, sort_columns=["name"], sort_orders=["asc"]
    )

    sorted_data = sorted(test_data, key=lambda x: x["name"])
    assert [item["name"] for item in result["data"]] == [
        item["name"] for item in sorted_data
    ][:total_count]


@pytest.mark.asyncio
async def test_get_multi_filtering(async_session, test_model, test_data):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    crud = FastCRUD(test_model)
    filter_criteria = {"name": "SpecificName"}
    result = await crud.get_multi(async_session, **filter_criteria)

    assert all(item["name"] == "SpecificName" for item in result["data"])


@pytest.mark.asyncio
async def test_get_multi_edge_cases(async_session, test_model, test_data):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    total_count_query = await async_session.execute(
        select(func.count()).select_from(test_model)
    )
    total_count = total_count_query.scalar()

    crud = FastCRUD(test_model)

    with pytest.raises(ValueError):
        await crud.get_multi(async_session, offset=-1)
    with pytest.raises(ValueError):
        await crud.get_multi(async_session, limit=-1)

    large_offset_result = await crud.get_multi(async_session, offset=total_count + 10)
    assert len(large_offset_result["data"]) == 0


@pytest.mark.asyncio
async def test_get_multi_return_model(
    async_session, test_model, test_data, create_schema
):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    crud = FastCRUD(test_model)
    result = await crud.get_multi(
        async_session, return_as_model=True, schema_to_select=create_schema
    )

    assert all(isinstance(item, create_schema) for item in result["data"])


@pytest.mark.asyncio
async def test_get_multi_advanced_filtering(async_session, test_model, test_data):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    crud = FastCRUD(test_model)
    filtered_results = await crud.get_multi(async_session, id__gt=5)

    assert all(
        item["id"] > 5 for item in filtered_results["data"]
    ), "Should only include records with ID greater than 5"


@pytest.mark.asyncio
async def test_get_multi_multiple_sorting(async_session, test_model, test_data):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    crud = FastCRUD(test_model)
    result = await crud.get_multi(
        async_session, sort_columns=["tier_id", "name"], sort_orders=["asc", "desc"]
    )

    assert len(result["data"]) > 0, "Should fetch sorted records"

    tier_ids = [item["tier_id"] for item in result["data"]]
    assert tier_ids == sorted(tier_ids), "tier_id should be sorted in ascending order"

    current_tier_id = None
    names_in_current_tier = []
    for item in result["data"]:
        if item["tier_id"] != current_tier_id:
            if names_in_current_tier:
                assert (
                    names_in_current_tier == sorted(names_in_current_tier, reverse=True)
                ), f"Names within tier_id {current_tier_id} should be sorted in descending order"
            current_tier_id = item["tier_id"]
            names_in_current_tier = [item["name"]]
        else:
            names_in_current_tier.append(item["name"])

    if names_in_current_tier:
        assert (
            names_in_current_tier == sorted(names_in_current_tier, reverse=True)
        ), f"Names within tier_id {current_tier_id} should be sorted in descending order"


@pytest.mark.asyncio
async def test_get_multi_advanced_filtering_return_model(
    async_session, test_model, test_data, read_schema
):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    crud = FastCRUD(test_model)
    result = await crud.get_multi(
        async_session, id__lte=5, return_as_model=True, schema_to_select=read_schema
    )

    assert all(
        isinstance(item, read_schema) for item in result["data"]
    ), "All items should be instances of the schema"
    assert all(
        item.id <= 5 for item in result["data"]
    ), "Should only include records with ID less than or equal to 5"


@pytest.mark.asyncio
async def test_get_multi_return_as_model_without_schema(
    async_session, test_model, test_data
):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    crud = FastCRUD(test_model)

    with pytest.raises(ValueError) as exc_info:
        await crud.get_multi(async_session, return_as_model=True)

    assert "schema_to_select must be provided when return_as_model is True" in str(
        exc_info.value
    )


@pytest.mark.asyncio
async def test_get_multi_handle_validation_error(async_session, test_model):
    invalid_test_data = {
        "name": "Extremely Long Name That Exceeds The Limits Of CustomCreateSchemaTest",
        "tier_id": 1,
    }
    async_session.add(test_model(**invalid_test_data))
    await async_session.commit()

    crud = FastCRUD(test_model)

    with pytest.raises(ValueError) as exc_info:
        await crud.get_multi(
            async_session, return_as_model=True, schema_to_select=CustomCreateSchemaTest
        )

    assert "Data validation error for schema CustomCreateSchemaTest:" in str(
        exc_info.value
    )


@pytest.mark.asyncio
async def test_read_items_with_advanced_filters(
        async_session, test_model, test_data
):
    for data in test_data:
        new_item = test_model(**data)
        async_session.add(new_item)
    await async_session.commit()

    crud = FastCRUD(test_model)

    # Test startswith filter
    name = "Ali"
    result = await crud.get_multi(async_session, name__startswith=name)

    assert len(result["data"]) > 0
    for item in result["data"]:
        assert item["name"].startswith(name)

    # Test with non-matching filter
    name = "Nothing"
    result = await crud.get_multi(async_session, name__startswith=name)

    assert len(result["data"]) == 0


@pytest.mark.asyncio
async def test_get_multi_or_filtering(async_session, test_model):
    # Create specific test data for OR filtering
    test_data = [
        {"name": "Alice", "tier_id": 1, "category_id": 1},
        {"name": "Bob", "tier_id": 2, "category_id": 1},
        {"name": "Charlie", "tier_id": 3, "category_id": 1},
        {"name": "David", "tier_id": 4, "category_id": 1},
        {"name": "Alice2", "tier_id": 5, "category_id": 1},
        {"name": "Frank", "tier_id": 6, "category_id": 1},
    ]

    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    crud = FastCRUD(test_model)

    # Test OR with simple conditions on tier_id
    result = await crud.get_multi(
        async_session,
        tier_id__or={"eq": 1, "eq": 6}
    )
    assert len(result["data"]) > 0
    assert all(item["tier_id"] in [1, 6] for item in result["data"])

    # Test OR with range conditions on tier_id
    result = await crud.get_multi(
        async_session,
        tier_id__or={"lt": 2, "gt": 5}
    )
    assert len(result["data"]) > 0
    assert all(
        item["tier_id"] < 2 or item["tier_id"] > 5
        for item in result["data"]
    )

    # Test OR with like conditions on name
    result = await crud.get_multi(
        async_session,
        name__or={"like": "Alice%", "like": "Frank%"}
    )
    assert len(result["data"]) > 0
    assert all(
        item["name"].startswith("Alice") or item["name"].startswith("Frank")
        for item in result["data"]
    )


@pytest.mark.asyncio
async def test_get_multi_not_filtering(async_session, test_model):
    # Create specific test data for NOT filtering
    test_data = [
        {"name": "Alice", "tier_id": 1, "category_id": 1},
        {"name": "Bob", "tier_id": 2, "category_id": 1},
        {"name": "Charlie", "tier_id": 3, "category_id": 1},
        {"name": "David", "tier_id": 4, "category_id": 1},
        {"name": "Eve", "tier_id": 5, "category_id": 1},
        {"name": "Frank", "tier_id": 6, "category_id": 1},
    ]

    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    crud = FastCRUD(test_model)

    # Test NOT with single condition
    result = await crud.get_multi(
        async_session,
        name__not={"eq": "Alice"}
    )
    assert len(result["data"]) > 0
    assert all(item["name"] != "Alice" for item in result["data"])

    # Test NOT with multiple conditions
    result = await crud.get_multi(
        async_session,
        tier_id__not={
            "between": (1, 3),
            "eq": 5
        }
    )
    assert len(result["data"]) > 0
    assert all(
        not (1 <= item["tier_id"] <= 3) and item["tier_id"] != 5
        for item in result["data"]
    )
    # Should only return records with tier_id = 4 or tier_id = 6
    assert all(item["tier_id"] in [4, 6] for item in result["data"])


@pytest.mark.asyncio
async def test_get_multi_basic_changed_multi_response_key(
    async_session, test_model, test_data
):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    total_count_query = await async_session.execute(
        select(func.count()).select_from(test_model)
    )
    total_count = total_count_query.scalar()

    new_multi_response_key = "items"
    crud = FastCRUD(test_model, multi_response_key=new_multi_response_key)
    result = await crud.get_multi(async_session)

    assert len(result[new_multi_response_key]) <= 100
    assert result["total_count"] == total_count


@pytest.mark.asyncio
async def test_get_multi_return_model_changed_multi_response_key(
    async_session, test_model, test_data, create_schema
):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    new_multi_response_key = "items"
    crud = FastCRUD(test_model, multi_response_key=new_multi_response_key)
    result = await crud.get_multi(
        async_session, return_as_model=True, schema_to_select=create_schema
    )

    assert all(
        isinstance(item, create_schema) for item in result[new_multi_response_key]
    )
