import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import String, Text, Integer, DateTime, Boolean, Enum as SQLAlchemyEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel
from .user import UserModel, DepartmentModel


class EducationEnum(str, enum.Enum):
    COLLEGE = "大专"
    BACHELOR = "本科"
    MASTER = "硕士"
    DOCTOR = "博士"
    UNKNOWN = "未知"


class PositionModel(BaseModel):
    __tablename__ = "positions"

    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    requirements: Mapped[Optional[str]] = mapped_column(Text)
    min_salary: Mapped[Optional[int]] = mapped_column(Integer)
    max_salary: Mapped[Optional[int]] = mapped_column(Integer)
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime)
    recruitment_count: Mapped[int] = mapped_column(Integer, default=1)
    education: Mapped[EducationEnum] = mapped_column(
        SQLAlchemyEnum(EducationEnum), default=EducationEnum.UNKNOWN, nullable=False,
    )
    work_year: Mapped[int] = mapped_column(Integer, default=0)
    is_open: Mapped[bool] = mapped_column(Boolean, default=True)
    department_id: Mapped[str] = mapped_column(ForeignKey("departments.id"))
    creator_id: Mapped[str] = mapped_column(ForeignKey("users.id"))

    # 关联: 所属部门（多对一）
    department: Mapped["DepartmentModel"] = relationship()
    # 关联: 创建者/招聘专员（多对一）
    creator: Mapped["UserModel"] = relationship()
    # 关联: 申请该职位的候选人（一对多）
    candidates: Mapped[List["CandidateModel"]
                       ] = relationship(back_populates="position")
