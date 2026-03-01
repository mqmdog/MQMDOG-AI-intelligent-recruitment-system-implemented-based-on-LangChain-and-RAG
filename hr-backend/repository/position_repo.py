from typing import Sequence, Tuple
from datetime import datetime

from sqlalchemy import select, delete, func
from sqlalchemy.orm import selectinload

from . import BaseRepo
from models.user import UserModel
from models.position import PositionModel
from models.candidate import CandidateModel, CandidateAIScoreModel
from models.interview import InterviewModel


class PositionRepo(BaseRepo):
    # 创建职位
    async def create_position(self, position_data: dict) -> PositionModel:
        position = PositionModel(**position_data)
        self.session.add(position)
        # 第一步（flush）：让数据库生成ID，建立对象的"身份"
        await self.session.flush([position]) 
        # 第二步（二次查询）：把关联数据（部门、创建者等）都加载到内存
        return await self.session.scalar(
            select(PositionModel)
            .where(PositionModel.id == position.id)
            .options(
                selectinload(PositionModel.department),
                selectinload(PositionModel.creator)
                .selectinload(UserModel.department),
            )
        )

    # 获取职位列表
    async def get_position_list(
        self,
        user: UserModel,
        page: int = 1,
        size: int = 10,
    ) -> Sequence[PositionModel]:
        stmt = select(PositionModel)

        # HR: 仅返回负责部门的职位; 普通员工: 仅返回本部门; superuser: 无限制
        if user.is_hr and not user.is_superuser:
            department_ids = [d.id for d in user.managed_departments]
            stmt = stmt.where(PositionModel.department_id.in_(department_ids))
        elif not user.is_superuser and not user.is_hr:
            stmt = stmt.where(PositionModel.department_id ==
                              user.department_id)

        offset = (page - 1) * size
        stmt = (
            stmt.options(
                selectinload(PositionModel.department),
                selectinload(PositionModel.creator)
                .selectinload(UserModel.department),
            )
            .offset(offset)
            .limit(size)
            .order_by(PositionModel.created_at.desc())
        )
        return (await self.session.scalars(stmt)).all()

    # 根据职位ID获取职位
    async def get_by_id(self, position_id: str) -> PositionModel | None:
        return await self.session.scalar(
            select(PositionModel)
            .where(PositionModel.id == position_id)
            .options(
                selectinload(PositionModel.department),
                selectinload(PositionModel.creator)
                .selectinload(UserModel.department),
            )
        )

    # 删除职位
    async def delete_position(self, position_id: str) -> None:
        # 获取该职位下所有候选人ID
        candidate_ids_stmt = select(CandidateModel.id).where(
            CandidateModel.position_id == position_id
        )
        # 1. 删除关联的面试记录
        await self.session.execute(
            delete(InterviewModel).where(
                InterviewModel.candidate_id.in_(candidate_ids_stmt)
            )
        )
        # 2. 删除关联的AI评分记录
        await self.session.execute(
            delete(CandidateAIScoreModel).where(
                CandidateAIScoreModel.candidate_id.in_(candidate_ids_stmt)
            )
        )
        # 3. 删除关联的候选人记录
        await self.session.execute(
            delete(CandidateModel).where(
                CandidateModel.position_id == position_id
            )
        )
        # 4. 删除职位本身（position_embeddings 通过数据库 CASCADE 自动删除）
        await self.session.execute(
            delete(PositionModel).where(PositionModel.id == position_id)
        )

    # 求职端获取公开职位列表
    async def get_open_positions(
        self,
        page: int = 1,
        size: int = 10,
        keyword: str | None = None,
    ) -> Tuple[Sequence[PositionModel], int]:
        """获取面向求职者的公开职位列表"""
        stmt = select(PositionModel).where(PositionModel.is_open == True)
        stmt = stmt.where(
            (PositionModel.deadline == None) |
            (PositionModel.deadline >= datetime.now())
        )

        # 关键字搜索
        if keyword:
            stmt = stmt.where(PositionModel.title.ilike(f"%{keyword}%")) #ilike 模糊匹配（不区分大小写）

        # 查总数
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await self.session.scalar(count_stmt) or 0

        # 分页查询
        offset = (page - 1) * size
        stmt = (
            stmt.options(selectinload(PositionModel.department))
            .offset(offset)
            .limit(size)
            .order_by(PositionModel.created_at.desc())
        )
        result = (await self.session.scalars(stmt)).all()
        return result, total
