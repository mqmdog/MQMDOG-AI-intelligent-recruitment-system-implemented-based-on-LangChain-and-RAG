from fastapi import Depends, APIRouter, HTTPException, status

from models import AsyncSession
from models.user import UserModel
from schemas import ResponseSchema
from schemas.position_schema import PositionCreateSchema, PositionRespSchema, PositionListRespSchema
from dependencies import get_current_user, get_session_instance
from repository.position_repo import PositionRepo

router = APIRouter(prefix="/position", tags=["position"])


@router.post("/create", summary="创建职位", response_model=PositionRespSchema)
async def create_position(
    position_data: PositionCreateSchema,
    current_user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(get_session_instance),
):
    async with session.begin():
        position_repo = PositionRepo(session=session)
        position_dict = position_data.model_dump()
        position_dict["creator_id"] = current_user.id
        position = await position_repo.create_position(position_dict)
        return {"position": position}


@router.get("/list", summary="职位列表", response_model=PositionListRespSchema)
async def get_position_list(
    page: int = 1,
    size: int = 10,
    current_user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(get_session_instance),
):
    async with session.begin():
        position_repo = PositionRepo(session=session)
        positions = await position_repo.get_position_list(current_user, page=page, size=size)
        return {"positions": positions}


@router.delete("/delete/{position_id}", summary="删除职位")
async def delete_position(
    position_id: str,
    current_user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(get_session_instance),
):
    async with session.begin():
        position_repo = PositionRepo(session=session)
        position = await position_repo.get_by_id(position_id)
        if not position:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="职位不存在")
        # superuser 可以直接删除，否则只能删除所属部门的职位
        if not current_user.is_superuser and position.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="无权限删除")
        await position_repo.delete_position(position_id)
        return ResponseSchema()
