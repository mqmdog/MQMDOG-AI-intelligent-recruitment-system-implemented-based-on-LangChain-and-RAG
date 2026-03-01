from sqlalchemy import select
from sqlalchemy.orm import selectinload

from . import BaseRepo
from models.candidate import ResumeModel


class ResumeRepo(BaseRepo):
    async def create_resume(self, file_path: str, uploader_id: str) -> ResumeModel:
        resume = ResumeModel(file_path=file_path, uploader_id=uploader_id)
        self.session.add(resume)
        await self.session.flush([resume]) 
        await self.session.refresh(resume, ["uploader"]) # 刷新会话，加载关联数据
        return resume

    async def create_resume_for_seeker(self, file_path: str, job_seeker_id: str) -> ResumeModel:
        resume = ResumeModel(file_path=file_path, job_seeker_id=job_seeker_id)
        self.session.add(resume)
        await self.session.flush([resume]) 
        return resume

    async def get_by_id(self, resume_id: str) -> ResumeModel | None:
        return await self.session.scalar(
            select(ResumeModel)
            .where(ResumeModel.id == resume_id)
            .options(selectinload(ResumeModel.uploader))
        )
