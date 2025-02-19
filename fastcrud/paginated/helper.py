from typing import Any, Type, Union
from fastapi.exceptions import RequestValidationError


def compute_offset(page: int, items_per_page: int) -> int:
    """Calculate the offset for pagination based on the given page number and items per page.

    The offset represents the starting point in a dataset for the items on a given page.
    For example, if each page displays 10 items and you want to display page 3, the offset will be 20,
    meaning the display should start with the 21st item.

    Args:
        page: The current page number. Page numbers should start from 1.
        items_per_page: The number of items to be displayed on each page.

    Returns:
        The calculated offset.

    Examples:
        >>> offset(1, 10)
        0
        >>> offset(3, 10)
        20
    """
    return (page - 1) * items_per_page

def parse_cursor(cursor: Any, type_tuple: Union[tuple[Type[Any], ...], tuple[()]]):
    """Parses a cursor the the expected format.

    The cursor supplied by the query param is always a string. 
    In reality, it can be either a truth-value (True) or a comma 
    seperated sequence of any types or a singular any type.
    The correct types are given by the type_tuple.
    If it is a True-value, then None is returned as representative of the "first-page" cursor
    Acceptable True-values: True, "True", "true", "T", "t", "Yes", "yes", "Y", "y"

    Args:
        cursor: the user-provided cursor
        type_tuple: the types that should make up the cursor

    Returns:
        Correctly formatted cursor (boolean (True), string, tuple of strings)

    Examples:
        >>> parse_cursor(True)
        None
        >>> parse_cursor("True")
        None
        >>> parse_cursor("1")
        "1"
    """
    if isinstance(cursor, bool) and cursor:
        return None
    elif isinstance(cursor, str) and cursor in {"True", "true", "t", "Yes", "yes", "Y", "y"}:
        return None
    elif isinstance(cursor, str) and "," in cursor:
        cursor_tuple = tuple(cursor.split(","))
        assert len(cursor_tuple) == len(type_tuple), f"cursor should be a tuple of len {len(type_tuple)} with types {type_tuple}"
        parsed_cursor = []
        for idx in range(len(cursor_tuple)):
            try:
                parsed_cursor.append(type_tuple[idx](cursor_tuple[idx]))
            except Exception:
                raise RequestValidationError(f"cannot cast cursor value {cursor_tuple[idx]} to type {type_tuple[idx]}")
        return tuple(parsed_cursor)
    elif isinstance(cursor, str):
        assert len(type_tuple) == 1, f"cursor should be a tuple of len {len(type_tuple)} with types {type_tuple}"
        try:
            return type_tuple[0](cursor)
        except Exception:
            raise RequestValidationError(f"cannot cast cursor value {cursor} to type {type_tuple[0]}")
    else:
        raise ValueError(f"invalid cursor {cursor}")
