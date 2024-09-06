# --8<-- [start:imports]
from pydantic import BaseModel


# --8<-- [end:imports]
# --8<-- [start:schemas]
# --8<-- [start:createschema]
class CreateProfileSchema(BaseModel):
    profile_id: int | None = None
    bio: str | None = None


# --8<-- [end:createschema]
# --8<-- [start:readschema]
class ReadProfileSchema(BaseModel):
    id: int
    bio: str | None = None


# --8<-- [end:readschema]
# --8<-- [start:updateschema]
class UpdateProfileSchema(BaseModel):
    bio: str | None = None


# --8<-- [end:updateschema]
# --8<-- [start:deleteschema]
class DeleteProfileSchema(BaseModel):
    pass


# --8<-- [end:deleteschema]
# --8<-- [end:schemas]
