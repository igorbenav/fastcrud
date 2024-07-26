# --8<-- [start:imports]
from pydantic import BaseModel


# --8<-- [end:imports]
# --8<-- [start:schemas]
# --8<-- [start:createschema]
class CreateProductSchema(BaseModel):
    name: str | None = None
    price: float | None = None


# --8<-- [end:createschema]
# --8<-- [start:readschema]
class ReadProductSchema(BaseModel):
    id: int
    name: str | None = None
    price: float | None = None


# --8<-- [end:readschema]
# --8<-- [start:updateschema]
class UpdateProductSchema(BaseModel):
    name: str | None = None
    price: float | None = None


# --8<-- [end:updateschema]
# --8<-- [start:deleteschema]
class DeleteProductSchema(BaseModel):
    pass


# --8<-- [end:deleteschema]
# --8<-- [end:schemas]
