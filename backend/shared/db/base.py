"""SQLAlchemy declarative base used by every model module."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
