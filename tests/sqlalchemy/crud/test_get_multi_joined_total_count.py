import pytest
from fastcrud import FastCRUD, JoinConfig
from tests.sqlalchemy.conftest import ModelTest, TierModel, CreateSchemaTest, TierSchemaTest


@pytest.mark.asyncio
async def test_get_multi_joined_total_count_with_join_model(async_session, test_data, test_data_tier):
    """Test that total_count is correct when using join_model parameter."""
    # Setup test data
    for tier_item in test_data_tier:
        async_session.add(TierModel(**tier_item))
    await async_session.commit()

    for user_item in test_data:
        async_session.add(ModelTest(**user_item))
    await async_session.commit()

    crud = FastCRUD(ModelTest)
    
    # Use join_model parameter
    result_with_join_model = await crud.get_multi_joined(
        db=async_session,
        join_model=TierModel,
        join_prefix="tier_",
        schema_to_select=CreateSchemaTest,
        join_schema_to_select=TierSchemaTest,
        offset=0,
        limit=5,  # Use a smaller limit to ensure we're not just getting all records
    )
    
    # Use joins_config parameter
    result_with_joins_config = await crud.get_multi_joined(
        db=async_session,
        schema_to_select=CreateSchemaTest,
        joins_config=[
            JoinConfig(
                model=TierModel,
                join_on=ModelTest.tier_id == TierModel.id,
                join_prefix="tier_",
                schema_to_select=TierSchemaTest,
                join_type="left",
            )
        ],
        offset=0,
        limit=5,  # Same limit as above
    )
    
    # Both approaches should return the same total_count
    assert result_with_join_model["total_count"] == len(test_data)
    assert result_with_joins_config["total_count"] == len(test_data)
    assert result_with_join_model["total_count"] == result_with_joins_config["total_count"]
    
    # Data length should be limited by the limit parameter
    assert len(result_with_join_model["data"]) == 5
    assert len(result_with_joins_config["data"]) == 5


@pytest.mark.asyncio
async def test_get_multi_joined_total_count_with_filters(async_session, test_data, test_data_tier):
    """Test that total_count is correct when using filters with join_model parameter."""
    # Setup test data
    for tier_item in test_data_tier:
        async_session.add(TierModel(**tier_item))
    await async_session.commit()

    for user_item in test_data:
        async_session.add(ModelTest(**user_item))
    await async_session.commit()

    crud = FastCRUD(ModelTest)
    
    # Count how many records have tier_id=1
    expected_count = sum(1 for item in test_data if item["tier_id"] == 1)
    
    # Use join_model parameter with filter
    result_with_join_model = await crud.get_multi_joined(
        db=async_session,
        join_model=TierModel,
        join_prefix="tier_",
        schema_to_select=CreateSchemaTest,
        join_schema_to_select=TierSchemaTest,
        offset=0,
        limit=10,
        tier_id=1,  # Filter by tier_id
    )
    
    # Use joins_config parameter with same filter
    result_with_joins_config = await crud.get_multi_joined(
        db=async_session,
        schema_to_select=CreateSchemaTest,
        joins_config=[
            JoinConfig(
                model=TierModel,
                join_on=ModelTest.tier_id == TierModel.id,
                join_prefix="tier_",
                schema_to_select=TierSchemaTest,
                join_type="left",
            )
        ],
        offset=0,
        limit=10,
        tier_id=1,  # Same filter
    )
    
    # Both approaches should return the same filtered total_count
    assert result_with_join_model["total_count"] == expected_count
    assert result_with_joins_config["total_count"] == expected_count
    assert result_with_join_model["total_count"] == result_with_joins_config["total_count"]
