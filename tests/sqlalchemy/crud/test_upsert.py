import pytest

from fastcrud.crud.fast_crud import FastCRUD
from tests.sqlalchemy.conftest import CategoryModel, ReadSchemaTest, TierModel


@pytest.mark.asyncio
async def test_upsert_successful(async_session, test_model, read_schema):
    crud = FastCRUD(test_model)
    new_data = read_schema(id=1, name="New Record", tier_id=1, category_id=1)
    fetched_record = await crud.upsert(async_session, new_data, return_as_model=True)
    assert read_schema.model_validate(fetched_record) == new_data

    fetched_record.name == "New name"

    updated_fetched_record = await crud.upsert(async_session, fetched_record)
    assert read_schema.model_validate(updated_fetched_record) == fetched_record


@pytest.mark.parametrize(
    ["insert", "update"],
    [
        pytest.param(
            {
                "kwargs": {},
                "expected_result": None,
            },
            {
                "kwargs": {},
                "expected_result": None,
            },
            id="none",
        ),
        pytest.param(
            {
                "kwargs": {"return_columns": ["id", "name"]},
                "expected_result": {
                    "data": [
                        {
                            "id": 1,
                            "name": "New Record",
                        }
                    ]
                },
            },
            {
                "kwargs": {"return_columns": ["id", "name"]},
                "expected_result": {
                    "data": [
                        {
                            "id": 1,
                            "name": "New name",
                        }
                    ]
                },
            },
            id="dict",
        ),
        pytest.param(
            {
                "kwargs": {"return_columns": ["id", "name"]},
                "expected_result": {
                    "data": [
                        {
                            "id": 1,
                            "name": "New Record",
                        }
                    ]
                },
            },
            {
                "kwargs": {
                    "return_columns": ["id", "name"],
                    "name__match": "NewRecord",
                },
                "expected_result": {"data": []},
            },
            id="dict-filtered",
        ),
        pytest.param(
            {
                "kwargs": {
                    "schema_to_select": ReadSchemaTest,
                    "return_as_model": True,
                },
                "expected_result": {
                    "data": [
                        ReadSchemaTest(
                            id=1, name="New Record", tier_id=1, category_id=1
                        )
                    ]
                },
            },
            {
                "kwargs": {
                    "schema_to_select": ReadSchemaTest,
                    "return_as_model": True,
                },
                "expected_result": {
                    "data": [
                        ReadSchemaTest(id=1, name="New name", tier_id=1, category_id=1)
                    ]
                },
            },
            id="model",
        ),
    ],
)
@pytest.mark.dialect("postgresql")
@pytest.mark.asyncio
async def test_upsert_multi_successful(
    async_session,
    test_model,
    read_schema,
    test_data_tier,
    test_data_category,
    insert,
    update,
):
    for tier_item in test_data_tier:
        async_session.add(TierModel(**tier_item))
    for category_item in test_data_category:
        async_session.add(CategoryModel(**category_item))
    await async_session.commit()

    crud = FastCRUD(test_model)
    new_data = read_schema(id=1, name="New Record", tier_id=1, category_id=1)
    fetched_records = await crud.upsert_multi(
        async_session, [new_data], **insert["kwargs"]
    )

    assert fetched_records == insert["expected_result"]

    updated_new_data = new_data.model_copy(update={"name": "New name"})
    updated_fetched_records = await crud.upsert_multi(
        async_session, [updated_new_data], **update["kwargs"]
    )

    assert updated_fetched_records == update["expected_result"]
