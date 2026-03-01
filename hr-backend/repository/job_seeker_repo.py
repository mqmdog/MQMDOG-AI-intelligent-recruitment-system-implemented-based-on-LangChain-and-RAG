"""求职者 Repository"""
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from models.job_seeker import JobSeekerModel
from repository import BaseRepo


class JobSeekerRepo(BaseRepo):
    """求职者数据仓库"""

    async def create_job_seeker(self, job_seeker_data: dict) -> JobSeekerModel:
        job_seeker = JobSeekerModel(**job_seeker_data)
        await self._create(job_seeker)
        await self.session.flush()
        await self.session.refresh(job_seeker)
        return job_seeker

    async def get_by_id(self, job_seeker_id: str) -> JobSeekerModel | None:
        return await self._get_by_id(JobSeekerModel, job_seeker_id)

    async def get_by_email(self, email: str) -> JobSeekerModel | None:
        return await self.session.scalar(
            select(JobSeekerModel).where(JobSeekerModel.email == email)
        )

    async def get_by_username(self, username: str) -> JobSeekerModel | None:
        return await self.session.scalar(
            select(JobSeekerModel).where(JobSeekerModel.username == username)
        )
