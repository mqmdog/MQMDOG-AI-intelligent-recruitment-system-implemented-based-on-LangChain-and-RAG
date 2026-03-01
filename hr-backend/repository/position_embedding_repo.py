"""职位向量 Repository，用于 RAG 检索"""
import logging
from typing import List, Tuple
from datetime import datetime

from sqlalchemy import select, delete, text, func
from sqlalchemy.orm import selectinload

from models.job_seeker import PositionEmbeddingModel, ChunkType
from models.position import PositionModel
from repository import BaseRepo
from settings import settings

logger = logging.getLogger(__name__) # 获取日志记录器


class PositionEmbeddingRepo(BaseRepo):
    """职位向量数据仓库"""

    async def upsert_position_embeddings(
        self,
        position_id: str,
        chunks: List[Tuple[str, List[float], ChunkType]]
    ) -> List[PositionEmbeddingModel]:
        """更新职位的向量块（先删除旧的，再插入新的）"""
        await self.delete_by_position_id(position_id) # 删除旧的向量块

        embeddings = [] 
        # 遍历向量块列表
        for chunk_text, embedding, chunk_type in chunks:
            model = PositionEmbeddingModel(
                position_id=position_id,
                chunk_text=chunk_text,
                embedding=embedding,
                chunk_type=chunk_type,
            )
            self.session.add(model) # 添加模型到会话
            embeddings.append(model) 

        await self.session.flush() # 刷新会话，获取向量块ID
        return embeddings # 返回向量块列表

    async def delete_by_position_id(self, position_id: str) -> None:
        """删除职位的所有向量块"""
        await self.session.execute(
            delete(PositionEmbeddingModel)
            .where(PositionEmbeddingModel.position_id == position_id)
        )

    # 向量相似度搜索
    async def vector_search(
        self,
        query_vector: List[float],
        top_k: int = None,
        is_open_only: bool = True
    ) -> List[Tuple[PositionEmbeddingModel, float]]:
        """向量相似度搜索（余弦距离）"""
        if top_k is None: # 如果未指定top_k，则使用默认值
            top_k = settings.RAG_TOP_K_VECTOR
        
        # 关键点1：计算余弦距离
        # embedding.cosine_distance(query_vector) 计算两个向量的夹角
        # 距离越小，语义越相似
        query = (
            select(
                PositionEmbeddingModel,
                PositionEmbeddingModel.embedding.cosine_distance(
                    query_vector).label("distance")
            )
            .join(PositionModel, PositionEmbeddingModel.position_id == PositionModel.id)
            .options(
                selectinload(PositionEmbeddingModel.position)
                .selectinload(PositionModel.department)
            )
        )
        
        # 关键点2：过滤公开职位
        if is_open_only:
            query = query.where(PositionModel.is_open == True)
            query = query.where(
                (PositionModel.deadline == None) |
                (PositionModel.deadline >= datetime.now())
            )
        
        # 关键点3：按距离（相似度）排序，取top_k
        query = query.order_by("distance").limit(top_k)
        result = await self.session.execute(query)
        # 返回：[(向量块对象, 相似度分数), ...]
        return [(row[0], row[1]) for row in result.all()]


    # 关键词全文搜索
    async def keyword_search(
        self,
        query_text: str,
        top_k: int = None,
        is_open_only: bool = True
    ) -> List[Tuple[PositionEmbeddingModel, float]]:
        """关键词全文搜索（PostgreSQL ts_rank）"""
        if top_k is None:
            top_k = settings.RAG_TOP_K_KEYWORD
        
        # 关键点1：将用户问题转为 tsquery
        ts_query = func.plainto_tsquery('simple', query_text)
        # "Python开发" → tsquery: 'python' & '开发'

        # 关键点2：将文本块转为 tsvector
        ts_vector = func.to_tsvector(
            'simple', PositionEmbeddingModel.chunk_text)
        # "Python开发工程师" → tsvector: 'python':1, '开发':2, '工程师':3

        # 关键点3：计算相关性分数
        rank = func.ts_rank(ts_vector, ts_query).label("rank")
        
        query = (
            select(PositionEmbeddingModel, rank)
            .join(PositionModel, PositionEmbeddingModel.position_id == PositionModel.id)
            .where(ts_vector.op("@@")(ts_query))  # 匹配条件
            .options(
                selectinload(PositionEmbeddingModel.position)
                .selectinload(PositionModel.department)
            )
        )

        if is_open_only:
            query = query.where(PositionModel.is_open == True)
            query = query.where(
                (PositionModel.deadline == None) |
                (PositionModel.deadline >= datetime.now())
            )

        # 关键点4：按相关性排序
        query = query.order_by(rank.desc()).limit(top_k)

        result = await self.session.execute(query)
        return [(row[0], row[1]) for row in result.all()]


    async def get_all_position_ids(self) -> List[str]:
        """获取所有已向量化的职位 ID"""
        result = await self.session.execute(
            select(PositionEmbeddingModel.position_id).distinct()
        )
        return [row[0] for row in result.all()]
