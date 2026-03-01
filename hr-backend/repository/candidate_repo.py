from typing import Sequence

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from . import BaseRepo
from models.position import PositionModel
from models.user import UserModel
from models.candidate import CandidateModel, CandidateStatusEnum, ResumeModel


class CandidateRepo(BaseRepo):
    async def create_candidate(self, candidate_info: dict) -> CandidateModel:
        candidate = CandidateModel(**candidate_info)
        self.session.add(candidate)
        await self.session.flush([candidate])
        await self.session.refresh(candidate, ['position', 'resume', 'ai_score'])
        return candidate

    async def update_candidate_status(self, candidate_id: str, status: CandidateStatusEnum) -> None:
        stmt = (
            update(CandidateModel)
            .where(CandidateModel.id == candidate_id)
            .values(status=status)
        )
        await self.session.execute(stmt)

    async def get_by_id(self, candidate_id: str) -> CandidateModel | None:
        return await self.session.scalar(
            select(CandidateModel)
            .where(CandidateModel.id == candidate_id)
            .options(
                selectinload(CandidateModel.position)
                .selectinload(PositionModel.department),
                selectinload(CandidateModel.position)
                .selectinload(PositionModel.creator)
                .selectinload(UserModel.department),
                selectinload(CandidateModel.resume)
                .selectinload(ResumeModel.uploader)
                .selectinload(UserModel.department),
                selectinload(CandidateModel.creator)
                .selectinload(UserModel.department),
                selectinload(CandidateModel.ai_score),
            )
        )

    async def get_list(
        self,
        current_user: UserModel,
        position_id: str | None = None,
        status: CandidateStatusEnum | None = None,
        page: int = 1,
        size: int = 10,
    ) -> Sequence[CandidateModel]:
        stmt = select(CandidateModel)

        # 按照用户角色过滤
        if current_user.is_superuser:
            pass
        elif current_user.is_hr:
            hr_user = await self.session.scalar(
                select(UserModel)
                .where(UserModel.id == current_user.id)
                .options(selectinload(UserModel.managed_departments))
            )
            managed_department_ids = [
                d.id for d in hr_user.managed_departments]
            if not managed_department_ids:
                return []
            stmt = stmt.join(PositionModel).where(
                PositionModel.department_id.in_(managed_department_ids)
            )
        else:
            stmt = stmt.join(PositionModel).where(
                PositionModel.creator_id == current_user.id
            )

        if position_id is not None:
            stmt = stmt.where(CandidateModel.position_id == position_id)
        if status is not None:
            stmt = stmt.where(CandidateModel.status == status)

        offset = (page - 1) * size
        stmt = (
            stmt.options(
                selectinload(CandidateModel.position)
                .selectinload(PositionModel.department),
                selectinload(CandidateModel.position)
                .selectinload(PositionModel.creator)
                .selectinload(UserModel.department),
                selectinload(CandidateModel.resume)
                .selectinload(ResumeModel.uploader)
                .selectinload(UserModel.department),
                selectinload(CandidateModel.creator)
                .selectinload(UserModel.department),
                selectinload(CandidateModel.ai_score),
            )
            .offset(offset)
            .limit(size)
            .order_by(CandidateModel.created_at.desc())
        )
        return (await self.session.scalars(stmt)).all()
