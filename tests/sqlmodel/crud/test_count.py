import pytest
from unittest.mock import patch
from fastcrud.crud.fast_crud import FastCRUD
from fastcrud import JoinConfig
from ..conftest import Project, Participant, ProjectsParticipantsAssociation


@pytest.mark.asyncio
async def test_count_no_filters(async_session, test_model, test_data):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    crud = FastCRUD(test_model)
    count = await crud.count(async_session)

    assert count == len(test_data)


@pytest.mark.asyncio
async def test_count_with_filters(async_session, test_model, test_data):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    filter_criteria = test_data[0]
    crud = FastCRUD(test_model)
    count = await crud.count(async_session, **filter_criteria)

    assert count == 1


@pytest.mark.asyncio
async def test_count_no_matching_records(async_session, test_model):
    non_existent_filter = {"name": "NonExistentName"}
    crud = FastCRUD(test_model)
    count = await crud.count(async_session, **non_existent_filter)

    assert count == 0


@pytest.mark.asyncio
async def test_count_with_advanced_filters(async_session, test_model, test_data):
    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    crud = FastCRUD(test_model)

    count_gt = await crud.count(async_session, tier_id__gt=1)
    assert count_gt == len([item for item in test_data if item["tier_id"] > 1])

    count_lt = await crud.count(async_session, tier_id__lt=2)
    assert count_lt == len([item for item in test_data if item["tier_id"] < 2])

    count_ne = await crud.count(async_session, name__ne=test_data[0]["name"])
    assert count_ne == len(test_data) - 1


@pytest.mark.asyncio
async def test_count_with_joins_config_many_to_many(async_session):
    project1 = Project(name="Project Alpha", description="First Project")
    project2 = Project(name="Project Beta", description="Second Project")
    project3 = Project(name="Project Gamma", description="Third Project")
    participant1 = Participant(name="John Doe", role="Developer")
    participant2 = Participant(name="Jane Doe", role="Designer")

    async_session.add_all([project1, project2, project3, participant1, participant2])
    await async_session.commit()

    async_session.add_all(
        [
            ProjectsParticipantsAssociation(
                project_id=project1.id, participant_id=participant1.id
            ),
            ProjectsParticipantsAssociation(
                project_id=project2.id, participant_id=participant1.id
            ),
            ProjectsParticipantsAssociation(
                project_id=project3.id, participant_id=participant2.id
            ),
        ]
    )
    await async_session.commit()

    crud_project = FastCRUD(Project)

    joins_config = [
        JoinConfig(
            model=ProjectsParticipantsAssociation,
            join_on=Project.id == ProjectsParticipantsAssociation.project_id,
            join_type="inner",
            join_prefix="association_",
        ),
        JoinConfig(
            model=Participant,
            join_on=ProjectsParticipantsAssociation.participant_id == Participant.id,
            join_type="inner",
            join_prefix="participant_",
            filters={"id": 1},
        ),
    ]

    count = await crud_project.count(
        async_session, joins_config=joins_config, participant_id=1
    )

    assert (
        count == 2
    ), f"Expected to find 2 projects associated with 'John Doe', found {count}"


@pytest.mark.asyncio
async def test_count_with_joins_and_filters_executes_primary_filter(async_session):
    project1 = Project(name="Project Delta", description="Fourth Project")
    project2 = Project(name="Project Epsilon", description="Fifth Project")
    participant1 = Participant(name="Alex Doe", role="Manager")
    participant2 = Participant(name="Chris Doe", role="Analyst")

    async_session.add_all([project1, project2, participant1, participant2])
    await async_session.commit()

    async_session.add_all(
        [
            ProjectsParticipantsAssociation(
                project_id=project1.id, participant_id=participant1.id
            ),
            ProjectsParticipantsAssociation(
                project_id=project2.id, participant_id=participant2.id
            ),
        ]
    )
    await async_session.commit()

    joins_config = [
        JoinConfig(
            model=ProjectsParticipantsAssociation,
            join_on=Project.id == ProjectsParticipantsAssociation.project_id,
            join_type="inner",
        ),
        JoinConfig(
            model=Participant,
            join_on=ProjectsParticipantsAssociation.participant_id == Participant.id,
            join_type="inner",
            filters={"role": "Manager"},
        ),
    ]

    crud_project = FastCRUD(Project)

    count = await crud_project.count(
        async_session, joins_config=joins_config, name="Project Delta"
    )

    assert (
        count == 1
    ), "Expected to find 1 project named 'Project Delta' associated with a manager, but found a different count."


@pytest.mark.asyncio
async def test_count_raises_value_error_for_invalid_count(async_session):
    crud = FastCRUD(Project)

    with patch("sqlalchemy.ext.asyncio.AsyncSession.scalar", return_value=None):
        with pytest.raises(ValueError) as exc_info:
            await crud.count(async_session)
        assert str(exc_info.value) == "Could not find the count."
