import pytest
from fastcrud import FastCRUD, JoinConfig, aliased
from ...sqlmodel.conftest import (
    ModelTest,
    TierModel,
    CreateSchemaTest,
    TierSchemaTest,
    ReadSchemaTest,
    CategoryModel,
    CategorySchemaTest,
    BookingModel,
    BookingSchema,
    Project,
    Participant,
    ProjectsParticipantsAssociation,
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
        name=specific_user_name,
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


@pytest.mark.asyncio
async def test_get_multi_joined_with_additional_join_model(
    async_session, test_data, test_data_tier, test_data_category
):
    for category_item in test_data_category:
        async_session.add(CategoryModel(**category_item))
    await async_session.commit()

    for tier_item in test_data_tier:
        async_session.add(TierModel(**tier_item))
    await async_session.commit()

    for user_item in test_data:
        async_session.add(ModelTest(**user_item))
    await async_session.commit()

    crud = FastCRUD(ModelTest)
    result = await crud.get_multi_joined(
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
        schema_to_select=ReadSchemaTest,
        offset=0,
        limit=10,
    )

    assert len(result["data"]) == min(10, len(test_data))
    assert result["total_count"] == len(test_data)
    assert all(
        "tier_name" in item and "category_name" in item for item in result["data"]
    )


@pytest.mark.asyncio
async def test_get_multi_joined_with_aliases(
    async_session, test_data, test_data_tier, test_data_category, test_data_booking
):
    for tier_item in test_data_tier:
        async_session.add(TierModel(**tier_item))
    for category_item in test_data_category:
        async_session.add(CategoryModel(**category_item))
    for user_item in test_data:
        async_session.add(ModelTest(**user_item))
    for booking_item in test_data_booking:
        async_session.add(BookingModel(**booking_item))
    await async_session.commit()

    crud = FastCRUD(BookingModel)

    expected_owner_name = "Charlie"
    expected_user_name = "Alice"

    owner_alias = aliased(ModelTest, name="owner")
    user_alias = aliased(ModelTest, name="user")

    result = await crud.get_multi_joined(
        db=async_session,
        schema_to_select=BookingSchema,
        joins_config=[
            JoinConfig(
                model=ModelTest,
                join_on=BookingModel.owner_id == owner_alias.id,
                join_prefix="owner_",
                alias=owner_alias,
                schema_to_select=ReadSchemaTest,
            ),
            JoinConfig(
                model=ModelTest,
                join_on=BookingModel.user_id == user_alias.id,
                join_prefix="user_",
                alias=user_alias,
                schema_to_select=ReadSchemaTest,
            ),
        ],
        offset=0,
        limit=10,
        sort_columns=["booking_date"],
        sort_orders=["asc"],
    )

    assert "data" in result and isinstance(
        result["data"], list
    ), "The result should have a 'data' key with a list of records."
    for booking in result["data"]:
        assert (
            "owner_name" in booking
        ), "Each record should include 'owner_name' from the joined owner ModelTest data."
        assert (
            "user_name" in booking
        ), "Each record should include 'user_name' from the joined user ModelTest data."
    assert result is not None
    assert result["total_count"] >= 1, "Expected at least one booking record"
    first_result = result["data"][0]
    assert (
        first_result["owner_name"] == expected_owner_name
    ), "Owner name does not match expected value"
    assert (
        first_result["user_name"] == expected_user_name
    ), "User name does not match expected value"


@pytest.mark.asyncio
async def test_get_multi_joined_with_aliases_no_schema(
    async_session, test_data, test_data_tier, test_data_category, test_data_booking
):
    for tier_item in test_data_tier:
        async_session.add(TierModel(**tier_item))
    for category_item in test_data_category:
        async_session.add(CategoryModel(**category_item))
    for user_item in test_data:
        async_session.add(ModelTest(**user_item))
    for booking_item in test_data_booking:
        async_session.add(BookingModel(**booking_item))
    await async_session.commit()

    crud = FastCRUD(BookingModel)

    expected_owner_name = "Charlie"
    expected_user_name = "Alice"

    owner_alias = aliased(ModelTest, name="owner")
    user_alias = aliased(ModelTest, name="user")

    result = await crud.get_multi_joined(
        db=async_session,
        schema_to_select=BookingSchema,
        joins_config=[
            JoinConfig(
                model=ModelTest,
                join_on=BookingModel.owner_id == owner_alias.id,
                join_prefix="owner_",
                alias=owner_alias,
            ),
            JoinConfig(
                model=ModelTest,
                join_on=BookingModel.user_id == user_alias.id,
                join_prefix="user_",
                alias=user_alias,
            ),
        ],
        offset=0,
        limit=10,
        sort_columns=["booking_date"],
        sort_orders=["asc"],
    )

    assert "data" in result and isinstance(
        result["data"], list
    ), "The result should have a 'data' key with a list of records."
    for booking in result["data"]:
        assert (
            "owner_name" in booking
        ), "Each record should include 'owner_name' from the joined owner ModelTest data."
        assert (
            "user_name" in booking
        ), "Each record should include 'user_name' from the joined user ModelTest data."
    assert result is not None
    assert result["total_count"] >= 1, "Expected at least one booking record"
    first_result = result["data"][0]
    assert (
        first_result["owner_name"] == expected_owner_name
    ), "Owner name does not match expected value"
    assert (
        first_result["user_name"] == expected_user_name
    ), "User name does not match expected value"


@pytest.mark.asyncio
async def test_many_to_many_joined(async_session):
    project1 = Project(id=1, name="Project 1", description="First Project")
    project2 = Project(id=2, name="Project 2", description="Second Project")

    participant1 = Participant(id=1, name="Participant 1", role="Developer")
    participant2 = Participant(id=2, name="Participant 2", role="Designer")

    async_session.add_all([project1, project2, participant1, participant2])
    await async_session.commit()

    projects_participants1 = ProjectsParticipantsAssociation(
        project_id=1, participant_id=1
    )
    projects_participants2 = ProjectsParticipantsAssociation(
        project_id=1, participant_id=2
    )
    projects_participants3 = ProjectsParticipantsAssociation(
        project_id=2, participant_id=1
    )

    async_session.add_all(
        [projects_participants1, projects_participants2, projects_participants3]
    )
    await async_session.commit()

    crud_project = FastCRUD(Project)

    join_condition_1 = Project.id == ProjectsParticipantsAssociation.project_id
    join_condition_2 = ProjectsParticipantsAssociation.participant_id == Participant.id

    joins_config = [
        JoinConfig(
            model=ProjectsParticipantsAssociation,
            join_on=join_condition_1,
            join_type="inner",
            join_prefix="pp_",
        ),
        JoinConfig(
            model=Participant,
            join_on=join_condition_2,
            join_type="inner",
            join_prefix="participant_",
        ),
    ]

    records = await crud_project.get_multi_joined(
        db=async_session,
        joins_config=joins_config,
    )

    expected_results = [
        {
            "project_id": 1,
            "participant_id": 1,
            "participant_name": "Participant 1",
            "participant_role": "Developer",
        },
        {
            "project_id": 1,
            "participant_id": 2,
            "participant_name": "Participant 2",
            "participant_role": "Designer",
        },
        {
            "project_id": 2,
            "participant_id": 1,
            "participant_name": "Participant 1",
            "participant_role": "Developer",
        },
    ]

    assert len(records["data"]) == 3, "Expected three project-participant associations"
    assert (
        len(records["data"]) == records["total_count"]
    ), "Number of records should be the same in total_count and len"

    for expected, actual in zip(expected_results, records["data"]):
        assert (
            actual["id"] == expected["project_id"]
        ), f"Project ID mismatch. Expected: {expected['project_id']}, Got: {actual['id']}"
        assert (
            actual["participant_id"] == expected["participant_id"]
        ), f"Participant ID mismatch. Expected: {expected['participant_id']}, Got: {actual['participant_id']}"
        assert (
            actual["participant_name"] == expected["participant_name"]
        ), f"Participant name mismatch. Expected: {expected['participant_name']}, Got: {actual['participant_name']}"
        assert (
            actual["participant_role"] == expected["participant_role"]
        ), f"Participant role mismatch. Expected: {expected['participant_role']}, Got: {actual['participant_role']}"
