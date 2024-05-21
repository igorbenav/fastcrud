import pytest
from fastcrud.endpoint.helper import FilterConfig


def test_filter_config_with_invalid_default_value():
    with pytest.raises(ValueError) as excinfo:
        FilterConfig(filters={"valid_string": "value", "invalid_list": [1, 2, 3]})

    assert "Invalid default value for 'invalid_list'" in str(excinfo.value)


def test_filter_config_with_valid_default_values():
    filter_config = FilterConfig(
        filters={
            "string": "value",
            "int": 42,
            "float": 3.14,
            "bool": True,
            "none": None,
        }
    )
    assert filter_config.filters == {
        "string": "value",
        "int": 42,
        "float": 3.14,
        "bool": True,
        "none": None,
    }


def test_filter_config_get_params():
    filter_config = FilterConfig(filters={"string": "value", "int": 42})
    params = filter_config.get_params()
    assert params["string"].default == "value"
    assert params["int"].default == 42
