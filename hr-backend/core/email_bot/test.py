from core.email_bot.bot import EmailBot, EmailBotSettings
import asyncio
import os
import sys

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from loguru import logger

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
load_dotenv()


REPLY_TEXT = "我已经收到，会尽快处理。"


async def poll_and_reply(bot: EmailBot, state: dict):
    try:
        last_uid = state.get("last_uid")
        if last_uid is None:
            state["last_uid"] = await bot.get_max_uid() or 0
            logger.info("init last_uid={}", state["last_uid"])
            return

        new_emails = await bot.fetch_since_uid(last_uid)
        if not new_emails:
            return

        new_emails.sort(key=lambda e: int(e.uid)
                        if str(e.uid).isdigit() else 0)

        for mail in new_emails:
            if mail.from_.address.lower() == bot.settings.email.lower():
                continue
            await bot.reply(mail, text=REPLY_TEXT)
            state["last_uid"] = max(state["last_uid"], int(mail.uid)) if str(
                mail.uid).isdigit() else state["last_uid"]

        logger.info("processed {} new emails, last_uid now {}",
                    len(new_emails), state["last_uid"])

    except Exception as e:
        logger.exception("poll_and_reply failed: {}", e)


async def main():
    mail_username = os.getenv("MAIL_USERNAME")
    mail_password = os.getenv("MAIL_PASSWORD")

    logger.info(f"MAIL_USERNAME: {mail_username}")
    logger.info(
        f"MAIL_PASSWORD: {'*' * len(mail_password) if mail_password else 'None'}")

    if not mail_username or not mail_password:
        logger.error("环境变量 MAIL_USERNAME 或 MAIL_PASSWORD 未设置！")
        return

    email_settings = EmailBotSettings(
        imap_host="imap.qq.com",
        smtp_host="smtp.qq.com",
        email=mail_username,
        password=mail_password,
    )
    state: dict = {"last_uid": None}

    async with EmailBot(email_settings) as bot:
        scheduler = AsyncIOScheduler()
        scheduler.add_job(poll_and_reply, "interval", seconds=15, args=[
                          bot, state], max_instances=1)
        scheduler.start()

        max_uid = await bot.get_max_uid()
        state["last_uid"] = max_uid or 0
        logger.info(f"初始化 last_uid={state['last_uid']}")
        logger.info("scheduler started, polling inbox...")
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
