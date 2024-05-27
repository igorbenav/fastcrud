import pytest
from sqlalchemy import and_
from fastcrud import FastCRUD, JoinConfig, aliased
from ...sqlalchemy.conftest import (
    ModelTest,
    TierModel,
    CreateSchemaTest,
    TierSchemaTest,
    CategoryModel,
    CategorySchemaTest,
    BookingModel,
    BookingSchema,
    ReadSchemaTest,
    Article,
    Card,
)


@pytest.mark.asyncio
async def test_get_joined_basic(async_session, test_data, test_data_tier):
    for tier_item in test_data_tier:
        async_session.add(TierModel(**tier_item))
    await async_session.commit()

    for user_item in test_data:
        async_session.add(ModelTest(**user_item))
    await async_session.commit()

    crud = FastCRUD(ModelTest)
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

    crud = FastCRUD(ModelTest)
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

    crud = FastCRUD(ModelTest)
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

    crud = FastCRUD(ModelTest)
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

    crud = FastCRUD(ModelTest)
    result = await crud.get_joined(
        db=async_session,
        join_model=TierModel,
        schema_to_select=CreateSchemaTest,
        join_schema_to_select=TierSchemaTest,
        name="Alice",
    )

    assert result is not None
    assert result["name"] == "Alice"


@pytest.mark.asyncio
async def test_update_multiple_records_allow_multiple(
    async_session, test_model, test_data
):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    crud = FastCRUD(test_model)
    await crud.update(
        db=async_session,
        object={"name": "Updated Name"},
        allow_multiple=True,
        name="Alice",
    )

    updated_records = await crud.get_multi(db=async_session, name="Updated Name")
    assert (
        len(updated_records["data"]) > 1
    ), "Should update multiple records when allow_multiple is True"


@pytest.mark.asyncio
async def test_count_with_advanced_filters(async_session, test_model, test_data):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    crud = FastCRUD(test_model)
    count_gt = await crud.count(async_session, id__gt=1)
    assert count_gt > 0, "Should count records with ID greater than 1"

    count_lt = await crud.count(async_session, id__lt=10)
    assert count_lt > 0, "Should count records with ID less than 10"


@pytest.mark.asyncio
async def test_get_joined_multiple_models(
    async_session, test_data, test_data_tier, test_data_category
):
    for tier_item in test_data_tier:
        async_session.add(TierModel(**tier_item))
    await async_session.commit()

    for category_item in test_data_category:
        async_session.add(CategoryModel(**category_item))
    await async_session.commit()

    for user_item in test_data:
        user_item_modified = user_item.copy()
        user_item_modified["category_id"] = 1
        async_session.add(ModelTest(**user_item_modified))
    await async_session.commit()

    crud = FastCRUD(ModelTest)
    result = await crud.get_joined(
        db=async_session,
        joins_config=[
            JoinConfig(
                model=TierModel,
                join_prefix="tier_",
                schema_to_select=TierSchemaTest,
                join_on=ModelTest.tier_id == TierModel.id,
                join_type="left",
            ),
            JoinConfig(
                model=CategoryModel,
                join_prefix="category_",
                schema_to_select=CategorySchemaTest,
                join_on=ModelTest.category_id == CategoryModel.id,
                join_type="left",
            ),
        ],
        schema_to_select=CreateSchemaTest,
    )

    assert result is not None
    assert "name" in result
    assert "tier_name" in result
    assert "category_name" in result


@pytest.mark.asyncio
async def test_get_joined_with_aliases(
    async_session, test_data, test_data_tier, test_data_category, test_data_booking
):
    for tier_item in test_data_tier:
        async_session.add(TierModel(**tier_item))
    for category_item in test_data_category:
        async_session.add(CategoryModel(**category_item))
    for user_item in test_data:
        async_session.add(ModelTest(**user_item))
    await async_session.commit()

    for booking_item in test_data_booking:
        async_session.add(BookingModel(**booking_item))
    await async_session.commit()

    crud = FastCRUD(BookingModel)

    specific_booking_id = 1
    expected_owner_name = "Charlie"
    expected_user_name = "Alice"

    owner = aliased(ModelTest, name="owner")
    user = aliased(ModelTest, name="user")

    result = await crud.get_joined(
        db=async_session,
        schema_to_select=BookingSchema,
        joins_config=[
            JoinConfig(
                model=ModelTest,
                join_on=BookingModel.owner_id == owner.id,
                join_prefix="owner_",
                alias=owner,
                schema_to_select=ReadSchemaTest,
            ),
            JoinConfig(
                model=ModelTest,
                join_on=BookingModel.user_id == user.id,
                join_prefix="user_",
                alias=user,
                schema_to_select=ReadSchemaTest,
            ),
        ],
        id=specific_booking_id,
    )

    assert result is not None
    assert (
        result["owner_name"] == expected_owner_name
    ), "Owner name does not match expected value"
    assert (
        result["user_name"] == expected_user_name
    ), "User name does not match expected value"


@pytest.mark.asyncio
async def test_get_joined_with_aliases_no_schema(
    async_session, test_data, test_data_tier, test_data_category, test_data_booking
):
    for tier_item in test_data_tier:
        async_session.add(TierModel(**tier_item))
    for category_item in test_data_category:
        async_session.add(CategoryModel(**category_item))
    for user_item in test_data:
        async_session.add(ModelTest(**user_item))
    await async_session.commit()

    for booking_item in test_data_booking:
        async_session.add(BookingModel(**booking_item))
    await async_session.commit()

    crud = FastCRUD(BookingModel)

    specific_booking_id = 1
    expected_owner_name = "Charlie"
    expected_user_name = "Alice"

    owner = aliased(ModelTest, name="owner")
    user = aliased(ModelTest, name="user")

    result = await crud.get_joined(
        db=async_session,
        schema_to_select=BookingSchema,
        joins_config=[
            JoinConfig(
                model=ModelTest,
                join_on=BookingModel.owner_id == owner.id,
                join_prefix="owner_",
                alias=owner,
            ),
            JoinConfig(
                model=ModelTest,
                join_on=BookingModel.user_id == user.id,
                join_prefix="user_",
                alias=user,
            ),
        ],
        id=specific_booking_id,
    )

    assert result is not None
    assert (
        result["owner_name"] == expected_owner_name
    ), "Owner name does not match expected value"
    assert (
        result["user_name"] == expected_user_name
    ), "User name does not match expected value"


@pytest.mark.asyncio
async def test_get_joined_with_both_single_and_joins_config_raises_value_error(
    async_session, test_data
):
    crud = FastCRUD(ModelTest)

    with pytest.raises(ValueError) as excinfo:
        await crud.get_joined(
            db=async_session,
            join_model=TierModel,
            joins_config=[
                JoinConfig(
                    model=TierModel,
                    join_on=ModelTest.tier_id == TierModel.id,
                )
            ],
        )

    assert (
        "Cannot use both single join parameters and joins_config simultaneously."
        in str(excinfo.value)
    )


@pytest.mark.asyncio
async def test_get_joined_without_join_model_or_joins_config_raises_value_error(
    async_session, test_data
):
    crud = FastCRUD(ModelTest)

    with pytest.raises(ValueError) as excinfo:
        await crud.get_joined(db=async_session)

    assert "You need one of join_model or joins_config." in str(excinfo.value)


@pytest.mark.asyncio
async def test_get_joined_with_unsupported_join_type_raises_value_error(
    async_session, test_data
):
    crud = FastCRUD(ModelTest)

    with pytest.raises(ValueError) as excinfo:
        await crud.get_joined(
            db=async_session,
            join_model=TierModel,
            join_type="unsupported_type",
        )

    assert "Unsupported join type" in str(excinfo.value)


@pytest.mark.asyncio
async def test_get_joined_returns_none_when_no_record_matches(async_session, test_data):
    crud = FastCRUD(ModelTest)

    result = await crud.get_joined(
        db=async_session,
        join_model=TierModel,
        schema_to_select=CreateSchemaTest,
        join_schema_to_select=TierSchemaTest,
        name="Nonexistent Name",
    )

    assert result is None


@pytest.mark.asyncio
async def test_get_joined_with_joined_model_filters(
    async_session, test_data, test_data_tier
):
    for tier_item in test_data_tier:
        async_session.add(TierModel(**tier_item))
    await async_session.commit()

    for user_item in test_data:
        async_session.add(ModelTest(**user_item))
    await async_session.commit()

    crud = FastCRUD(ModelTest)

    join_filters = {"name": "Premium"}

    result = await crud.get_joined(
        db=async_session,
        join_model=TierModel,
        join_filters=join_filters,
        schema_to_select=CreateSchemaTest,
        join_schema_to_select=TierSchemaTest,
        join_prefix="tier_",
    )

    assert result is not None, "Expected to find at least one matching record"
    assert (
        result["tier_name"] == "Premium"
    ), "Expected joined record to meet the filter criteria"


@pytest.mark.asyncio
async def test_get_joined_nest_joins(async_session, test_data, test_data_tier):
    for tier_item in test_data_tier:
        async_session.add(TierModel(**tier_item))
    await async_session.commit()

    for user_item in test_data:
        async_session.add(ModelTest(**user_item))
    await async_session.commit()

    crud = FastCRUD(ModelTest)

    result = await crud.get_joined(
        db=async_session,
        join_model=TierModel,
        join_prefix="tier_",
        schema_to_select=CreateSchemaTest,
        join_schema_to_select=TierSchemaTest,
        nest_joins=True,
    )

    assert result is not None, "No result returned, expected a nested join result."
    assert "name" in result, "Expected primary model field 'name' in result."
    assert "tier" in result, "Expected nested 'tier' key in result for joined fields."
    assert (
        "name" in result["tier"]
    ), "Expected 'name' inside nested 'tier' dictionary from TierModel."
    assert (
        "tier_name" not in result
    ), "'tier_name' should not be at the top level in the result."


@pytest.mark.asyncio
async def test_get_joined_nested_no_prefix_provided(
    async_session, test_data, test_data_tier
):
    for tier_item in test_data_tier:
        async_session.add(TierModel(**tier_item))
    await async_session.commit()

    for user_item in test_data:
        async_session.add(ModelTest(**user_item))
    await async_session.commit()

    crud = FastCRUD(ModelTest)
    result = await crud.get_joined(
        db=async_session,
        join_model=TierModel,
        schema_to_select=CreateSchemaTest,
        join_schema_to_select=TierSchemaTest,
        nest_joins=True,
    )

    assert result is not None, "No result returned, expected a nested join result."
    assert "name" in result, "Expected primary model field 'name' in result."
    assert (
        "name" in result[TierModel.__tablename__]
    ), f"Expected 'name' field inside nested '{TierModel.__tablename__}' dictionary."


@pytest.mark.asyncio
async def test_get_joined_no_prefix_no_nesting(
    async_session, test_data, test_data_tier
):
    for tier_item in test_data_tier:
        async_session.add(TierModel(**tier_item))
    await async_session.commit()

    for user_item in test_data:
        async_session.add(ModelTest(**user_item))
    await async_session.commit()

    crud = FastCRUD(ModelTest)

    result = await crud.get_joined(
        db=async_session,
        join_model=TierModel,
        schema_to_select=CreateSchemaTest,
        join_schema_to_select=TierSchemaTest,
    )

    assert result is not None, "Expected to retrieve a result from joined query."
    assert (
        "name" in result
    ), "Expected 'name' field from the primary model in the result."
    assert "tier_id" in result, "Expected 'tier_id' (foreign key) in the result."
    assert (
        "tier_name" not in result
    ), "Field 'tier_name' should not exist unless specifically prefixed or nested."


@pytest.mark.asyncio
async def test_get_joined_card_with_articles(async_session):
    card = Card(title="Test Card")
    async_session.add(card)
    async_session.add_all(
        [
            Article(title="Article 1", card=card),
            Article(title="Article 2", card=card),
            Article(title="Article 3", card=card),
        ]
    )
    await async_session.commit()

    card_crud = FastCRUD(Card)

    result = await card_crud.get_joined(
        db=async_session,
        nest_joins=True,
        joins_config=[
            JoinConfig(
                model=Article,
                join_on=Article.card_id == Card.id,
                join_prefix="articles_",
                join_type="left",
                relationship_type="one-to-many",
            )
        ],
    )

    assert result is not None, "No data returned from the database."
    assert "title" in result, "Card title should be present in the result."
    assert "articles" in result, "Articles should be nested under 'articles'."
    assert isinstance(result["articles"], list), "Articles should be a list."
    assert len(result["articles"]) == 3, "There should be three articles."
    assert all(
        "title" in article for article in result["articles"]
    ), "Each article should have a title."
