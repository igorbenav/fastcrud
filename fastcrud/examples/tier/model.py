# --8<-- [start:imports]
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# --8<-- [end:imports]


# --8<-- [start:model]
class Tier(Base):
    __tablename__ = "tier"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)


# --8<-- [end:model]
