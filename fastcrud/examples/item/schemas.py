# --8<-- [start:imports]
import datetime

from pydantic import BaseModel


# --8<-- [end:imports]
# --8<-- [start:schemas]
# --8<-- [start:itemschema]
class ItemSchema(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    price: float | None = None
    last_sold: datetime.datetime | None = None


# --8<-- [end:itemschema]
# --8<-- [start:createschema]
class CreateItemSchema(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    price: float | None = None
    last_sold: datetime.datetime | None = None


# --8<-- [end:createschema]
# --8<-- [start:readschema]
class ReadItemSchema(BaseModel):
    id: int
    name: str | None = None
    description: str | None = None
    category: str | None = None
    price: float | None = None
    last_sold: datetime.datetime | None = None
    created_at: datetime.datetime


# --8<-- [end:readschema]
# --8<-- [start:updateschema]
class UpdateItemSchema(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    price: float | None = None
    last_sold: datetime.datetime | None = None


# --8<-- [end:updateschema]
# --8<-- [start:deleteschema]
class DeleteItemSchema(BaseModel):
    pass


# --8<-- [end:deleteschema]
# --8<-- [end:schemas]
