# --8<-- [start:imports]
from pydantic import BaseModel


# --8<-- [end:imports]
# --8<-- [start:schemas]
# --8<-- [start:createschema]
class CreateOrderSchema(BaseModel):
    customer_id: int | None = None
    product_id: int | None = None
    quantity: int | None = None


# --8<-- [end:createschema]
# --8<-- [start:readschema]
class ReadOrderSchema(BaseModel):
    id: int
    customer_id: int | None = None
    product_id: int | None = None
    quantity: int | None = None


# --8<-- [end:readschema]
# --8<-- [start:updateschema]
class UpdateOrderSchema(BaseModel):
    customer_id: int | None = None
    product_id: int | None = None
    quantity: int | None = None


# --8<-- [end:updateschema]
# --8<-- [start:deleteschema]
class DeleteOrderSchema(BaseModel):
    pass


# --8<-- [end:deleteschema]
# --8<-- [end:schemas]
