import pytest

from fastcrud import FastCRUD


@pytest.mark.asyncio
async def test_multi_field_or_filter(async_session, test_model):
    # Create specific test data for multi-field OR filtering
    test_data = [
        {"name": "Alice Johnson", "tier_id": 1, "category_id": 1},
        {"name": "Bob Smith", "tier_id": 2, "category_id": 1},
        {"name": "Charlie Brown", "tier_id": 3, "category_id": 2},
        {"name": "David Jones", "tier_id": 4, "category_id": 2},
        {"name": "Eve Williams", "tier_id": 5, "category_id": 1},
        {"name": "Frank Miller", "tier_id": 6, "category_id": 2},
    ]

    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    crud = FastCRUD(test_model)

    # Test multi-field OR with simple equality conditions
    result = await crud.get_multi(
        async_session,
        _or={"name": "Alice Johnson", "tier_id": 2}
    )
    assert len(result["data"]) == 2
    assert any(item["name"] == "Alice Johnson" for item in result["data"])
    assert any(item["tier_id"] == 2 for item in result["data"])

    # Test multi-field OR with operators
    result = await crud.get_multi(
        async_session,
        _or={"name__startswith": "Alice", "tier_id__gt": 5}
    )
    assert len(result["data"]) > 0
    for item in result["data"]:
        assert item["name"].startswith("Alice") or item["tier_id"] > 5

    # Test multi-field OR with LIKE operators
    keyword = "li"
    result = await crud.get_multi(
        async_session,
        _or={
            "name__ilike": f"%{keyword}%",
            "category_id__eq": 2
        }
    )
    assert len(result["data"]) > 0
    for item in result["data"]:
        assert (keyword.lower() in item["name"].lower() or
                item["category_id"] == 2)

    # Test multi-field OR with mixed operators
    result = await crud.get_multi(
        async_session,
        _or={
            "tier_id__gt": 4,
            "name__startswith": "Alice"
        }
    )
    assert len(result["data"]) > 0
    for item in result["data"]:
        assert item["tier_id"] > 4 or item["name"].startswith("Alice")

    # Test multi-field OR combined with regular filters
    result = await crud.get_multi(
        async_session,
        category_id=1,  # Regular filter applied to all results
        _or={
            "name__ilike": "%Alice%",
            "tier_id__eq": 2
        }
    )
    assert len(result["data"]) > 0
    for item in result["data"]:
        assert item["category_id"] == 1
        assert ("alice" in item["name"].lower() or
                item["tier_id"] == 2)

    # Test with no matching results
    result = await crud.get_multi(
        async_session,
        _or={
            "name": "NonExistent",
            "tier_id": 999
        }
    )
    assert len(result["data"]) == 0


@pytest.mark.asyncio
async def test_multi_field_or_filter_client_example(async_session, test_model):
    # Create test data to simulate a search across multiple fields
    test_data = [
        {"name": "Acme Corp", "tier_id": 1, "category_id": 1},
        {"name": "XYZ Inc", "tier_id": 2, "category_id": 1},
        {"name": "ABC Ltd", "tier_id": 3, "category_id": 2},
        {"name": "Tech Solutions", "tier_id": 4, "category_id": 2},
    ]

    for item in test_data:
        async_session.add(test_model(**item))
    await async_session.commit()

    crud = FastCRUD(test_model)

    # Test searching across multiple fields with a keyword
    keyword = "corp"
    result = await crud.get_multi(
        async_session,
        _or={
            "name__ilike": f"%{keyword}%",
            "tier_id__eq": 2
        }
    )

    assert len(result["data"]) > 0
    for item in result["data"]:
        assert (keyword.lower() in item["name"].lower() or
                item["tier_id"] == 2)

    # Test with a different keyword
    keyword = "tech"
    result = await crud.get_multi(
        async_session,
        _or={
            "name__ilike": f"%{keyword}%",
            "category_id__eq": 1
        }
    )

    assert len(result["data"]) > 0
    for item in result["data"]:
        assert (keyword.lower() in item["name"].lower() or
                item["category_id"] == 1)
