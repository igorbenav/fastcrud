# --8<-- [start:imports]
import datetime

from sqlmodel import Field, SQLModel, func


# --8<-- [end:imports]
# --8<-- [start:model]
class Item(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str | None = None
    description: str | None = None
    category: str | None = None
    price: float | None = None
    last_sold: datetime.datetime | None = None
    created_at: datetime.datetime = Field(
        nullable=False, sa_column_kwargs={"default": func.now()}
    )


# --8<-- [end:model]
# --8<-- [start:schemas]
# --8<-- [start:itemschema]
class ItemSchema(SQLModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    price: float | None = None
    last_sold: datetime.datetime | None = None


# --8<-- [end:itemschema]
# --8<-- [start:createschema]
class CreateItemSchema(SQLModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    price: float | None = None
    last_sold: datetime.datetime | None = None


# --8<-- [end:createschema]
# --8<-- [start:readschema]
class ReadItemSchema(SQLModel):
    id: int
    name: str | None = None
    description: str | None = None
    category: str | None = None
    price: float | None = None
    last_sold: datetime.datetime | None = None
    created_at: datetime.datetime


# --8<-- [end:readschema]
# --8<-- [start:updateschema]
class UpdateItemSchema(SQLModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    price: float | None = None
    last_sold: datetime.datetime | None = None


# --8<-- [end:updateschema]
# --8<-- [start:deleteschema]
class DeleteItemSchema(SQLModel):
    pass


# --8<-- [end:deleteschema]
# --8<-- [end:schemas]
