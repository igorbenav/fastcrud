# --8<-- [start:imports]
from sqlalchemy import Column, Integer, Numeric, String
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# --8<-- [end:imports]
# --8<-- [start:model]
class Product(Base):
    __tablename__ = "product"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    price = Column(Numeric)


# --8<-- [end:model]
