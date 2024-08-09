# --8<-- [start:imports]
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# --8<-- [end:imports]


# --8<-- [start:model]
# --8<-- [start:model_common]
class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    # --8<-- [end:model_common]
    username = Column(String)
    email = Column(String)
    age = Column(Integer)
    role = Column(String)
    # --8<-- [start:model_tier]
    tier_id = Column(Integer, ForeignKey("tier.id"))
    # --8<-- [end:model_tier]
    department_id = Column(Integer, ForeignKey("department.id"))
    manager_id = Column(Integer, ForeignKey("user.id"))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    registration_date = Column(DateTime, default=func.now())
    # --8<-- [start:model_archived]
    archived = Column(Boolean, default=False)
    archived_at = Column(DateTime)
    # --8<-- [end:model_archived]


# --8<-- [end:model]
