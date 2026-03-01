from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from models.position import EducationEnum
from schemas.user_schema import UserSchema, DepartmentSchema


class PositionBaseSchema(BaseModel):
    title: str = Field(..., description="职位标题")
    description: Optional[str] = Field(..., description="职位描述")
    requirements: str = Field(..., description="职位要求")
    min_salary: int = Field(..., description="最低薪资")
    max_salary: int = Field(..., description="最高薪资")
    deadline: Optional[datetime] = Field(None, description="招聘截止日期")
    recruitment_count: int = Field(1, description="职位招聘人数")
    education: EducationEnum = Field(..., description="教育背景")
    work_year: int = Field(0, description="工作年限")
    is_open: bool = Field(True, description="是否开放")


class PositionCreateSchema(PositionBaseSchema):
    department_id: str = Field(..., description="所属部门ID")


class PositionSchema(PositionBaseSchema):
    id: str = Field(..., description="职位ID")
    creator: UserSchema = Field(..., description="职位创建者")
    department: DepartmentSchema = Field(..., description="职位所属部门")

    model_config = ConfigDict(from_attributes=True)


class PositionRespSchema(BaseModel):
    position: PositionSchema | None


class PositionListRespSchema(BaseModel):
    positions: List[PositionSchema] | None


class PublicPositionSchema(PositionBaseSchema):
    """面向求职者的公开职位视图"""
    id: str = Field(..., description="职位ID")
    department_name: str = Field("", description="部门名称")

    model_config = ConfigDict(from_attributes=True)


class PublicPositionListRespSchema(BaseModel):
    positions: List[PublicPositionSchema] 
    total: int = Field(0, description="总数")
