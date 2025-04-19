import pytest
from pydantic import BaseModel
from fastcrud.paginated.schemas import create_list_response, create_paginated_response


class TestSchema(BaseModel):
    name: str
    value: int


def test_create_list_response_default_key():
    ResponseModel = create_list_response(TestSchema)
    
    # Test model creation
    assert ResponseModel.__name__ == "DynamicListResponse"
    
    # Test with valid data
    data = [{"name": "test", "value": 1}, {"name": "test2", "value": 2}]
    response = ResponseModel(data=data)
    assert len(response.data) == 2
    assert response.data[0].name == "test"
    assert response.data[1].value == 2

    # Test with empty list
    empty_response = ResponseModel(data=[])
    assert len(empty_response.data) == 0


def test_create_list_response_custom_key():
    ResponseModel = create_list_response(TestSchema, response_key="items")
    
    # Test model creation
    assert ResponseModel.__name__ == "DynamicListResponse"
    
    # Test with valid data
    data = [{"name": "test", "value": 1}]
    response = ResponseModel(items=data)
    assert len(response.items) == 1
    assert response.items[0].name == "test"
    assert response.items[0].value == 1


def test_create_list_response_validation():
    ResponseModel = create_list_response(TestSchema)
    
    # Test invalid data
    with pytest.raises(ValueError):
        ResponseModel(data=[{"invalid_field": "test"}])


def test_create_paginated_response_default_key():
    ResponseModel = create_paginated_response(TestSchema)
    
    # Test model creation
    assert ResponseModel.__name__ == "DynamicPaginatedResponse"
    
    # Test with valid data
    response = ResponseModel(
        data=[{"name": "test", "value": 1}],
        total_count=1,
        has_more=False,
        page=1,
        items_per_page=10
    )
    
    assert len(response.data) == 1
    assert response.data[0].name == "test"
    assert response.total_count == 1
    assert response.has_more is False
    assert response.page == 1
    assert response.items_per_page == 10


def test_create_paginated_response_custom_key():
    ResponseModel = create_paginated_response(TestSchema, response_key="items")
    
    # Test with valid data
    response = ResponseModel(
        items=[{"name": "test", "value": 1}],
        total_count=1,
        has_more=False,
        page=1,
        items_per_page=10
    )
    
    assert len(response.items) == 1
    assert response.items[0].name == "test"


def test_create_paginated_response_optional_fields():
    ResponseModel = create_paginated_response(TestSchema)
    
    # Test with minimal required fields
    response = ResponseModel(
        data=[{"name": "test", "value": 1}],
        total_count=1,
        has_more=False
    )
    
    assert response.page is None
    assert response.items_per_page is None


def test_create_paginated_response_validation():
    ResponseModel = create_paginated_response(TestSchema)
    
    # Test missing required fields
    with pytest.raises(ValueError):
        ResponseModel(
            data=[{"name": "test", "value": 1}],
            has_more=False  # missing total_count
        )
    
    # Test invalid data structure
    with pytest.raises(ValueError):
        ResponseModel(
            data=[{"invalid_field": "test"}],
            total_count=1,
            has_more=False
        )


def test_create_paginated_response_empty_list():
    ResponseModel = create_paginated_response(TestSchema)
    
    response = ResponseModel(
        data=[],
        total_count=0,
        has_more=False,
        page=1,
        items_per_page=10
    )
    
    assert len(response.data) == 0
    assert response.total_count == 0
    assert response.has_more is False