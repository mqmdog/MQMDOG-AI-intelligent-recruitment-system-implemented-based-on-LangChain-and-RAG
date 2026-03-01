from sqlalchemy import select, delete
from typing import Sequence

from . import BaseRepo
from models.user import DepartmentModel


class DepartmentRepo(BaseRepo):
    async def create_department(self, department_data: dict) -> DepartmentModel:
        department = DepartmentModel(**department_data)
        self.session.add(department)
        return department

    async def get_by_id(self, department_id: str) -> DepartmentModel | None:
        return await self.session.scalar(
            select(DepartmentModel).where(DepartmentModel.id == department_id)
        )

    async def get_by_name(self, department_name: str) -> DepartmentModel | None:
        return await self.session.scalar(
            select(DepartmentModel).where(
                DepartmentModel.name == department_name)
        )

    async def get_department_list(self) -> Sequence[DepartmentModel]:
        result = await self.session.scalars(select(DepartmentModel))
        return result.all()

    async def delete_department(self, department_id: str) -> None:
        await self.session.execute(
            delete(DepartmentModel).where(DepartmentModel.id == department_id)
        )
