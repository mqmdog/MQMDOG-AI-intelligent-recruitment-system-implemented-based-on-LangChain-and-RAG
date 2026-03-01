import os.path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, File, UploadFile, Query
from loguru import logger

from models import AsyncSession
from models.candidate import CandidateStatusEnum
from models.user import UserModel
from schemas import ResponseSchema
from schemas.candidate_schema import (
    ResumeUploadRespSchema, ResumeParseSchema, ResumeParseTaskRespSchema,
    ResumeParseTaskInfoRespSchema, CandidateCreateSchema, CandidateSchema, CandidateListSchema,
)
from schemas.position_schema import PositionSchema
from schemas.user_schema import UserSchema
from dependencies import get_session_instance, get_current_user, get_cache_instance
from repository.resume_repo import ResumeRepo
from repository.candidate_repo import CandidateRepo
from repository.position_repo import PositionRepo
from repository.user_repo import UserRepo
from core.cache import HRCache
from tasks import ocr_parse_resume_task, run_candidate_agent
from settings import settings
from utils.resume_utils import save_resume_file

router = APIRouter(prefix="/candidate", tags=["candidate"])


@router.post("/resume/upload", summary="简历上传", response_model=ResumeUploadRespSchema)
async def resume_upload(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session_instance),
    current_user: UserModel = Depends(get_current_user),
):
    file_path = await save_resume_file(file)

    async with session.begin():
        resume_repo = ResumeRepo(session=session)
        resume = await resume_repo.create_resume(file_path=file_path, uploader_id=current_user.id)
    return {"message": "简历上传成功", "resume": resume}


@router.post("/resume/parse", summary="简历解析", response_model=ResumeParseTaskRespSchema)
async def parse_resume(
    resume_data: ResumeParseSchema,
    background_tasks: BackgroundTasks,
    _: UserModel = Depends(get_current_user),
):
    task_id = str(uuid4())
    background_tasks.add_task(ocr_parse_resume_task,
                              resume_id=resume_data.resume_id, task_id=task_id)
    return {"task_id": task_id}


@router.get("/resume/parse/{task_id}", summary="获取任务状态", response_model=ResumeParseTaskInfoRespSchema)
async def get_task_status(
    task_id: str,
    cache: HRCache = Depends(get_cache_instance),
    _: UserModel = Depends(get_current_user),
):
    task_info = await cache.get_task_info(task_id)
    return task_info.model_dump()


@router.post("/create", summary="创建候选人", response_model=ResponseSchema)
async def create_candidate(
    candidate_data: CandidateCreateSchema,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session_instance),
    current_user: UserModel = Depends(get_current_user),
):
    async with session.begin():
        candidate_dict = candidate_data.model_dump()
        candidate_dict["creator_id"] = current_user.id
        candidate_repo = CandidateRepo(session=session)
        candidate = await candidate_repo.create_candidate(candidate_dict)

        candidate_schema = CandidateSchema.model_validate(candidate)

        position_repo = PositionRepo(session=session)
        position = await position_repo.get_by_id(candidate_data.position_id)
        position_schema = PositionSchema.model_validate(position)

        interviewer_schema = UserSchema.model_validate(position.creator)

    background_tasks.add_task(
        run_candidate_agent,
        candidate=candidate_schema,
        position=position_schema,
        interviewer=interviewer_schema,
    )
    return ResponseSchema()


@router.get("/list", summary="获取候选人列表", response_model=CandidateListSchema)
async def get_candidate_list(
    page: int = Query(1, description="页码"),
    size: int = Query(10, description="每页数量"),
    position_id: str | None = Query(None, description="职位ID"),
    status: CandidateStatusEnum | None = Query(None, description="候选人状态"),
    session: AsyncSession = Depends(get_session_instance),
    current_user: UserModel = Depends(get_current_user),
):
    async with session.begin():
        candidate_repo = CandidateRepo(session=session)
        candidates = await candidate_repo.get_list(
            current_user=current_user,
            page=page,
            size=size,
            position_id=position_id,
            status=status,
        )
        return {"candidates": candidates}


@router.get("/resume/ocr/test")
async def resume_ocr_test():
    try:
        file_path = os.path.join(
            settings.RESUME_DIR, "c5e0f068-bc05-497e-bdf4-ce279d795553.pdf")
        paddle_ocr = PaddleOcr()
        join_id = await paddle_ocr.create_job(file_path)
        join_url = await paddle_ocr.poll_for_state(join_id)
        contents = await paddle_ocr.fetch_parsed_contents(join_url)
        logger.info(contents)
        return {"message": "OCR测试成功", "contents": contents}
    except ValueError as e:
        error_msg = str(e)
        if "超时" in error_msg or "timeout" in error_msg.lower():
            logger.error(f"OCR测试网络超时: {error_msg}")
            raise HTTPException(status_code=504, detail=f"网络连接超时: {error_msg}")
        else:
            logger.error(f"OCR测试失败: {error_msg}")
            raise HTTPException(
                status_code=503, detail=f"OCR服务暂时不可用: {error_msg}")
    except Exception as e:
        logger.error(f"OCR测试出现未知错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"系统错误: {str(e)}")


@router.get("/agent/test")
async def agent_test(
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session_instance),
):
    async with session.begin():
        candidate_repo = CandidateRepo(session=session)
        position_repo = PositionRepo(session=session)
        user_repo = UserRepo(session=session)

        candidate_model = await candidate_repo.get_by_id("Tx4siXK7bkWfo9NirJKuMx")
        position_model = await position_repo.get_by_id("oMp5MzPeUHSSYaVNoX3RBS")
        interviewer_model = await user_repo.get_by_id("E23AF8Wqphh2wPc5Fidxtk")

        return {"result": "success"}
