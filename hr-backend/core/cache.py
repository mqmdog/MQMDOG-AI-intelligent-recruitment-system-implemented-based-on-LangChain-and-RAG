from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

from core.single import SingletonMeta
from schemas.cache_schema import InviteInfoSchema, DingTalkTokenInfoSchema, TaskInfoSchema
from settings import settings


class HRCache(metaclass=SingletonMeta):
    """Redis 缓存操作封装（单例）"""

    invite_prefix = "invite:"
    dingtalk_prefix = "dingtalk:"
    task_prefix = "task:"
    email_last_uid_key = "email:last_uid"

    def __init__(self):
        self.cache_backend: RedisBackend = FastAPICache.get_backend()

    async def set(self, key: str, value: str, ex: int) -> None:
        await self.cache_backend.set(key, value, expire=ex if ex else None)

    async def get(self, key: str) -> str | None:
        return await self.cache_backend.get(key)

    async def delete(self, key: str) -> None:
        await self.cache_backend.clear(key)

    # ---- 邀请码 ----
    # 存储邀请信息，使用邮箱作为键，过期时间从settings获取
    async def set_invite_info(self, invite_info: InviteInfoSchema) -> None:
        key = f"{self.invite_prefix}{invite_info.email}"
        await self.set(key, invite_info.model_dump_json(), ex=settings.INVITE_CODE_EXPIRES)
    # 根据邮箱获取邀请信息，自动反序列化为InviteInfoSchema对象
    async def get_invite_info(self, email: str) -> InviteInfoSchema | None:
        key = f"{self.invite_prefix}{email}"
        value = await self.get(key)
        if value is not None:
            return InviteInfoSchema.model_validate_json(value)
        return None

    # ---- 钉钉 Token ----
    # 存储钉钉Token信息，使用用户ID作为键，过期时间设置为29天
    async def set_dingtalk_token_info(self, info: DingTalkTokenInfoSchema) -> None:
        key = f"{self.dingtalk_prefix}{info.user_id}"
        await self.set(key, info.model_dump_json(), ex=60 * 60 * 24 * 29)
    # 根据用户ID获取钉钉Token信息，自动反序列化为DingTalkTokenInfoSchema对象
    async def get_dingtalk_info(self, user_id: str) -> DingTalkTokenInfoSchema | None:
        key = f"{self.dingtalk_prefix}{user_id}"
        value = await self.get(key)
        if value is None:
            return None
        return DingTalkTokenInfoSchema.model_validate_json(value)

    # ---- 后台任务 ----
    # 存储任务信息，使用任务ID作为键，过期时间设置为1小时
    async def set_task_info(self, task_info: TaskInfoSchema) -> None:
        key = f"{self.task_prefix}{task_info.task_id}"
        await self.set(key, task_info.model_dump_json(), ex=60 * 60)
    # 根据任务ID获取任务信息，自动反序列化为TaskInfoSchema对象
    async def get_task_info(self, task_id: str) -> TaskInfoSchema | None:
        key = f"{self.task_prefix}{task_id}"
        value = await self.get(key)
        if value is not None:
            return TaskInfoSchema.model_validate_json(value)
        return None

    # ---- 邮件 UID ----
    # 存储邮件最后的UID，使用固定键，可选过期时间
    async def set_email_last_uid(self, last_uid: int, *, ex: int | None = None) -> None:
        await self.set(self.email_last_uid_key, str(int(last_uid)), ex=ex or 0)
    # 根据固定键获取邮件最后的UID，自动转换为int类型
    async def get_email_last_uid(self) -> int | None:
        value = await self.get(self.email_last_uid_key)
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
