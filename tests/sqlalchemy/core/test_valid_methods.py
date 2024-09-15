import pytest

from pydantic import ValidationError
from fastcrud.endpoint.helper import CRUDMethods


def test_crud_methods_with_invalid_method():
    with pytest.raises(ValidationError) as excinfo:
        CRUDMethods(valid_methods=["create", "invalid_method"])

    assert "Invalid CRUD method: invalid_method" in str(excinfo.value)


def test_crud_methods_with_valid_methods():
    crud_methods = CRUDMethods(valid_methods=["create", "read"])
    assert crud_methods.valid_methods == ["create", "read"]


def test_crud_methods_default_methods():
    crud_methods = CRUDMethods()
    expected_methods = [
        "create",
        "read",
        "read_multi",
        "update",
        "delete",
        "db_delete",
    ]
    assert (
        crud_methods.valid_methods == expected_methods
    ), "Default CRUD methods are incorrect."
