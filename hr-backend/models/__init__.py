# 统一接口导出
from .database import engine, AsyncSessionFactory
from .base import Base, BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

# 确保所有模型被导入以便 Alembic 和关系发现
from . import user
from . import position
from . import interview
from . import candidate
from . import job_seeker

__all__ = [
    "engine",
    "AsyncSessionFactory",
    "AsyncSession",
    "Base",
    "BaseModel",
]
