# --8<-- [start:imports]
from pydantic import BaseModel


# --8<-- [end:imports]
# --8<-- [start:schemas]
# --8<-- [start:createschema]
class CreateTaskSchema(BaseModel):
    creator_id: int | None = None
    owner_id: int | None = None
    assigned_user_id: int | None = None
    story_id: int | None = None
    status: str | None = None
    priority: str | None = None


# --8<-- [end:createschema]
# --8<-- [start:readschema]
class ReadTaskSchema(BaseModel):
    id: int
    creator_id: int | None = None
    owner_id: int | None = None
    assigned_user_id: int | None = None
    story_id: int | None = None
    status: str | None = None
    priority: str | None = None


# --8<-- [end:readschema]
# --8<-- [start:updateschema]
class UpdateTaskSchema(BaseModel):
    creator_id: int | None = None
    owner_id: int | None = None
    assigned_user_id: int | None = None
    story_id: int | None = None
    status: str | None = None
    priority: str | None = None


# --8<-- [end:updateschema]
# --8<-- [start:deleteschema]
class DeleteTaskSchema(BaseModel):
    pass


# --8<-- [end:deleteschema]
# --8<-- [end:schemas]
