"""Embedding 生成工具，使用 DashScope text-embedding-v3"""
import httpx
from loguru import logger

from settings import settings


class EmbeddingClient:
    """DashScope Embedding 客户端"""

    def __init__(self):
        self.api_key = settings.DASHSCOPE_API_KEY
        self.model = settings.EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION
        self.batch_size = settings.EMBEDDING_BATCH_SIZE
        self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"

    async def embed_text(self, text: str) -> list[float]:
        """单文本向量化"""
        result = await self.embed_batch([text])  # 调用批量方法，但只传一个文本
        return result[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量文本向量化，自动处理批次大小限制"""
        all_embeddings = []

        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            embeddings = await self._call_api(batch)  # 调用API获取这批的向量
            all_embeddings.extend(embeddings)

        return all_embeddings

    async def _call_api(self, texts: list[str]) -> list[list[float]]:
        """调用 DashScope Embedding API"""
        # 设置请求头
        headers = {
            "Authorization": f"Bearer {self.api_key}", # 认证信息
            "Content-Type": "application/json",  #请求体为JSON
        }
        
        # 设置请求体
        payload = {
            "model": self.model,
            "input": texts,
            "encoding_format": "float",  #返回格式为浮点数列表
        }

        # 使用httpx异步客户端，超时60秒
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.base_url,
                headers=headers,
                json=payload,
            )
            #错误处理
            if response.status_code != 200:
                logger.error(f"Embedding API 调用失败: {response.text}")
                raise ValueError(f"Embedding API 错误: {response.status_code}")
            #解析响应
            data = response.json()

            # 提取向量数据
            # data["data"] 是一个列表，每个元素格式:
            # {
            #   "embedding": [0.123, 0.456, ...],  # 1024维向量
            #   "index": 0
            # }
            embeddings = [item["embedding"] for item in data["data"]]
            return embeddings

# 创建全局单例实例
embedding_client = EmbeddingClient()
