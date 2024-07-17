# --8<-- [start:imports]
from sqlalchemy import Column, DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# --8<-- [end:imports]
# --8<-- [start:model]
class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    category = Column(String)
    price = Column(Numeric)
    last_sold = Column(DateTime)
    created_at = Column(DateTime, default=func.now())


# --8<-- [end:model]
