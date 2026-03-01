import asyncio
import os

from aiosmtplib import SMTPResponseException
from fastapi_mail import FastMail, MessageSchema
from loguru import logger

from agents.candidate import CandidateProcessAgent
from agents.resume import extract_candidate_info
from core.mail import create_mail_instance
from core.ocr import PaddleOcr
from dependencies import get_cache_instance, HRCache
from models import AsyncSessionFactory
from repository.resume_repo import ResumeRepo
from repository.candidate_repo import CandidateRepo
from repository.position_repo import PositionRepo
from schemas.agent_schema import AgentCandidateSchema
from schemas.cache_schema import TaskInfoSchema
from schemas.candidate_schema import CandidateSchema
from schemas.position_schema import PositionSchema
from schemas.user_schema import UserSchema
from settings import settings


async def send_email_task(message: MessageSchema) -> None:
    mail: FastMail = create_mail_instance()
    try:
        await mail.send_message(message)
    except SMTPResponseException as e:
        if e.code == -1 and b'\\x00\\x00\\x00' in str(e).encode():
            logger.info("忽略 QQ 邮箱 SMTP 关闭阶段的非标准响应（邮件已成功发送）", enqueue=True)
        else:
            logger.error(f"邮件发送失败！{e}")


async def send_invite_email_task(email: str, invite_code: str) -> None:
    html_body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 20px; background-color: #f5f5f5; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" border="0" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 600;">🎉 欢迎加入 MQMDOG</h1>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px 30px;">
                            <p style="font-size: 16px; color: #333333; margin-bottom: 20px;">
                                您好，<strong>{email}</strong>
                            </p>
                            <p style="font-size: 14px; color: #666666; line-height: 1.6;">
                                感谢您注册 MQMDOG！请使用以下邀请码完成注册：
                            </p>
                            <!-- Invite Code -->
                            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin: 20px 0;">
                                <tr>
                                    <td align="center">
                                        <table cellpadding="0" cellspacing="0" border="0">
                                            <tr>
                                                <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 15px 30px; border-radius: 8px; text-align: center;">
                                                    <span style="color: #ffffff; font-size: 28px; font-weight: bold; letter-spacing: 4px
    ">{invite_code}</span>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                            <!-- Info Box -->
                            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f8f9fa; border-left: 4px solid #667eea; margin: 20px 0;">
                                <tr>
                                    <td style="padding: 20px;">
                                        <p style="font-size: 14px; color: #666666; margin: 0 0 8px 0;">⏰ 有效时间</p>
                                        <p style="font-size: 16px; color: #333333; margin: 0; font-weight: 500;">24 小时内有效</p>
                                    </td>
                                </tr>
                            </table>
                            <!-- Notice -->
                            <p style="font-size: 14px; color: #999999; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eeeeee;">
                                💡 提示：如果这不是您本人的操作，请忽略此邮件。
                            </p>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8f9fa; padding: 20px; text-align: center;">
                            <p style="font-size: 12px; color: #999999; margin: 0 0 5px 0;">此邮件由 MQMDOG 系统自动发送，请勿回复</p>
                            <p style="font-size: 12px; color: #999999; margin: 0;">© 2026 MQMDOG. All rights reserved.</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

    message = MessageSchema(
        subject="🎉 MQMDOG - 注册邀请",
        recipients=[email],
        body=html_body,
        subtype="html"
    )
    await send_email_task(message)


async def ocr_parse_resume_task(resume_id: str, task_id: str) -> None:
    async with AsyncSessionFactory() as session:
        async with session.begin():
            resume_repo = ResumeRepo(session=session)
            resume = await resume_repo.get_by_id(resume_id)
    file_path = os.path.join(settings.RESUME_DIR, resume.file_path)
    cache: HRCache = get_cache_instance()
    await cache.set_task_info(TaskInfoSchema(task_id=task_id, status="pending"))
    try:
        paddle_ocr = PaddleOcr()
        join_id = await paddle_ocr.create_job(file_path)
        join_url = await paddle_ocr.poll_for_state(join_id)
        contents = await paddle_ocr.fetch_parsed_contents(join_url)
        content = "\n\n".join(contents)
        candidate_info: AgentCandidateSchema = await extract_candidate_info(content)
        await cache.set_task_info(TaskInfoSchema(task_id=task_id, status="done", result=candidate_info))
    except Exception as e:
        await cache.set_task_info(TaskInfoSchema(task_id=task_id, status="failed", error=str(e)))


async def run_candidate_agent(
    candidate: CandidateSchema,
    position: PositionSchema,
    interviewer: UserSchema
):
    async with CandidateProcessAgent(
        candidate=candidate,
        position=position,
        interviewer=interviewer
    ) as agent:
        thread_id = candidate.email or f"seeker_{candidate.id}"
        response = await agent.ainvoke(
            messages=[{
                "role": "user",
                "content": f"候选人信息：{candidate.model_dump_json()}，职位信息：{position.model_dump_json()}"
            }],
            thread_id=thread_id
        )
        logger.info(f"候选人Agent处理结果: {response}")
        return response


async def apply_for_position_task(
    resume_id: str,
    position_id: str,
    job_seeker_id: str,
    task_id: str,
) -> None:
    """求职者投递职位的完整后台任务：OCR -> AI提取 -> 创建候选人 -> AI评分"""
    cache: HRCache = get_cache_instance()
    await cache.set_task_info(TaskInfoSchema(task_id=task_id, status="pending"))

    try:
        # 1. 获取简历文件路径
        async with AsyncSessionFactory() as session:
            async with session.begin():
                resume_repo = ResumeRepo(session=session)
                resume = await resume_repo.get_by_id(resume_id)
        file_path = resume.file_path

        # 2. OCR 解析
        paddle_ocr = PaddleOcr()
        join_id = await paddle_ocr.create_job(file_path)
        join_url = await paddle_ocr.poll_for_state(join_id)
        contents = await paddle_ocr.fetch_parsed_contents(join_url)
        content = "\n\n".join(contents)
        await cache.set_task_info(TaskInfoSchema(task_id=task_id, status="ocr_done"))

        # 3. AI 提取候选人信息
        candidate_info: AgentCandidateSchema = await extract_candidate_info(content)
        await cache.set_task_info(TaskInfoSchema(task_id=task_id, status="ai_extracted"))

        # 4. 创建候选人记录
        async with AsyncSessionFactory() as session:
            async with session.begin():
                candidate_dict = candidate_info.model_dump()
                candidate_dict["position_id"] = position_id
                candidate_dict["resume_id"] = resume_id
                candidate_dict["job_seeker_id"] = job_seeker_id

                candidate_repo = CandidateRepo(session=session)
                candidate = await candidate_repo.create_candidate(candidate_dict)
                # 重新查询以加载完整的嵌套关系链
                candidate = await candidate_repo.get_by_id(candidate.id)
                candidate_schema = CandidateSchema.model_validate(candidate)

                position_repo = PositionRepo(session=session)
                position = await position_repo.get_by_id(position_id)
                position_schema = PositionSchema.model_validate(position)
                interviewer_schema = UserSchema.model_validate(
                    position.creator)

        await cache.set_task_info(TaskInfoSchema(task_id=task_id, status="candidate_created"))

        # 5. 触发 AI 评分 Agent
        await run_candidate_agent(
            candidate=candidate_schema,
            position=position_schema,
            interviewer=interviewer_schema,
        )
        await cache.set_task_info(TaskInfoSchema(task_id=task_id, status="done"))

    except Exception as e:
        logger.error(f"职位申请任务失败: {e}")
        await cache.set_task_info(TaskInfoSchema(task_id=task_id, status="failed", error=str(e)))
