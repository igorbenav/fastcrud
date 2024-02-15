from typing import Any

def paginated_response(crud_data: dict, page: int, items_per_page: int) -> dict[str, Any]:
    """Create a paginated response based on the provided data and pagination parameters.

    Parameters
    ----------
    crud_data : ListResponse[SchemaType]
        Data to be paginated, including the list of items and total count.
    page : int
        Current page number.
    items_per_page : int
        Number of items per page.

    Returns
    -------
    dict[str, Any]
        A structured paginated response dict containing the list of items, total count, pagination flags, and numbers.

    Note
    ----
    The function does not actually paginate the data but formats the response to indicate pagination metadata.
    """
    return {
        "data": crud_data["data"],
        "total_count": crud_data["total_count"],
        "has_more": (page * items_per_page) < crud_data["total_count"],
        "page": page,
        "items_per_page": items_per_page,
    }
