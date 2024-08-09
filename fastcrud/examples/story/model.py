# --8<-- [start:imports]
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# --8<-- [end:imports]


# --8<-- [start:model]
class Story(Base):
    __tablename__ = "story"
    id = Column(Integer, primary_key=True)
    name = Column(String)


# --8<-- [end:model]
