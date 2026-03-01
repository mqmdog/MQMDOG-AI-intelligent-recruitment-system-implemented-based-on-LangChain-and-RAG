import enum
from typing import List, Optional, TYPE_CHECKING

from pwdlib import PasswordHash
from sqlalchemy import String, Text, Enum as SEnum, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from .base import BaseModel

if TYPE_CHECKING:
    from .position import PositionModel

password_hasher = PasswordHash.recommended()


class JobSeekerStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"

# 职位向量块类型枚举
class ChunkType(str, enum.Enum):
    TITLE = "TITLE" 
    DESCRIPTION = "DESCRIPTION"
    REQUIREMENTS = "REQUIREMENTS"
    FULL = "FULL"

# 消息角色枚举
class MessageRole(str, enum.Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"


class JobSeekerModel(BaseModel):
    """求职者用户表，与内部用户完全独立"""
    __tablename__ = "job_seekers"

    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    _password: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    phone_number: Mapped[Optional[str]] = mapped_column(String(20))
    status: Mapped[JobSeekerStatus] = mapped_column(
        SEnum(JobSeekerStatus), default=JobSeekerStatus.ACTIVE
    )

    chat_sessions: Mapped[List["ChatSessionModel"]] = relationship(
        back_populates="job_seeker", cascade="all, delete-orphan"
    )

    def __init__(self, **kwargs):
        if "password" in kwargs:
            raw_password = kwargs.pop("password")
            kwargs["_password"] = password_hasher.hash(raw_password)
        super().__init__(**kwargs)

    @property
    def password(self) -> str:
        return self._password

    @password.setter
    def password(self, password: str) -> None:
        self._password = password_hasher.hash(password)

    def check_password(self, password: str) -> bool:
        return password_hasher.verify(password, self._password)


class PositionEmbeddingModel(BaseModel):
    """职位向量块表，用于 RAG 检索"""
    __tablename__ = "position_embeddings"

    position_id: Mapped[str] = mapped_column(
        ForeignKey("positions.id", ondelete="CASCADE"), index=True
    )
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[List[float]] = mapped_column(
        Vector(1024), nullable=False)
    chunk_type: Mapped[ChunkType] = mapped_column(
        SEnum(ChunkType), nullable=False
    )

    position: Mapped["PositionModel"] = relationship()


class ChatSessionModel(BaseModel):
    """求职者对话会话表"""
    __tablename__ = "job_seeker_chat_sessions"

    job_seeker_id: Mapped[str] = mapped_column(
        ForeignKey("job_seekers.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[Optional[str]] = mapped_column(String(200))

    job_seeker: Mapped["JobSeekerModel"] = relationship(
        back_populates="chat_sessions"
    )
    histories: Mapped[List["ChatHistoryModel"]] = relationship(
        back_populates="session", cascade="all, delete-orphan",
        order_by="ChatHistoryModel.created_at"
    )


class ChatHistoryModel(BaseModel):
    """对话历史消息表"""
    __tablename__ = "job_seeker_chat_histories"

    session_id: Mapped[str] = mapped_column(
        ForeignKey("job_seeker_chat_sessions.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[MessageRole] = mapped_column(
        SEnum(MessageRole), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    retrieved_position_ids: Mapped[Optional[List[str]]] = mapped_column(JSON)

    session: Mapped["ChatSessionModel"] = relationship(
        back_populates="histories")
