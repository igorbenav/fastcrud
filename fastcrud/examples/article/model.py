# --8<-- [start:imports]
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# --8<-- [end:imports]
# --8<-- [start:model]
class Article(Base):
    __tablename__ = "article"
    id = Column(Integer, primary_key=True)
    author_id = Column(Integer, ForeignKey("author.id"))
    title = Column(String)
    content = Column(String)


# --8<-- [end:model]
