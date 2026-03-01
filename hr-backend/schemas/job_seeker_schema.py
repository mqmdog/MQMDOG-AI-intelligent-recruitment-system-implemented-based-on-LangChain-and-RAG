"""求职者相关的 Pydantic Schema"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from models.job_seeker import JobSeekerStatus, MessageRole


class JobSeekerRegisterSchema(BaseModel):
    """求职者注册请求"""
    username: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=20)
    phone_number: Optional[str] = None


class JobSeekerLoginSchema(BaseModel):
    """求职者登录请求"""
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=20)


class JobSeekerSchema(BaseModel):
    """求职者信息响应"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    email: str
    phone_number: Optional[str]
    status: JobSeekerStatus
    created_at: datetime


class JobSeekerLoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    refresh_token: str
    job_seeker: JobSeekerSchema
    message: str = "登录成功"


class ChatSessionCreateSchema(BaseModel):
    """创建会话请求"""
    title: Optional[str] = None


class ChatSessionSchema(BaseModel):
    """会话信息响应"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime


class ChatHistorySchema(BaseModel):
    """历史消息响应"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: MessageRole
    content: str
    retrieved_position_ids: Optional[List[str]]
    created_at: datetime


class ChatSessionListResponse(BaseModel):
    """会话列表响应"""
    sessions: List[ChatSessionSchema]


class ChatHistoryResponse(BaseModel):
    """历史消息列表响应"""
    histories: List[ChatHistorySchema]


class ChatMessageSchema(BaseModel):
    """发送消息请求"""
    session_id: str
    message: str = Field(..., min_length=1, max_length=2000)


class PositionSourceSchema(BaseModel):
    """检索来源的职位信息"""
    id: str
    title: str


class SSEEventSchema(BaseModel):
    """SSE 事件格式"""
    type: str
    layer: Optional[int] = None
    content: Optional[str] = None
    positions: Optional[List[PositionSourceSchema]] = None
