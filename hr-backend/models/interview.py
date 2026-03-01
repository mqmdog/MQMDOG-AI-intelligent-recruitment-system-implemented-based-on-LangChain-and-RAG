import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel
from .user import UserModel
from .candidate import CandidateModel


class InterviewResultEnum(str, enum.Enum):
    """面试结果"""
    PENDING = "PENDING"
    PASSED = "PASSED"
    FAILED = "FAILED"


class InterviewModel(BaseModel):
    """面试模型"""
    __tablename__ = "interviews"

    scheduled_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    feedback: Mapped[Optional[str]] = mapped_column(Text)
    result: Mapped[Optional[InterviewResultEnum]] = mapped_column(
        Enum(InterviewResultEnum),
    )

    # unique=True: 一个候选人只能有一条面试记录（一对一）
    candidate_id: Mapped[str] = mapped_column(
        ForeignKey("candidates.id"), unique=True,
    )
    interviewer_id: Mapped[str] = mapped_column(ForeignKey("users.id"))

    # 关联: 面试对应的候选人（一对一）
    candidate: Mapped["CandidateModel"] = relationship(
        back_populates="interviews",
    )
    # 关联: 面试官（多对一）
    interviewer: Mapped["UserModel"] = relationship()
