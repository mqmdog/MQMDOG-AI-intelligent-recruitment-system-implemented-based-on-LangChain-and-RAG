from loguru import logger

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from models import AsyncSessionFactory
from models.user import UserModel, UserStatus
from models.job_seeker import JobSeekerModel, JobSeekerStatus
from repository.user_repo import UserRepo
from repository.job_seeker_repo import JobSeekerRepo
from core.auth import AuthHandler
from core.cache import HRCache

auth_handler = AuthHandler()


async def get_session_instance():
    """获取数据库会话实例"""
    session: AsyncSession = AsyncSessionFactory()
    try:
        yield session
    finally:
        await session.close()


async def get_auth_handler() -> AuthHandler:
    return auth_handler


def get_user_id(
    iss: str = Depends(auth_handler.auth_access_dependency),
) -> str:
    return iss


async def get_current_user(
    user_id: str = Depends(get_user_id),
    session: AsyncSession = Depends(get_session_instance),
) -> UserModel:
    async with session.begin():
        user_repo = UserRepo(session=session)
        user: UserModel = await user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
        if user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="该账号不可用，请联系管理员")
        return user


async def get_super_user(
    current_user: UserModel = Depends(get_current_user),
) -> UserModel:
    if current_user.is_superuser:
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="权限不足，无法访问")


def get_cache_instance() -> HRCache:
    return HRCache()


def get_job_seeker_id(
    iss: str = Depends(auth_handler.auth_access_dependency),
) -> str:
    """从 JWT 获取求职者 ID"""
    return iss


async def get_current_job_seeker(
    job_seeker_id: str = Depends(get_job_seeker_id),
    session: AsyncSession = Depends(get_session_instance),
) -> JobSeekerModel:
    """获取当前求职者用户"""
    async with session.begin():
        repo = JobSeekerRepo(session=session)
        job_seeker = await repo.get_by_id(job_seeker_id)
        if not job_seeker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="求职者不存在"
            )
        if job_seeker.status != JobSeekerStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="该账号已被禁用"
            )
        return job_seeker


async def get_hr_or_superuser(
    current_user: UserModel = Depends(get_current_user),
) -> UserModel:
    """获取 HR 或超级用户"""
    if current_user.is_hr or current_user.is_superuser:
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="需要 HR 或管理员权限"
    )
