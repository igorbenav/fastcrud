import pytest
from sqlalchemy import and_
from fastcrud.crud.crud_base import CRUDBase
from ..conftest import ModelTest, TierModel, CreateSchemaTest, TierSchemaTest


@pytest.mark.asyncio
async def test_get_joined_basic(async_session, test_data, test_data_tier):
    for tier_item in test_data_tier:
        async_session.add(TierModel(**tier_item))
    await async_session.commit()

    for user_item in test_data:
        async_session.add(ModelTest(**user_item))
    await async_session.commit()

    crud = CRUDBase(ModelTest)
    result = await crud.get_joined(
        db=async_session,
        join_model=TierModel,
        join_prefix="tier_",
        schema_to_select=CreateSchemaTest,
        join_schema_to_select=TierSchemaTest,
    )

    assert result is not None
    assert "name" in result
    assert "tier_name" in result


@pytest.mark.asyncio
async def test_get_joined_custom_condition(async_session, test_data, test_data_tier):
    for tier_item in test_data_tier:
        async_session.add(TierModel(**tier_item))
    await async_session.commit()

    user_data_with_condition = [item for item in test_data if item["name"] == "Alice"]
    for user_item in user_data_with_condition:
        async_session.add(ModelTest(**user_item))
    await async_session.commit()

    crud = CRUDBase(ModelTest)
    result = await crud.get_joined(
        db=async_session,
        join_model=TierModel,
        join_on=and_(ModelTest.tier_id == TierModel.id),
        join_prefix="tier_",
        schema_to_select=CreateSchemaTest,
        join_schema_to_select=TierSchemaTest,
        name="Alice",
    )

    assert result is not None
    assert result["name"] == "Alice"
    assert "tier_name" in result


@pytest.mark.asyncio
async def test_get_joined_with_prefix(async_session, test_data, test_data_tier):
    for tier_item in test_data_tier:
        async_session.add(TierModel(**tier_item))
    await async_session.commit()

    for user_item in test_data:
        async_session.add(ModelTest(**user_item))
    await async_session.commit()

    crud = CRUDBase(ModelTest)
    result = await crud.get_joined(
        db=async_session,
        join_model=TierModel,
        join_prefix="tier_",
        schema_to_select=CreateSchemaTest,
        join_schema_to_select=TierSchemaTest,
    )

    assert result is not None
    assert "name" in result
    assert "tier_name" in result


@pytest.mark.asyncio
async def test_get_joined_different_join_types(
    async_session, test_data, test_data_tier
):
    for tier_item in test_data_tier:
        async_session.add(TierModel(**tier_item))
    await async_session.commit()

    for user_item in test_data:
        async_session.add(ModelTest(**user_item))
    await async_session.commit()

    crud = CRUDBase(ModelTest)
    result_left = await crud.get_joined(
        db=async_session,
        join_model=TierModel,
        join_type="left",
        schema_to_select=CreateSchemaTest,
        join_schema_to_select=TierSchemaTest,
    )

    result_inner = await crud.get_joined(
        db=async_session,
        join_model=TierModel,
        join_type="inner",
        schema_to_select=CreateSchemaTest,
        join_schema_to_select=TierSchemaTest,
    )

    assert result_left is not None
    assert result_inner is not None


@pytest.mark.asyncio
async def test_get_joined_with_filters(async_session, test_data, test_data_tier):
    for tier_item in test_data_tier:
        async_session.add(TierModel(**tier_item))
    await async_session.commit()

    for user_item in test_data:
        async_session.add(ModelTest(**user_item))
    await async_session.commit()

    crud = CRUDBase(ModelTest)
    result = await crud.get_joined(
        db=async_session,
        join_model=TierModel,
        schema_to_select=CreateSchemaTest,
        join_schema_to_select=TierSchemaTest,
        name="Alice",
    )

    assert result is not None
    assert result["name"] == "Alice"
