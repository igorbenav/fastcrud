# --8<-- [start:imports]
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# --8<-- [end:imports]
# --8<-- [start:model]
# --8<-- [start:model_softdelete]
# --8<-- [start:model_simple]
class MyModel(Base):
    __tablename__ = "my_model"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    # --8<-- [end:model_simple]
    archived = Column(Boolean, default=False)  # Custom soft delete column
    archived_at = Column(DateTime)  # Custom timestamp column for soft delete
    # --8<-- [end:model_softdelete]
    date_updated = Column(DateTime)  # Custom timestamp column for update


# --8<-- [end:model]
