"""对话会话和历史 Repository"""
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from models.job_seeker import ChatSessionModel, ChatHistoryModel, MessageRole
from repository import BaseRepo


class ChatRepo(BaseRepo):
    """对话数据仓库"""

    async def create_session(
        self,
        job_seeker_id: str,
        title: Optional[str] = None
    ) -> ChatSessionModel:
        """创建新会话"""
        session = ChatSessionModel(
            job_seeker_id=job_seeker_id,
            title=title,
        )
        self.session.add(session)
        await self.session.flush()
        await self.session.refresh(session)
        return session

    async def get_session_by_id(self, session_id: str) -> ChatSessionModel | None:
        """获取会话详情"""
        return await self.session.scalar(
            select(ChatSessionModel)
            .where(ChatSessionModel.id == session_id)
            .options(selectinload(ChatSessionModel.histories))
        )

    async def get_session_list(
        self,
        job_seeker_id: str,
        page: int = 1,
        size: int = 20
    ) -> List[ChatSessionModel]:
        """获取求职者的会话列表"""
        offset = (page - 1) * size
        result = await self.session.execute(
            select(ChatSessionModel)
            .where(ChatSessionModel.job_seeker_id == job_seeker_id)
            .order_by(ChatSessionModel.updated_at.desc())
            .offset(offset)
            .limit(size)
        )
        return list(result.scalars().all())

    async def update_session_title(
        self,
        session_id: str,
        title: str
    ) -> None:
        """更新会话标题"""
        session = await self.session.scalar(
            select(ChatSessionModel).where(ChatSessionModel.id == session_id)
        )
        if session:
            session.title = title

    async def create_history(
        self,
        session_id: str,
        role: MessageRole,
        content: str,
        retrieved_position_ids: Optional[List[str]] = None,
    ) -> ChatHistoryModel:
        """创建历史消息"""
        history = ChatHistoryModel(
            session_id=session_id,
            role=role,
            content=content,
            retrieved_position_ids=retrieved_position_ids,
        )
        self.session.add(history)
        await self.session.flush()
        await self.session.refresh(history)
        return history

    async def get_history(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[ChatHistoryModel]:
        """获取会话的最近历史消息"""
        result = await self.session.execute(
            select(ChatHistoryModel)
            .where(ChatHistoryModel.session_id == session_id)
            .order_by(ChatHistoryModel.created_at.desc())
            .limit(limit)
        )
        histories = list(result.scalars().all())
        histories.reverse()
        return histories

    async def get_all_history(self, session_id: str) -> List[ChatHistoryModel]:
        """获取会话的所有历史消息"""
        result = await self.session.execute(
            select(ChatHistoryModel)
            .where(ChatHistoryModel.session_id == session_id)
            .order_by(ChatHistoryModel.created_at.asc())
        )
        return list(result.scalars().all())

    async def delete_session(self, session_id: str) -> None:
        """删除会话（级联删除历史）"""
        session = await self.session.scalar(
            select(ChatSessionModel).where(ChatSessionModel.id == session_id)
        )
        if session:
            await self.session.delete(session)
