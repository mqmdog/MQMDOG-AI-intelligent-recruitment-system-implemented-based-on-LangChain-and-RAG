from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from models.candidate import GenderEnum, CandidateStatusEnum
from schemas.cache_schema import TaskInfoSchema
from schemas.position_schema import PositionSchema
from schemas.user_schema import UserSchema


class ResumeSchema(BaseModel):
    id: str = Field(..., description="简历id")
    file_path: str = Field(..., description="简历存储路径")
    uploader: Optional[UserSchema] = Field(None, description="上传者")

    model_config = ConfigDict(from_attributes=True)


class ResumeUploadRespSchema(BaseModel):
    resume: ResumeSchema | None = Field(..., description="简历信息")


class ResumeParseSchema(BaseModel):
    resume_id: str = Field(..., description="简历ID")


class ResumeParseTaskRespSchema(BaseModel):
    task_id: str = Field(..., description="任务ID")


class ResumeParseTaskInfoRespSchema(TaskInfoSchema):
    pass


class CandidateCreateSchema(BaseModel):
    name: str = Field(..., description="候选人姓名")
    email: str = Field(..., description="候选人邮箱")
    gender: GenderEnum = Field(GenderEnum.UNKNOWN, description="候选人性别")
    birthday: str | None = Field(
        None, description="候选人出生日期，如果只有年份，那么就把日期设置为1月1日")
    phone_number: str | None = Field(None, description="候选人电话")
    work_experience: str | None = Field(None, description="候选人工作经历")
    project_experience: str | None = Field(None, description="候选人项目经历")
    education_experience: str | None = Field(None, description="候选人教育经历")
    self_evaluation: str | None = Field(None, description="候选人自我评价")
    other_information: str | None = Field(None, description="候选人其他信息")
    skills: str | None = Field(None, description="候选人技能")

    position_id: str = Field(..., description="候选人职位申请ID")
    resume_id: str = Field(..., description="候选人简历ID")


class CandidateAIScoreSchema(BaseModel):
    id: str = Field(..., description="评分ID")
    work_experience_score: int = Field(..., description="工作经验评分")
    technical_skills_score: int = Field(..., description="技术能力评分")
    soft_skills_score: int = Field(..., description="软技能评分")
    educational_background_score: int = Field(..., description="教育背景评分")
    project_experience_score: int = Field(..., description="项目经验评分")
    overall_score: int = Field(..., description="综合评分")
    summary: str = Field(..., description="评价总结")
    strengths: list[str] = Field(..., description="优势")
    weaknesses: list[str] = Field(..., description="不足")

    model_config = ConfigDict(from_attributes=True)


class CandidateSchema(BaseModel):
    id: str = Field(..., description="候选人ID")
    name: str = Field(..., description="候选人姓名")
    email: str = Field(..., description="候选人邮箱")
    gender: GenderEnum = Field(GenderEnum.UNKNOWN, description="候选人性别")
    birthday: str | None = Field(
        None, description="候选人出生日期，如果只有年份，那么就把日期设置为1月1日")
    phone_number: str | None = Field(None, description="候选人电话")
    work_experience: str | None = Field(None, description="候选人工作经历")
    project_experience: str | None = Field(None, description="候选人项目经历")
    education_experience: str | None = Field(None, description="候选人教育经历")
    self_evaluation: str | None = Field(None, description="候选人自我评价")
    other_information: str | None = Field(None, description="候选人其他信息")
    skills: str | None = Field(None, description="候选人技能")
    status: CandidateStatusEnum | str | None = Field(None, description="候选人状态")
    position: Optional[PositionSchema] = Field(None, description="候选人申请的职位信息")
    resume: Optional[ResumeSchema] = Field(None, description="候选人的简历信息")
    creator: Optional[UserSchema] = Field(None, description="创建该候选人的信息")
    ai_score: Optional[CandidateAIScoreSchema] = Field(
        None, description="AI评分")
    created_at: datetime = Field(..., description="创建时间")

    model_config = ConfigDict(from_attributes=True)


class CandidateListSchema(BaseModel):
    candidates: list[CandidateSchema]


class SeekerApplySchema(BaseModel):
    resume_id: str = Field(..., description="简历ID")
    position_id: str = Field(..., description="投递职位ID")
