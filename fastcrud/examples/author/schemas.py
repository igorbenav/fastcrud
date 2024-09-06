# --8<-- [start:imports]
from pydantic import BaseModel


# --8<-- [end:imports]
# --8<-- [start:schemas]
# --8<-- [start:createschema]
class CreateAuthorSchema(BaseModel):
    profile_id: int | None = None
    name: str | None = None


# --8<-- [end:createschema]
# --8<-- [start:readschema]
class ReadAuthorSchema(BaseModel):
    id: int
    profile_id: int | None = None
    name: str | None = None


# --8<-- [end:readschema]
# --8<-- [start:updateschema]
class UpdateAuthorSchema(BaseModel):
    profile_id: int | None = None
    name: str | None = None


# --8<-- [end:updateschema]
# --8<-- [start:deleteschema]
class DeleteAuthorSchema(BaseModel):
    pass


# --8<-- [end:deleteschema]
# --8<-- [end:schemas]
