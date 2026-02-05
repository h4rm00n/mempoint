"""
Embedding客户端 - OpenAI风格API
"""
from typing import List, Optional
import httpx

from config import settings
from utils.logger import logger
from utils.cache import cache


class EmbeddingClient:
    """
    Embedding客户端类
    用于调用OpenAI风格的Embedding API
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        """
        初始化Embedding客户端
        
        Args:
            base_url: API基础URL
            api_key: API密钥
            model: 模型名称
            timeout: 超时时间（秒）
        """
        self.base_url = base_url or settings.EMBEDDING_BASE_URL
        self.api_key = api_key or settings.EMBEDDING_API_KEY
        self.model = model or settings.EMBEDDING_MODEL
        self.timeout = timeout or settings.EMBEDDING_TIMEOUT
        
        # 创建HTTP客户端
        self.client = httpx.Client(timeout=self.timeout)
        
        logger.info(f"EmbeddingClient initialized: model={self.model}, base_url={self.base_url}")
    
    async def embed(self, text: str) -> List[float]:
        """
        将文本转换为向量
        
        Args:
            text: 输入文本
        
        Returns:
            向量表示
        """
        # 检查缓存
        cache_key = f"embed:{hash(text)}"
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # 调用API
        try:
            response = self.client.post(
                f"{self.base_url}/embeddings",
                json={
                    "input": text,
                    "model": self.model
                },
                headers=self._get_headers()
            )
            response.raise_for_status()
            
            data = response.json()
            embedding = data["data"][0]["embedding"]
            
            # 缓存结果
            cache.set(cache_key, embedding)
            
            logger.debug(f"Successfully embedded text (length: {len(text)})")
            return embedding
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during embedding: {e}")
            raise
        except Exception as e:
            logger.error(f"Error during embedding: {e}")
            raise
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量将文本转换为向量
        
        Args:
            texts: 输入文本列表
        
        Returns:
            向量表示列表
        """
        # 检查缓存
        results = []
        uncached_texts = []
        uncached_indices = []
        
        for i, text in enumerate(texts):
            cache_key = f"embed:{hash(text)}"
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                results.append((i, cached_result))
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # 调用API获取未缓存的文本的向量
        if uncached_texts:
            try:
                response = self.client.post(
                    f"{self.base_url}/embeddings",
                    json={
                        "input": uncached_texts,
                        "model": self.model
                    },
                    headers=self._get_headers()
                )
                response.raise_for_status()
                
                data = response.json()
                embeddings = [item["embedding"] for item in data["data"]]
                
                # 缓存结果
                for text, embedding in zip(uncached_texts, embeddings):
                    cache_key = f"embed:{hash(text)}"
                    cache.set(cache_key, embedding)
                
                # 合并结果
                for idx, embedding in zip(uncached_indices, embeddings):
                    results.append((idx, embedding))
                
                logger.debug(f"Successfully embedded {len(uncached_texts)} texts")
                
            except httpx.HTTPError as e:
                logger.error(f"HTTP error during batch embedding: {e}")
                raise
            except Exception as e:
                logger.error(f"Error during batch embedding: {e}")
                raise
        
        # 按原始顺序排序
        results.sort(key=lambda x: x[0])
        return [embedding for _, embedding in results]
    
    def _get_headers(self) -> dict:
        """
        获取请求头
        
        Returns:
            请求头字典
        """
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        return headers
    
    def close(self):
        """关闭HTTP客户端"""
        self.client.close()
        logger.info("EmbeddingClient closed")


# 创建全局Embedding客户端实例
embedding_client = EmbeddingClient()
