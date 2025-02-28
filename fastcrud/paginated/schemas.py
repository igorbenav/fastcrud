from typing import Generic, TypeVar, Optional

from pydantic import BaseModel, create_model

SchemaType = TypeVar("SchemaType", bound=BaseModel)


def create_list_response(
    schema: type[SchemaType], response_key: str = "data"
) -> type[BaseModel]:
    """Creates a dynamic ListResponse model with the specified response key."""
    return create_model("DynamicListResponse", **{response_key: (list[schema], ...)})


def create_paginated_response(
    schema: type[SchemaType], response_key: str = "data"
) -> type[BaseModel]:
    """Creates a dynamic PaginatedResponse model with the specified response key."""
    return create_model(
        "DynamicPaginatedResponse",
        **{
            response_key: (list[schema], ...),
            "total_count": (int, ...),
            "has_more": (bool, ...),
            "page": (Optional[int], None),
            "items_per_page": (Optional[int], None),
        }
    )


class ListResponse(BaseModel, Generic[SchemaType]):
    data: list[SchemaType]


class PaginatedListResponse(ListResponse[SchemaType]):
    total_count: int
    has_more: bool
    page: Optional[int] = None
    items_per_page: Optional[int] = None
