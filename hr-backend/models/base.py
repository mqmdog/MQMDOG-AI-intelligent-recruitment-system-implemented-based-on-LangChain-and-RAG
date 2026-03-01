from datetime import datetime

from shortuuid import uuid
from sqlalchemy import MetaData, DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """所有模型的声明基类，定义统一的命名约定"""
    metadata = MetaData(naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    })


class BaseModel(Base):
    """抽象基类，提供通用的 id / created_at / updated_at 字段"""
    __abstract__ = True

    id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
        default=lambda: uuid(),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
    )
