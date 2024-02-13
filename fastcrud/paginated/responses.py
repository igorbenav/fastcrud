from typing import Generic, TypeVar, Optional

from pydantic import BaseModel

SchemaType = TypeVar("SchemaType", bound=BaseModel)


class ListResponse(BaseModel, Generic[SchemaType]):
    data: list[SchemaType]


class PaginatedListResponse(ListResponse[SchemaType]):
    total_count: int
    has_more: bool
    page: Optional[int] = None
    items_per_page: Optional[int] = None
