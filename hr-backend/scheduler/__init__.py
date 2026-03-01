from apscheduler.schedulers.asyncio import AsyncIOScheduler
from core.email_bot import EmailBot
from core.email_bot.settings import EmailBotSettings
from loguru import logger
from agents.candidate import CandidateProcessAgent
from langchain.messages import HumanMessage
from settings import settings
from core.cache import HRCache

scheduler = AsyncIOScheduler()

# 轮询并处理邮件

"""
状态管理：使用 state 字典跟踪最后处理的邮件 UID，确保只处理新邮件
去重处理：跳过由当前账户发送的邮件，避免处理回路
线程管理：使用发件人地址作为线程 ID，保持对话上下文
持久化：将最新的 UID 保存到缓存中，保证服务重启后能继续从正确位置开始处理
"""

async def poll_and_process_emails(bot: EmailBot, state: dict):
    try:
        last_uid = state.get("last_uid")
        if last_uid is None:
            last_uid = await bot.get_max_uid() or 0
        state["last_uid"] = last_uid
        logger.info(f"Initialized last_uid={last_uid}")

        new_emails = await bot.fetch_since_uid(last_uid)
        if not new_emails:
            return

        new_emails.sort(key=lambda e: int(e.uid))

        async with CandidateProcessAgent() as agent:
            for mail in new_emails:
                if mail.from_.address.lower() == bot.settings.email.lower():
                    continue

                thread_id = mail.from_.address
                response = await agent.ainvoke(
                    messages=[HumanMessage(content=f"收到邮件内容：{mail.text or mail.html}")],
                    thread_id=thread_id
                )
                logger.info(f"Processed email from {thread_id}, response: {response}")

                state["last_uid"] = max(state["last_uid"], int(mail.uid))
                cache = HRCache()
                await cache.set_email_last_uid(state["last_uid"])

            logger.info(f"Processed {len(new_emails)} new emails, last_uid now {state['last_uid']}")

    except Exception as e:
        logger.exception(f"Failed to poll and process emails: {e}")


# 启动邮件轮询
"""
配置加载：从系统设置中加载邮件服务器配置
状态恢复：从缓存中恢复上次处理的邮件 UID，实现服务重启后的无缝衔接
定时任务：每 15 秒执行一次邮件检查，频率可调
并发控制：使用 max_instances=1 确保同一任务不会并发执行
"""

async def start_email_polling():
    """Initializes and starts the email polling scheduler."""
    email_settings = EmailBotSettings(
        imap_host=settings.EMAIL_BOT_IMAP_HOST,
        smtp_host=settings.EMAIL_BOT_SMTP_HOST,
        email=settings.EMAIL_BOT_EMAIL,
        password=settings.EMAIL_BOT_PASSWORD,
    )
    #缓存初始化和状态恢复
    cache = HRCache()  # Initialize cache
    last_uid = await cache.get_email_last_uid()  # Get last_uid from cache
    state: dict = {"last_uid": last_uid}  # 创建状态字典
    
    # 创建邮件机器人实例并连接
    bot = EmailBot(email_settings)
    await bot.connect()

    # 调度任务配置
    scheduler.add_job(poll_and_process_emails, "interval", seconds=15, args=[bot, state], max_instances=1) #任务函数、建个触发器类型，每15秒检查一次，传递机器人实例和状态字典，确保同一任务不会并发执行
    scheduler.start()
    logger.info("Scheduler started, polling inbox...")
    return bot, scheduler