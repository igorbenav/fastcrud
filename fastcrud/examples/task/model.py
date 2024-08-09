# --8<-- [start:imports]
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# --8<-- [end:imports]


# --8<-- [start:model]
class Task(Base):
    __tablename__ = "task"
    id = Column(Integer, primary_key=True)
    creator_id = Column(Integer, ForeignKey("user.id"))
    owner_id = Column(Integer, ForeignKey("user.id"))
    assigned_user_id = Column(Integer, ForeignKey("user.id"))
    story_id = Column(Integer, ForeignKey("story.id"))
    status = Column(String)
    priority = Column(String)


# --8<-- [end:model]
