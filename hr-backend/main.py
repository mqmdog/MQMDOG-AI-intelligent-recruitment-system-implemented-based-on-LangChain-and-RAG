from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from loguru import logger
from redis import asyncio as aioredis

from routers.user_router import router as user_router
from routers.position_router import router as position_router
from routers.candidate_router import router as candidate_router
from routers.job_qa_router import router as job_qa_router

from scheduler import start_email_polling
from settings import settings


"""
应用的生命周期管理器
"""
@asynccontextmanager
async def lifespan(_: FastAPI):
    # 启动阶段：初始化 Redis 缓存和邮件轮询
    redis_client = aioredis.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
        encoding="utf-8",
        decode_responses=True,
    )
    cache_backend = RedisBackend(redis_client)
    FastAPICache.init(cache_backend, prefix="fastapi-cache")  # 初始化 FastAPI 缓存

    # 尝试启动邮件轮询，失败时记录警告但不阻塞服务启动
    try:
        bot, scheduler = await start_email_polling() 
    except Exception as e:
        logger.warning(f"邮件轮询启动失败，服务将继续运行: {e}")
        # 创建空的 bot 和 scheduler 以避免关闭时出错
        from core.email_bot.bot import EmailBot
        from apscheduler.scheduler import Scheduler
        from core.email_bot.settings import EmailBotSettings

        email_settings = EmailBotSettings(
            imap_host=settings.EMAIL_BOT_IMAP_HOST,
            smtp_host=settings.EMAIL_BOT_SMTP_HOST,
            email=settings.EMAIL_BOT_EMAIL,
            password=settings.EMAIL_BOT_PASSWORD,
        )
        bot = EmailBot(email_settings)
        scheduler = Scheduler()

    # 暂停执行，将控制权交给应用运行阶段。应用运行期间会保持在此处
    yield

    # 关闭阶段：释放资源
    await redis_client.close()
    try:
        if bot.is_connected:
            await bot.close()
        if scheduler.running:
            scheduler.shutdown()
    except Exception as e:
        logger.warning(f"关闭资源时出错: {e}")


# 创建 FastAPI 应用实例，使用上面定义的 lifespan 上下文管理器。
app = FastAPI(lifespan=lifespan)

# 添加跨域中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由注册
app.include_router(user_router)
app.include_router(position_router)
app.include_router(candidate_router)
app.include_router(job_qa_router)

# 根路径路由


@app.get("/")
async def root():
    return {"message": "Hello World"}
