"""求职者问答 Agent - 四层 RAG 架构实现"""
import json
from typing import List, Dict, Any, AsyncGenerator, Optional
from dataclasses import dataclass
from collections import defaultdict

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.messages import HumanMessage, SystemMessage

from agents.llms import qwen_llm, deepseek_llm
from agents.prompts_job_seeker import (
    QUERY_UNDERSTANDING_PROMPT,
    RERANK_PROMPT,
    JOBSEEKER_ANSWER_PROMPT,
    POSITION_CHUNK_TEMPLATE,
)
from core.embedding import embedding_client
from repository.position_embedding_repo import PositionEmbeddingRepo
from repository.chat_repo import ChatRepo
from models.job_seeker import PositionEmbeddingModel, ChatHistoryModel, MessageRole, ChunkType
from models.position import PositionModel
from settings import settings


@dataclass
class QueryAnalysis:
    """查询分析结果"""
    intent: str
    rewritten_queries: List[str]
    key_entities: List[str]


@dataclass
class RetrievedChunk:
    """检索到的文本块"""
    chunk_id: str
    position_id: str
    chunk_text: str
    chunk_type: ChunkType
    position: PositionModel
    score: float
    source: str


class QueryUnderstandingLayer:
    """Layer 1: 查询理解与改写层"""

    async def process(
        self,
        user_question: str,
        chat_history: List[ChatHistoryModel]
    ) -> QueryAnalysis:
        """分析用户查询，识别意图并改写"""
        history_text = self._format_history(chat_history)

        prompt = QUERY_UNDERSTANDING_PROMPT.format(
            chat_history=history_text,
            user_question=user_question,
        )

        try:
            response = await qwen_llm.ainvoke([HumanMessage(content=prompt)])
            result = self._parse_response(response.content)
            return result
        except Exception as e:
            logger.error(f"查询理解失败: {e}")
            return QueryAnalysis(
                intent="GENERAL",
                rewritten_queries=[user_question],
                key_entities=[],
            )

    def _format_history(self, history: List[ChatHistoryModel]) -> str:
        if not history:
            return "无历史对话"

        lines = []
        for msg in history[-6:]:
            role = "用户" if msg.role == MessageRole.USER else "助手"
            lines.append(f"{role}: {msg.content[:200]}")
        return "\n".join(lines)

    def _parse_response(self, content: str) -> QueryAnalysis:
        try:
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]

            data = json.loads(content.strip())
            return QueryAnalysis(
                intent=data.get("intent", "GENERAL"),
                rewritten_queries=data.get("rewritten_queries", []),
                key_entities=data.get("key_entities", []),
            )
        except json.JSONDecodeError:
            logger.warning(f"JSON 解析失败: {content}")
            return QueryAnalysis(
                intent="GENERAL",
                rewritten_queries=[],
                key_entities=[],
            )


class HybridRetrievalLayer:
    """Layer 2: 混合检索层（向量 + 关键词）"""

    def __init__(self, session: AsyncSession):
        self.repo = PositionEmbeddingRepo(session)

    async def retrieve(
        self,
        analysis: QueryAnalysis
    ) -> List[RetrievedChunk]:
        """执行混合检索并融合结果"""
        queries = analysis.rewritten_queries or [
            analysis.key_entities[0] if analysis.key_entities else ""]
        if not queries or not queries[0]:
            return []

        vector_results = await self._vector_search(queries)
        keyword_results = await self._keyword_search(queries)

        fused_results = self._rrf_fusion(vector_results, keyword_results)
        return fused_results[:10]

    async def _vector_search(self, queries: List[str]) -> List[RetrievedChunk]:
        """向量相似度搜索"""
        try:
            embeddings = await embedding_client.embed_batch(queries)
            avg_embedding = [
                sum(emb[i] for emb in embeddings) / len(embeddings)
                for i in range(len(embeddings[0]))
            ]

            results = await self.repo.vector_search(avg_embedding)

            return [
                RetrievedChunk(
                    chunk_id=chunk.id,
                    position_id=chunk.position_id,
                    chunk_text=chunk.chunk_text,
                    chunk_type=chunk.chunk_type,
                    position=chunk.position,
                    score=1 - distance,
                    source="vector",
                )
                for chunk, distance in results
            ]
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            return []

    async def _keyword_search(self, queries: List[str]) -> List[RetrievedChunk]:
        """关键词全文搜索"""
        try:
            query_text = " ".join(queries)
            results = await self.repo.keyword_search(query_text)

            return [
                RetrievedChunk(
                    chunk_id=chunk.id,
                    position_id=chunk.position_id,
                    chunk_text=chunk.chunk_text,
                    chunk_type=chunk.chunk_type,
                    position=chunk.position,
                    score=rank,
                    source="keyword",
                )
                for chunk, rank in results
            ]
        except Exception as e:
            logger.error(f"关键词搜索失败: {e}")
            return []

    def _rrf_fusion(
        self,
        vector_results: List[RetrievedChunk],
        keyword_results: List[RetrievedChunk],
        k: int = 60
    ) -> List[RetrievedChunk]:
        """RRF (Reciprocal Rank Fusion) 融合"""
        rrf_scores: Dict[str, float] = defaultdict(float)
        chunk_map: Dict[str, RetrievedChunk] = {}

        for rank, chunk in enumerate(vector_results):
            rrf_scores[chunk.chunk_id] += 1 / (k + rank + 1)
            chunk_map[chunk.chunk_id] = chunk

        for rank, chunk in enumerate(keyword_results):
            rrf_scores[chunk.chunk_id] += 1 / (k + rank + 1)
            if chunk.chunk_id not in chunk_map:
                chunk_map[chunk.chunk_id] = chunk

        sorted_ids = sorted(rrf_scores.keys(),
                            key=lambda x: rrf_scores[x], reverse=True)

        result = []
        for chunk_id in sorted_ids:
            chunk = chunk_map[chunk_id]
            chunk.score = rrf_scores[chunk_id]
            result.append(chunk)

        return result


class RerankFilterLayer:
    """Layer 3: 重排序与过滤层"""

    async def rerank_and_filter(
        self,
        user_question: str,
        chunks: List[RetrievedChunk]
    ) -> List[RetrievedChunk]:
        """重排序和过滤"""
        if not chunks:
            return []

        scored_chunks = await self._llm_rerank(user_question, chunks)

        filtered = [c for c in scored_chunks if c.score >= 3]

        deduplicated = self._deduplicate(filtered)

        return deduplicated[:settings.RAG_TOP_K_RERANK]

    async def _llm_rerank(
        self,
        user_question: str,
        chunks: List[RetrievedChunk]
    ) -> List[RetrievedChunk]:
        """使用 LLM 对候选文档打分"""
        candidates_text = "\n\n".join([
            f"[{i}] {chunk.chunk_text[:500]}"
            for i, chunk in enumerate(chunks)
        ])

        prompt = RERANK_PROMPT.format(
            user_question=user_question,
            candidates=candidates_text,
        )

        try:
            response = await deepseek_llm.ainvoke([HumanMessage(content=prompt)])
            scores = self._parse_scores(response.content)

            for i, chunk in enumerate(chunks):
                chunk.score = scores.get(i, 0)

            return sorted(chunks, key=lambda x: x.score, reverse=True)
        except Exception as e:
            logger.error(f"LLM 重排失败: {e}")
            return chunks

    def _parse_scores(self, content: str) -> Dict[int, float]:
        """解析 LLM 返回的评分"""
        try:
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]

            data = json.loads(content.strip())
            return {item["index"]: item["score"] for item in data}
        except:
            return {}

    def _deduplicate(self, chunks: List[RetrievedChunk]) -> List[RetrievedChunk]:
        """去重：同一职位最多保留 1 个 chunk"""
        seen_positions = set()
        result = []

        for chunk in chunks:
            if chunk.position_id not in seen_positions:
                seen_positions.add(chunk.position_id)
                result.append(chunk)

        return result


class GenerationValidationLayer:
    """Layer 4: 生成与验证层"""

    async def generate_stream(
        self,
        user_question: str,
        chunks: List[RetrievedChunk],
        chat_history: List[ChatHistoryModel],
    ) -> AsyncGenerator[str, None]:
        """流式生成回答"""
        context = self._build_context(chunks)
        history_text = self._format_history(chat_history)

        prompt = JOBSEEKER_ANSWER_PROMPT.format(
            chat_history=history_text,
            context=context,
            user_question=user_question,
        )

        async for chunk in qwen_llm.astream([HumanMessage(content=prompt)]):
            if chunk.content:
                yield chunk.content

    def _build_context(self, chunks: List[RetrievedChunk]) -> str:
        if not chunks:
            return "暂无相关职位信息"

        contexts = []
        for chunk in chunks:
            pos = chunk.position
            salary = "面议"
            if pos.min_salary and pos.max_salary:
                salary = f"{pos.min_salary}k-{pos.max_salary}k"
            elif pos.min_salary:
                salary = f"{pos.min_salary}k起"
            elif pos.max_salary:
                salary = f"最高{pos.max_salary}k"

            dept_name = pos.department.name if pos.department else "未知部门"

            context = POSITION_CHUNK_TEMPLATE.format(
                title=pos.title,
                department=dept_name,
                salary=salary,
                education=pos.education.value if pos.education else "不限",
                work_year=pos.work_year or 0,
                description=pos.description or "暂无描述",
                requirements=pos.requirements or "暂无要求",
            )
            contexts.append(context)

        return "\n---\n".join(contexts)

    def _format_history(self, history: List[ChatHistoryModel]) -> str:
        if not history:
            return "无历史对话"

        lines = []
        for msg in history[-6:]:
            role = "用户" if msg.role == MessageRole.USER else "助手"
            lines.append(f"{role}: {msg.content[:300]}")
        return "\n".join(lines)


class JobQAAgent:
    """求职者问答 Agent - 四层 RAG 编排器"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.layer1 = QueryUnderstandingLayer()
        self.layer2 = HybridRetrievalLayer(session)
        self.layer3 = RerankFilterLayer()
        self.layer4 = GenerationValidationLayer()
        self.chat_repo = ChatRepo(session)

    async def chat_stream(
        self,
        session_id: str,
        user_message: str,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """执行 RAG 流程并返回 SSE 事件流"""

        history = await self.chat_repo.get_history(session_id, limit=10)

        yield {"type": "layer_info", "layer": 1, "content": "正在理解您的问题..."}
        analysis = await self.layer1.process(user_message, history)
        logger.info(
            f"查询分析: intent={analysis.intent}, queries={analysis.rewritten_queries}")

        yield {"type": "layer_info", "layer": 2, "content": "正在检索相关职位..."}
        chunks = await self.layer2.retrieve(analysis)
        logger.info(f"检索到 {len(chunks)} 个候选文档")

        yield {"type": "layer_info", "layer": 3, "content": "正在整理最相关结果..."}
        final_chunks = await self.layer3.rerank_and_filter(user_message, chunks)
        logger.info(f"重排后保留 {len(final_chunks)} 个文档")

        yield {"type": "layer_info", "layer": 4, "content": "正在生成回答..."}

        full_response = ""
        async for token in self.layer4.generate_stream(user_message, final_chunks, history):
            full_response += token
            yield {"type": "token", "content": token}

        position_ids = [c.position_id for c in final_chunks]
        sources = [
            {"id": c.position_id, "title": c.position.title}
            for c in final_chunks
        ]
        yield {"type": "sources", "positions": sources}

        await self.chat_repo.create_history(
            session_id=session_id,
            role=MessageRole.USER,
            content=user_message,
        )
        await self.chat_repo.create_history(
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=full_response,
            retrieved_position_ids=position_ids,
        )

        if not history:
            title = user_message[:50] + \
                ("..." if len(user_message) > 50 else "")
            await self.chat_repo.update_session_title(session_id, title)

        yield {"type": "done"}


async def embed_position(session: AsyncSession, position: PositionModel) -> None:
    """为单个职位生成向量块"""
    repo = PositionEmbeddingRepo(session)

    dept_name = position.department.name if position.department else ""
    salary = ""
    if position.min_salary and position.max_salary:
        salary = f"{position.min_salary}k-{position.max_salary}k"

    chunks = []

    if position.title:
        embedding = await embedding_client.embed_text(position.title)
        chunks.append((position.title, embedding, ChunkType.TITLE))

    if position.description:
        embedding = await embedding_client.embed_text(position.description)
        chunks.append((position.description, embedding, ChunkType.DESCRIPTION))

    if position.requirements:
        embedding = await embedding_client.embed_text(position.requirements)
        chunks.append(
            (position.requirements, embedding, ChunkType.REQUIREMENTS))

    full_text = f"""
职位: {position.title}
部门: {dept_name}
薪资: {salary}
学历: {position.education.value if position.education else '不限'}
工作年限: {position.work_year or 0}年以上
描述: {position.description or ''}
要求: {position.requirements or ''}
""".strip()

    embedding = await embedding_client.embed_text(full_text)
    chunks.append((full_text, embedding, ChunkType.FULL))

    await repo.upsert_position_embeddings(position.id, chunks)
    logger.info(f"已为职位 {position.title} 生成 {len(chunks)} 个向量块")
