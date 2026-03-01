import enum
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import (
    String, Text, Integer, Enum as SQLAlchemyEnum, ForeignKey, JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel
from .user import UserModel, DepartmentModel

if TYPE_CHECKING:
    from .interview import InterviewModel
    from .job_seeker import JobSeekerModel


class CandidateStatusEnum(str, enum.Enum):
    """候选人招聘流程状态"""
    APPLICATION = "已投递"
    AI_FILTER_FAILED = "AI筛选失败"
    AI_FILTER_PASSED = "AI筛选成功"
    WAITING_FOR_INTERVIEW = "待面试"
    REFUSED_INTERVIEW = "拒绝面试"
    INTERVIEW_PASSED = "面试通过"
    INTERVIEW_REJECTED = "面试未通过"
    HIRED = "已入职"
    REJECTED = "已拒绝"


class GenderEnum(str, enum.Enum):
    """性别"""
    MALE = "男"
    FEMALE = "女"
    UNKNOWN = "未知"


class CandidateModel(BaseModel):
    """候选人模型"""
    __tablename__ = "candidates"

    name: Mapped[str] = mapped_column(String(50), nullable=False)
    gender: Mapped[GenderEnum] = mapped_column(
        SQLAlchemyEnum(GenderEnum), default=GenderEnum.UNKNOWN, nullable=False,
    )
    birthday: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[str] = mapped_column(String(100), nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), index=True)
    work_experience: Mapped[Optional[str]] = mapped_column(Text)
    project_experience: Mapped[Optional[str]] = mapped_column(Text)
    education_experience: Mapped[Optional[str]] = mapped_column(Text)
    self_evaluation: Mapped[Optional[str]] = mapped_column(Text)
    other_information: Mapped[Optional[str]] = mapped_column(Text)
    skills: Mapped[Optional[str]] = mapped_column(Text)

    # values_callable: 使用枚举值（中文）存储而非枚举名
    status: Mapped[CandidateStatusEnum] = mapped_column(
        SQLAlchemyEnum(
            CandidateStatusEnum,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        default=CandidateStatusEnum.APPLICATION,
        nullable=False,
    )

    position_id: Mapped[str] = mapped_column(ForeignKey("positions.id"))
    resume_id: Mapped[str] = mapped_column(ForeignKey("resumes.id"))
    creator_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("users.id"), nullable=True)
    job_seeker_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("job_seekers.id"), nullable=True, index=True)

    # 关联: 应聘职位（多对一）
    position: Mapped["PositionModel"] = relationship(
        back_populates="candidates")
    # 关联: 简历（一对一）
    resume: Mapped["ResumeModel"] = relationship(
        back_populates="candidate", uselist=False,
    )
    # 关联: 创建者（多对一，求职者自投时为空）
    creator: Mapped[Optional["UserModel"]] = relationship()
    # 关联: 求职者（多对一，HR创建时为空）
    job_seeker: Mapped[Optional["JobSeekerModel"]] = relationship(
        foreign_keys=[job_seeker_id])
    # 关联: AI评分（一对一）
    ai_score: Mapped["CandidateAIScoreModel"] = relationship(
        back_populates="candidate", uselist=False,
    )
    # 关联: 面试记录（一对多）
    interviews: Mapped[List["InterviewModel"]] = relationship(
        "InterviewModel", back_populates="candidate",
    )


class CandidateAIScoreModel(BaseModel):
    """候选人AI评分模型"""
    __tablename__ = "candidate_ai_scores"

    work_experience_score: Mapped[int] = mapped_column(Integer, nullable=False)
    technical_skills_score: Mapped[int] = mapped_column(
        Integer, nullable=False)
    soft_skills_score: Mapped[int] = mapped_column(Integer, nullable=False)
    educational_background_score: Mapped[int] = mapped_column(
        Integer, nullable=False)
    project_experience_score: Mapped[int] = mapped_column(
        Integer, nullable=False)
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    strengths: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    weaknesses: Mapped[list[str]] = mapped_column(JSON, nullable=False)

    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidates.id"))

    # 关联: 所属候选人（一对一）
    candidate: Mapped["CandidateModel"] = relationship(
        back_populates="ai_score")


class ResumeModel(BaseModel):
    """简历模型"""
    __tablename__ = "resumes"

    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    uploader_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("users.id"), nullable=True)
    job_seeker_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("job_seekers.id"), nullable=True, index=True)

    # 关联: 上传者（多对一，求职者自投时为空）
    uploader: Mapped[Optional["UserModel"]] = relationship()
    # 关联: 求职者（多对一，HR上传时为空）
    job_seeker: Mapped[Optional["JobSeekerModel"]] = relationship(
        foreign_keys=[job_seeker_id])
    # 关联: 所属候选人（一对一）
    candidate: Mapped["CandidateModel"] = relationship(back_populates="resume")
