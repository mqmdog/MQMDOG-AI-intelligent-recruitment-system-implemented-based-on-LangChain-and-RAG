"""求职者问答路由 - 包含 SSE 流式响应"""
import json
from uuid import uuid4
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks, File, UploadFile
from fastapi.responses import StreamingResponse
from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from models import AsyncSession
from models.job_seeker import JobSeekerModel, JobSeekerStatus
from models.position import PositionModel
from models.candidate import CandidateModel
from schemas.job_seeker_schema import (
    JobSeekerRegisterSchema,
    JobSeekerLoginSchema,
    JobSeekerLoginResponse,
    JobSeekerSchema,
    ChatSessionCreateSchema,
    ChatSessionSchema,
    ChatSessionListResponse,
    ChatHistoryResponse,
)
from schemas import ResponseSchema
from schemas.candidate_schema import (
    SeekerApplySchema,
    ResumeParseTaskRespSchema,
    ResumeParseTaskInfoRespSchema,
)
from schemas.position_schema import PublicPositionSchema, PublicPositionListRespSchema
from dependencies import (
    get_session_instance,
    get_auth_handler,
    AuthHandler,
    get_current_job_seeker,
    get_job_seeker_id,
    get_super_user,
    get_cache_instance,
)
from core.cache import HRCache
from repository.job_seeker_repo import JobSeekerRepo
from repository.chat_repo import ChatRepo
from repository.position_repo import PositionRepo
from repository.position_embedding_repo import PositionEmbeddingRepo
from repository.resume_repo import ResumeRepo
from agents.job_qa_agent import JobQAAgent, embed_position
from tasks import apply_for_position_task
from utils.resume_utils import save_resume_file

router = APIRouter(prefix="/job-qa", tags=["job-qa"])


@router.post("/register", summary="求职者注册", response_model=JobSeekerSchema)
async def register(
    data: JobSeekerRegisterSchema,
    session: AsyncSession = Depends(get_session_instance),
):
    async with session.begin():
        repo = JobSeekerRepo(session)

        existing = await repo.get_by_email(str(data.email))
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该邮箱已被注册",
            )

        existing = await repo.get_by_username(data.username)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该用户名已被使用",
            )

        job_seeker = await repo.create_job_seeker({
            "username": data.username,
            "email": str(data.email),
            "password": data.password,
            "phone_number": data.phone_number,
        })

        return job_seeker


@router.post("/login", summary="求职者登录", response_model=JobSeekerLoginResponse)
async def login(
    data: JobSeekerLoginSchema,
    session: AsyncSession = Depends(get_session_instance),
    auth_handler: AuthHandler = Depends(get_auth_handler),
):
    async with session.begin():
        repo = JobSeekerRepo(session)
        job_seeker = await repo.get_by_email(str(data.email))

        if not job_seeker:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户不存在",
            )

        if not job_seeker.check_password(data.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱或密码错误",
            )

        if job_seeker.status != JobSeekerStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="该账号已被禁用",
            )

        tokens = auth_handler.encode_login_token(job_seeker.id)

        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "job_seeker": job_seeker,
        }


@router.get("/me", summary="获取当前求职者信息", response_model=JobSeekerSchema)
async def get_me(
    job_seeker: JobSeekerModel = Depends(get_current_job_seeker),
):
    return job_seeker


@router.post("/chat/session", summary="创建新会话", response_model=ChatSessionSchema)
async def create_session(
    data: ChatSessionCreateSchema,
    job_seeker: JobSeekerModel = Depends(get_current_job_seeker),
    session: AsyncSession = Depends(get_session_instance),
):
    async with session.begin():
        repo = ChatRepo(session)
        chat_session = await repo.create_session(
            job_seeker_id=job_seeker.id,
            title=data.title,
        )
        return chat_session


@router.get("/chat/session/list", summary="获取会话列表", response_model=ChatSessionListResponse)
async def get_session_list(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    job_seeker: JobSeekerModel = Depends(get_current_job_seeker),
    session: AsyncSession = Depends(get_session_instance),
):
    async with session.begin():
        repo = ChatRepo(session)
        sessions = await repo.get_session_list(
            job_seeker_id=job_seeker.id,
            page=page,
            size=size,
        )
        return {"sessions": sessions}


@router.get("/chat/history/{session_id}", summary="获取历史消息", response_model=ChatHistoryResponse)
async def get_history(
    session_id: str,
    job_seeker: JobSeekerModel = Depends(get_current_job_seeker),
    session: AsyncSession = Depends(get_session_instance),
):
    async with session.begin():
        repo = ChatRepo(session)
        chat_session = await repo.get_session_by_id(session_id)

        if not chat_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在",
            )

        if chat_session.job_seeker_id != job_seeker.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此会话",
            )

        histories = await repo.get_all_history(session_id)
        return {"histories": histories}


@router.delete("/chat/session/{session_id}", summary="删除会话", response_model=ResponseSchema)
async def delete_session(
    session_id: str,
    job_seeker: JobSeekerModel = Depends(get_current_job_seeker),
    session: AsyncSession = Depends(get_session_instance),
):
    async with session.begin():
        repo = ChatRepo(session)
        chat_session = await repo.get_session_by_id(session_id)

        if not chat_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在",
            )

        if chat_session.job_seeker_id != job_seeker.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除此会话",
            )

        await repo.delete_session(session_id)

    return {"message": "会话已删除"}


@router.get("/chat/stream", summary="SSE 流式问答")
async def chat_stream(
    session_id: str = Query(..., description="会话 ID"),
    message: str = Query(..., min_length=1,
                         max_length=2000, description="用户消息"),
    job_seeker_id: str = Depends(get_job_seeker_id),
):
    """SSE 流式问答接口"""

    async def event_generator() -> AsyncGenerator[str, None]:
        from models import AsyncSessionFactory
        db_session = AsyncSessionFactory()

        try:
            async with db_session.begin():
                chat_repo = ChatRepo(db_session)
                chat_session = await chat_repo.get_session_by_id(session_id)

                if not chat_session:
                    yield f"data: {json.dumps({'type': 'error', 'content': '会话不存在'})}\n\n"
                    return

                if chat_session.job_seeker_id != job_seeker_id:
                    yield f"data: {json.dumps({'type': 'error', 'content': '无权访问此会话'})}\n\n"
                    return

            async with db_session.begin():
                agent = JobQAAgent(db_session)

                async for event in agent.chat_stream(session_id, message):
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.error(f"SSE 流处理错误: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
        finally:
            await db_session.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/admin/embed/position/{position_id}", summary="单个职位向量化", response_model=ResponseSchema)
async def embed_single_position(
    position_id: str,
    session: AsyncSession = Depends(get_session_instance),
    _=Depends(get_super_user),
):
    """为单个职位生成向量（需要超级用户权限）"""
    async with session.begin():
        position_repo = PositionRepo(session)
        position = await position_repo.get_by_id(position_id)

        if not position:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="职位不存在",
            )

        await embed_position(session, position)

    return {"message": f"职位 {position.title} 向量化完成"}


@router.post("/admin/embed/all", summary="全量职位向量化", response_model=ResponseSchema)
async def embed_all_positions(
    session: AsyncSession = Depends(get_session_instance),
    _=Depends(get_super_user),
):
    """为所有职位生成向量（需要超级用户权限）"""
    async with session.begin():
        result = await session.execute(
            select(PositionModel)
            .where(PositionModel.is_open == True)
            .options(selectinload(PositionModel.department))
        )
        positions = list(result.scalars().all())

        count = 0
        for position in positions:
            try:
                await embed_position(session, position)
                count += 1
            except Exception as e:
                logger.error(f"职位 {position.title} 向量化失败: {e}")

    return {"message": f"已完成 {count}/{len(positions)} 个职位的向量化"}


@router.delete("/admin/embed/position/{position_id}", summary="删除职位向量", response_model=ResponseSchema)
async def delete_position_embedding(
    position_id: str,
    session: AsyncSession = Depends(get_session_instance),
    _=Depends(get_super_user),
):
    """删除职位的向量数据（需要超级用户权限）"""
    async with session.begin():
        repo = PositionEmbeddingRepo(session)
        await repo.delete_by_position_id(position_id)

    return {"message": "向量数据已删除"}


# ==================== 求职者投递简历相关端点 ====================


@router.get("/positions", summary="获取公开职位列表", response_model=PublicPositionListRespSchema)
async def get_open_positions(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=50, description="每页数量"),
    keyword: str | None = Query(None, max_length=100, description="搜索关键词"),
    _: JobSeekerModel = Depends(get_current_job_seeker),
    session: AsyncSession = Depends(get_session_instance),
):
    """获取面向求职者的公开职位列表"""
    async with session.begin():
        position_repo = PositionRepo(session)
        positions, total = await position_repo.get_open_positions(
            page=page, size=size, keyword=keyword,
        )

        position_list = []
        for pos in positions:
            dept_name = pos.department.name if pos.department else ""
            schema = PublicPositionSchema(
                id=pos.id,
                title=pos.title,
                description=pos.description,
                requirements=pos.requirements,
                min_salary=pos.min_salary,
                max_salary=pos.max_salary,
                deadline=pos.deadline,
                recruitment_count=pos.recruitment_count,
                education=pos.education,
                work_year=pos.work_year,
                department_name=dept_name,
            )
            position_list.append(schema)

        return {"positions": position_list, "total": total}


@router.post("/resume/upload", summary="求职者上传简历", response_model=ResumeParseTaskRespSchema)
async def seeker_resume_upload(
    file: UploadFile = File(...),
    job_seeker: JobSeekerModel = Depends(get_current_job_seeker),
    session: AsyncSession = Depends(get_session_instance),
):
    """求职者上传简历文件"""
    file_path = await save_resume_file(file)

    async with session.begin():
        resume_repo = ResumeRepo(session)
        resume = await resume_repo.create_resume_for_seeker(
            file_path=file_path, job_seeker_id=job_seeker.id,
        )

    return {"task_id": resume.id}


@router.post("/apply", summary="提交职位申请", response_model=ResumeParseTaskRespSchema)
async def seeker_apply(
    data: SeekerApplySchema,
    background_tasks: BackgroundTasks,
    job_seeker: JobSeekerModel = Depends(get_current_job_seeker),
    session: AsyncSession = Depends(get_session_instance),
):
    """求职者提交职位申请，触发 AI 处理流水线"""
    async with session.begin():
        # 校验职位存在且开放
        position_repo = PositionRepo(session)
        position = await position_repo.get_by_id(data.position_id)
        if not position or not position.is_open:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该职位不存在或已关闭",
            )

        # 防止重复投递
        existing = await session.scalar(
            select(CandidateModel).where(
                CandidateModel.job_seeker_id == job_seeker.id,
                CandidateModel.position_id == data.position_id,
            )
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="您已投递过该职位，请耐心等待",
            )

    task_id = str(uuid4())
    background_tasks.add_task(
        apply_for_position_task,
        resume_id=data.resume_id,
        position_id=data.position_id,
        job_seeker_id=job_seeker.id,
        task_id=task_id,
    )
    return {"task_id": task_id}


@router.get("/apply/status/{task_id}", summary="查询申请进度", response_model=ResumeParseTaskInfoRespSchema)
async def get_apply_status(
    task_id: str,
    _: JobSeekerModel = Depends(get_current_job_seeker),
    cache: HRCache = Depends(get_cache_instance),
):
    """查询求职者申请处理进度"""
    task_info = await cache.get_task_info(task_id)
    return task_info.model_dump()
