from typing import TypeVar, Type, Sequence

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from models.base import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseRepo:
    """基础仓库，提供通用 CRUD 操作"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def _get_by_id(self, model_class: Type[T], entity_id: str) -> T | None:
        return await self.session.scalar(
            select(model_class).where(model_class.id == entity_id)
        )

    async def _create(self, entity: BaseModel) -> BaseModel:
        self.session.add(entity)
        return entity

    async def _delete_by_id(self, model_class: Type[T], entity_id: str) -> None:
        await self.session.execute(
            delete(model_class).where(model_class.id == entity_id)
        )
