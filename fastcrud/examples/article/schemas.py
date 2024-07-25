# --8<-- [start:imports]
from pydantic import BaseModel


# --8<-- [end:imports]
# --8<-- [start:schemas]
# --8<-- [start:createschema]
class CreateArticleSchema(BaseModel):
    author_id: int | None = None
    title: str | None = None
    content: str | None = None


# --8<-- [end:createschema]
# --8<-- [start:readschema]
class ReadArticleSchema(BaseModel):
    id: int
    author_id: int | None = None
    title: str | None = None
    content: str | None = None


# --8<-- [end:readschema]
# --8<-- [start:updateschema]
class UpdateArticleSchema(BaseModel):
    author_id: int | None = None
    title: str | None = None
    content: str | None = None


# --8<-- [end:updateschema]
# --8<-- [start:deleteschema]
class DeleteArticleSchema(BaseModel):
    pass


# --8<-- [end:deleteschema]
# --8<-- [end:schemas]
