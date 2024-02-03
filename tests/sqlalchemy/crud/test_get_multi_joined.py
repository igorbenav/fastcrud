import pytest
from fastcrud.crud.fast_crud import FastCRUD
from ...sqlalchemy.conftest import (
    ModelTest,
    TierModel,
    CreateSchemaTest,
    TierSchemaTest,
    ReadSchemaTest,
)


@pytest.mark.asyncio
async def test_get_multi_joined_basic(async_session, test_data, test_data_tier):
    for tier_item in test_data_tier:
        async_session.add(TierModel(**tier_item))
    await async_session.commit()

    for user_item in test_data:
        async_session.add(ModelTest(**user_item))
    await async_session.commit()

    crud = FastCRUD(ModelTest)
    result = await crud.get_multi_joined(
        db=async_session,
        join_model=TierModel,
        join_prefix="tier_",
        schema_to_select=CreateSchemaTest,
        join_schema_to_select=TierSchemaTest,
        offset=0,
        limit=10,
    )

    assert len(result["data"]) == min(10, len(test_data))
    assert result["total_count"] == len(test_data)
    assert all("tier_name" in item for item in result["data"])


@pytest.mark.asyncio
async def test_get_multi_joined_sorting(async_session, test_data, test_data_tier):
    for tier_item in test_data_tier:
        async_session.add(TierModel(**tier_item))
    await async_session.commit()

    for user_item in test_data:
        async_session.add(ModelTest(**user_item))
    await async_session.commit()

    crud = FastCRUD(ModelTest)
    result = await crud.get_multi_joined(
        db=async_session,
        join_model=TierModel,
        join_prefix="tier_",
        schema_to_select=CreateSchemaTest,
        join_schema_to_select=TierSchemaTest,
        sort_columns=["name"],
        sort_orders=["asc"],
        offset=0,
        limit=10,
    )

    assert len(result["data"]) <= 10
    assert all(
        result["data"][i]["name"] <= result["data"][i + 1]["name"]
        for i in range(len(result["data"]) - 1)
    )


@pytest.mark.asyncio
async def test_get_multi_joined_filtering(async_session, test_data, test_data_tier):
    # Assuming there's a user with a specific name in test_data
    specific_user_name = "Charlie"
    for tier_item in test_data_tier:
        async_session.add(TierModel(**tier_item))
    await async_session.commit()

    for user_item in test_data:
        async_session.add(ModelTest(**user_item))
    await async_session.commit()

    crud = FastCRUD(ModelTest)
    result = await crud.get_multi_joined(
        db=async_session,
        join_model=TierModel,
        join_prefix="tier_",
        schema_to_select=CreateSchemaTest,
        join_schema_to_select=TierSchemaTest,
        name=specific_user_name,  # Filter based on ModelTest attribute
        offset=0,
        limit=10,
    )

    assert len(result["data"]) <= 10
    assert all(item["name"] == specific_user_name for item in result["data"])


@pytest.mark.asyncio
async def test_get_multi_joined_different_join_types(
    async_session, test_data, test_data_tier
):
    for tier_item in test_data_tier:
        async_session.add(TierModel(**tier_item))
    await async_session.commit()

    for user_item in test_data:
        async_session.add(ModelTest(**user_item))
    await async_session.commit()

    crud = FastCRUD(ModelTest)
    for join_type in ["left", "inner"]:
        result = await crud.get_multi_joined(
            db=async_session,
            join_model=TierModel,
            join_type=join_type,
            schema_to_select=CreateSchemaTest,
            join_schema_to_select=TierSchemaTest,
            offset=0,
            limit=10,
        )

        assert len(result["data"]) <= 10


@pytest.mark.asyncio
async def test_get_multi_joined_return_model(async_session, test_data, test_data_tier):
    for tier_item in test_data_tier:
        async_session.add(TierModel(**tier_item))
    await async_session.commit()

    for user_item in test_data:
        async_session.add(ModelTest(**user_item))
    await async_session.commit()

    crud = FastCRUD(ModelTest)
    result = await crud.get_multi_joined(
        db=async_session,
        join_model=TierModel,
        schema_to_select=CreateSchemaTest,
        join_schema_to_select=TierSchemaTest,
        return_as_model=True,
        offset=0,
        limit=10,
    )

    assert len(result["data"]) <= 10
    assert all(isinstance(item, CreateSchemaTest) for item in result["data"])


@pytest.mark.asyncio
async def test_get_multi_joined_no_results(async_session, test_data, test_data_tier):
    for tier_item in test_data_tier:
        async_session.add(TierModel(**tier_item))
    await async_session.commit()

    for user_item in test_data:
        async_session.add(ModelTest(**user_item))
    await async_session.commit()

    crud = FastCRUD(ModelTest)
    result = await crud.get_multi_joined(
        db=async_session,
        join_model=TierModel,
        schema_to_select=CreateSchemaTest,
        join_schema_to_select=TierSchemaTest,
        offset=0,
        limit=10,
        name="NonExistingName",
    )

    assert len(result["data"]) == 0
    assert result["total_count"] == 0


@pytest.mark.asyncio
async def test_get_multi_joined_large_offset(async_session, test_data, test_data_tier):
    for tier_item in test_data_tier:
        async_session.add(TierModel(**tier_item))
    await async_session.commit()

    for user_item in test_data:
        async_session.add(ModelTest(**user_item))
    await async_session.commit()

    crud = FastCRUD(ModelTest)
    result = await crud.get_multi_joined(
        db=async_session,
        join_model=TierModel,
        schema_to_select=CreateSchemaTest,
        join_schema_to_select=TierSchemaTest,
        offset=1000,
        limit=10,
    )

    assert len(result["data"]) == 0


@pytest.mark.asyncio
async def test_get_multi_joined_invalid_limit_offset(
    async_session, test_data, test_data_tier
):
    for tier_item in test_data_tier:
        async_session.add(TierModel(**tier_item))
    await async_session.commit()

    for user_item in test_data:
        async_session.add(ModelTest(**user_item))
    await async_session.commit()

    crud = FastCRUD(ModelTest)
    with pytest.raises(ValueError):
        await crud.get_multi_joined(
            db=async_session,
            join_model=TierModel,
            schema_to_select=CreateSchemaTest,
            join_schema_to_select=TierSchemaTest,
            offset=-1,
            limit=10,
        )
    with pytest.raises(ValueError):
        await crud.get_multi_joined(
            db=async_session,
            join_model=TierModel,
            schema_to_select=CreateSchemaTest,
            join_schema_to_select=TierSchemaTest,
            offset=0,
            limit=-1,
        )


@pytest.mark.asyncio
async def test_get_multi_joined_advanced_filtering(
    async_session, test_data, test_data_tier
):
    for tier_item in test_data_tier:
        async_session.add(TierModel(**tier_item))
    await async_session.commit()

    for user_item in test_data:
        async_session.add(ModelTest(**user_item))
    await async_session.commit()

    crud = FastCRUD(ModelTest)
    advanced_filter_result = await crud.get_multi_joined(
        db=async_session,
        join_model=TierModel,
        schema_to_select=ReadSchemaTest,
        join_schema_to_select=TierSchemaTest,
        join_prefix="tier_",
        offset=0,
        limit=10,
        id__gt=5,
    )

    assert (
        len(advanced_filter_result["data"]) > 0
    ), "Should fetch records with ID greater than 5"
    assert all(
        item["id"] > 5 for item in advanced_filter_result["data"]
    ), "All fetched records should meet the advanced filter condition"
