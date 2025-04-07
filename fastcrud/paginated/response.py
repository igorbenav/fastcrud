from typing import Any


def paginated_response(
    crud_data: dict,
    page: int,
    items_per_page: int,
    multi_response_key: str = "data",
) -> dict[str, Any]:
    """Create a paginated response based on the provided data and pagination parameters.

    Args:
        crud_data: Data to be paginated, including the list of items and total count.
        page: Current page number.
        items_per_page: Number of items per page.
        multi_response_key: Key to use for the items list in the response (defaults to "data").

    Returns:
        A structured paginated response dict containing the list of items, total count, pagination flags, and numbers.

    Note:
        The function does not actually paginate the data but formats the response to indicate pagination metadata.
    """
    items = crud_data.get(multi_response_key, [])
    total_count = crud_data.get("total_count", 0)

    response = {
        multi_response_key: items,
        "total_count": total_count,
        "has_more": (page * items_per_page) < total_count,
        "page": page,
        "items_per_page": items_per_page,
    }

    return response
