from sqlalchemy import select
from typing import Sequence, List
from sqlalchemy.orm import selectinload # 预加载关联数据,避免N+1查询

from . import BaseRepo
from models.user import UserModel, DingdingUserModel, DepartmentModel


class UserRepo(BaseRepo):
    # 创建用户
    async def create_user(self, user_data: dict) -> UserModel:
        user = UserModel(**user_data)
        self.session.add(user)
        return user

    # 根据用户ID获取用户
    async def get_by_id(self, user_id: str) -> UserModel | None:
        return await self.session.scalar(
            select(UserModel)
            .where(UserModel.id == user_id)
            .options(selectinload(UserModel.department)) 
        )
    
    # 根据用户邮箱获取用户
    async def get_by_email(self, email: str) -> UserModel | None:
        return await self.session.scalar(
            select(UserModel)
            .where(UserModel.email == email)
            .options(selectinload(UserModel.department))
        )

    # 根据部门ID获取用户列表
    async def get_user_list(
        self,
        page: int = 1, # 页码
        size: int = 10, # 每页大小
        department_id: str | None = None,
    ) -> Sequence[UserModel]:
        stmt = select(UserModel).options(selectinload(UserModel.department)) 
        if department_id:
            stmt = stmt.where(UserModel.department_id == department_id)
        offset = (page - 1) * size # 计算偏移量
        stmt = stmt.limit(size).offset(offset).order_by(
            UserModel.created_at.desc()) # 按创建时间降序排序
        result = await self.session.scalars(stmt)
        return result.all()

    # 设置钉钉用户信息
    async def set_dingding_user(self, user_id: str, dingding_user_data: dict) -> DingdingUserModel:
        #检查用户是否存在
        user = await self.get_by_id(user_id)
        if not user:
            raise ValueError("设置钉钉的用户不存在！")

        #查询是否已存在钉钉用户信息
        dingding_user = await self.session.scalar(
            select(DingdingUserModel).where(
                DingdingUserModel.user_id == user_id)
        )
        #有则更新，没有则创建
        if dingding_user:
            for key, value in dingding_user_data.items():
                setattr(dingding_user, key, value)
        else:
            dingding_user = DingdingUserModel(
                **dingding_user_data, user_id=user_id)
            self.session.add(dingding_user)
        return dingding_user

    # 根据用户ID获取钉钉用户信息
    async def get_dingding_user(self, user_id: str) -> DingdingUserModel | None:
        return await self.session.scalar(
            select(DingdingUserModel).where(
                DingdingUserModel.user_id == user_id)
        )

    # 分配HR管理部门
    async def assign_department(self, hr_id: str, department_ids: List[str]) -> None:
        # 查询 HR 用户，预加载关联的部门
        hr_stmt = (
            select(UserModel)
            .where(UserModel.id == hr_id)
            .options(selectinload(UserModel.managed_departments))
        )
        hr: UserModel = await self.session.scalar(hr_stmt)
        if not hr:
            raise ValueError("该用户不存在！")
        # 批量查询部门并替换
        department_stmt = select(DepartmentModel).where(
            DepartmentModel.id.in_(department_ids))
        departments = (await self.session.scalars(department_stmt)).all()
        hr.managed_departments = departments
