# --8<-- [start:imports]
from pydantic import BaseModel


# --8<-- [end:imports]
# --8<-- [start:schemas]
# --8<-- [start:createschema]
class CreateTierSchema(BaseModel):
    name: str | None = None


# --8<-- [end:createschema]
# --8<-- [start:readschema]
class ReadTierSchema(BaseModel):
    id: int
    name: str | None = None


# --8<-- [end:readschema]
# --8<-- [start:updateschema]
class UpdateTierSchema(BaseModel):
    name: str | None = None


# --8<-- [end:updateschema]
# --8<-- [start:deleteschema]
class DeleteTierSchema(BaseModel):
    pass


# --8<-- [end:deleteschema]
# --8<-- [end:schemas]
