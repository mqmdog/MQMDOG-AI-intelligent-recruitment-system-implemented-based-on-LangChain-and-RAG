from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from settings import settings

# 异步数据库引擎（全局唯一）
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False, #关闭SQL日志输出
    pool_size=10,#连接池大小
    max_overflow=20, #连接池最大溢出数
    pool_timeout=10, #连接池超时时间
    pool_recycle=3600, #连接池回收时间
    pool_pre_ping=True, #连接池预检查
)

# 异步会话工厂
AsyncSessionFactory = sessionmaker(
    bind=engine,  # 绑定上面创建的引擎
    class_=AsyncSession, # 使用AsyncSession作为会话类
    autoflush=True, # 自动刷新更改到数据库
    expire_on_commit=False, #提交后不使得对象过期
)
