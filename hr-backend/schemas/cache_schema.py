from typing import Any, Literal

from pydantic import BaseModel, EmailStr

from schemas.agent_schema import AgentCandidateSchema


# 邀请信息
class InviteInfoSchema(BaseModel):
    email: EmailStr
    department_id: str
    invite_code: str

# 钉钉token信息
class DingTalkTokenInfoSchema(BaseModel):
    access_token: str
    refresh_token: str
    user_id: str

# 任务信息
class TaskInfoSchema(BaseModel):
    task_id: str
    status: Literal['pending', 'ocr_done', 'ai_extracted',
                    'candidate_created', 'done', 'failed']
    result: AgentCandidateSchema | None = None
    error: str | None = None
