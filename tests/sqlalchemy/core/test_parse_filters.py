import pytest
from fastcrud import FastCRUD


@pytest.mark.asyncio
async def test_parse_filters_single_condition(test_model):
    fast_crud = FastCRUD(test_model)

    filters = fast_crud._parse_filters(name="John Doe")
    assert len(filters) == 1
    assert str(filters[0]) == "test.name = :name_1"


@pytest.mark.asyncio
async def test_parse_filters_multiple_conditions(test_model):
    fast_crud = FastCRUD(test_model)

    filters = fast_crud._parse_filters(tier_id__gt=1, is_deleted=True)
    assert len(filters) == 2
    assert str(filters[0]).endswith("tier_id > :tier_id_1")
    assert str(filters[1]) == "test.is_deleted = true"


@pytest.mark.asyncio
async def test_parse_filters_contained_in(test_model):
    fast_crud = FastCRUD(test_model)
    filters = fast_crud._parse_filters(category_id__in=[1, 2])
    assert len(filters) == 1
    assert str(
        filters[0]
    ) == "test.category_id IN (__[POSTCOMPILE_category_id_1])"


@pytest.mark.asyncio
async def test_parse_filters_invalid_column(test_model):
    fast_crud = FastCRUD(test_model)

    with pytest.raises(ValueError):
        fast_crud._parse_filters(invalid_column__="This does not exist")
