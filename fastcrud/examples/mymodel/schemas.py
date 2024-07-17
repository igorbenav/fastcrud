# --8<-- [start:imports]
import datetime

from pydantic import BaseModel


# --8<-- [end:imports]
# --8<-- [start:schemas]
# --8<-- [start:createschema]
class CreateMyModelSchema(BaseModel):
    name: str | None = None


# --8<-- [end:createschema]
# --8<-- [start:readschema]
class ReadMyModelSchema(BaseModel):
    id: int
    name: str | None = None
    archived: bool
    archived_at: datetime.datetime
    date_updated: datetime.datetime


# --8<-- [end:readschema]
# --8<-- [start:updateschema]
class UpdateMyModelSchema(BaseModel):
    name: str | None = None


# --8<-- [end:updateschema]
# --8<-- [start:deleteschema]
class DeleteMyModelSchema(BaseModel):
    pass


# --8<-- [end:deleteschema]
# --8<-- [end:schemas]
