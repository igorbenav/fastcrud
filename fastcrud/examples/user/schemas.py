# --8<-- [start:imports]
import datetime

from pydantic import BaseModel


# --8<-- [end:imports]
# --8<-- [start:schemas]
# --8<-- [start:createschema]
# --8<-- [start:createschema_common]
class CreateUserSchema(BaseModel):
    name: str | None = None
    # --8<-- [end:createschema_common]
    username: str | None = None
    email: str | None = None
    age: int | None = None
    role: str | None = None
    tier_id: int | None = None
    department_id: int | None = None
    manager_id: int | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None


# --8<-- [end:createschema]
# --8<-- [start:readschema]
# --8<-- [start:readschema_common]
class ReadUserSchema(BaseModel):
    id: int
    name: str | None = None
    # --8<-- [end:readschema_common]
    username: str | None = None
    email: str | None = None
    age: int | None = None
    role: str | None = None
    tier_id: int | None = None
    department_id: int | None = None
    manager_id: int | None = None
    is_active: bool
    is_superuser: bool
    registration_date: datetime.datetime
    archived: bool
    archived_at: datetime.datetime | None = None


# --8<-- [end:readschema]
# --8<-- [start:updateschema]
# --8<-- [start:updateschema_common]
class UpdateUserSchema(BaseModel):
    name: str | None = None
    # --8<-- [end:updateschema_common]
    username: str | None = None
    email: str | None = None
    age: int | None = None
    role: str | None = None
    tier_id: int | None = None
    department_id: int | None = None
    manager_id: int | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None


# --8<-- [end:updateschema]
# --8<-- [start:deleteschema]
class DeleteUserSchema(BaseModel):
    pass


# --8<-- [end:deleteschema]
# --8<-- [end:schemas]
