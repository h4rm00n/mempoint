"""
向量存储 - Milvus Lite操作
"""
from typing import List, Dict, Any, Optional
from pymilvus import (
    connections,
    Collection,
    FieldSchema,
    CollectionSchema,
    DataType,
    utility
)
import threading

from config import settings
from utils.logger import logger
from utils.helpers import get_current_timestamp_ms


class VectorStore:
    """
    向量存储类
    使用Milvus Lite进行向量存储和检索
    """
    
    def __init__(self):
        """初始化向量存储"""
        self.milvus_uri = settings.MILVUS_URI
        self.collection_knowledge = None

        # 连接到Milvus
        self._connect()

        # 初始化集合
        self._init_collections()

        logger.info(f"VectorStore initialized: uri={self.milvus_uri}")
    
    def _connect(self):
        """连接到Milvus"""
        try:
            connections.connect(
                alias="default",
                uri=self.milvus_uri
            )
            logger.info("Connected to Milvus Lite")
        except Exception as e:
            logger.error(f"Failed to connect to Milvus Lite: {e}")
            raise
    
    def _init_collections(self):
        """初始化集合"""
        # 创建知识向量集合
        self._create_knowledge_collection()
    
    def _create_knowledge_collection(self):
        """创建知识向量集合"""
        collection_name = settings.MILVUS_COLLECTION_KNOWLEDGE

        # 检查集合是否已存在
        if utility.has_collection(collection_name):
            self.collection_knowledge = Collection(collection_name)
            logger.info(f"Knowledge collection '{collection_name}' already exists")
            return

        # 定义字段
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=64),
            FieldSchema(name="persona_id", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=settings.EMBEDDING_DIMENSIONS),
            FieldSchema(name="entity_id", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="created_at", dtype=DataType.INT64),
            FieldSchema(name="last_accessed_at", dtype=DataType.INT64),
            FieldSchema(name="access_count", dtype=DataType.INT64),
            FieldSchema(name="score", dtype=DataType.FLOAT),
            FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=65535)
        ]

        # 创建schema
        schema = CollectionSchema(
            fields=fields,
            description="Knowledge vectors collection"
        )

        # 创建集合
        self.collection_knowledge = Collection(
            name=collection_name,
            schema=schema
        )

        # 创建索引
        index_params = {
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128}
        }
        self.collection_knowledge.create_index(
            field_name="embedding",
            index_params=index_params
        )

        logger.info(f"Created knowledge collection '{collection_name}'")

    async def insert_knowledge(
        self,
        id: str,
        persona_id: str,
        content: str,
        embedding: List[float],
        entity_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        插入知识向量

        Args:
            id: 向量ID
            persona_id: 记忆体ID
            content: 内容
            embedding: 向量
            entity_id: 实体ID
            metadata: 元数据

        Returns:
            是否成功
        """
        import json

        current_time = get_current_timestamp_ms()

        data = [
            [id],
            [persona_id],
            [content],
            [embedding],
            [entity_id or ""],
            [current_time],
            [current_time],
            [0],
            [0.0],
            [json.dumps(metadata or {})]
        ]

        try:
            self.collection_knowledge.insert(data)
            self.collection_knowledge.flush()
            logger.debug(f"Inserted knowledge vector: id={id}, persona_id={persona_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to insert knowledge vector: {e}")
            return False

    async def search_knowledge(
        self,
        embedding: List[float],
        top_k: int = 10,
        persona_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索知识向量

        Args:
            embedding: 查询向量
            top_k: 返回结果数量
            persona_id: 记忆体ID（可选，用于过滤）

        Returns:
            搜索结果列表
        """
        logger.info(f"[DEBUG] VectorStore.search_knowledge: persona_id='{persona_id}', top_k={top_k}")
        self.collection_knowledge.load()

        search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}

        # 构建过滤表达式
        expr = f"persona_id == '{persona_id}'" if persona_id else None
        logger.info(f"[DEBUG] Search expression: {expr}")

        try:
            results = self.collection_knowledge.search(
                data=[embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                expr=expr,
                output_fields=["id", "persona_id", "content", "entity_id", "created_at", "last_accessed_at", "access_count", "score", "metadata"]
            )

            logger.info(f"[DEBUG] Milvus search returned {len(results)} result groups")
            if len(results) > 0:
                logger.info(f"[DEBUG] First result group has {len(results[0])} hits")

            # 格式化结果
            formatted_results = []
            for result in results[0]:
                entity = result.entity
                logger.info(f"[DEBUG] Processing hit: entity={entity}, score={result.score}")
                formatted_results.append({
                    "id": entity.get("id"),
                    "persona_id": entity.get("persona_id"),
                    "content": entity.get("content"),
                    "entity_id": entity.get("entity_id"),
                    "created_at": entity.get("created_at"),
                    "last_accessed_at": entity.get("last_accessed_at"),
                    "access_count": entity.get("access_count"),
                    "score": entity.get("score"),
                    "metadata": entity.get("metadata"),
                    "similarity": result.score
                })

            logger.info(f"[DEBUG] Formatted {len(formatted_results)} knowledge vectors")
            return formatted_results

        except Exception as e:
            logger.error(f"Failed to search knowledge vectors: {e}")
            return []

    async def update_access(
        self,
        id: str
    ) -> bool:
        """
        更新访问信息

        Args:
            id: 向量ID

        Returns:
            是否成功
        """
        collection = self.collection_knowledge

        try:
            # 获取当前数据
            results = collection.query(
                expr=f"id == '{id}'",
                output_fields=["access_count", "score"]
            )

            if not results:
                return False

            # 更新访问信息
            current_time = get_current_timestamp_ms()
            access_count = results[0].get("access_count", 0) + 1

            collection.update(
                id,
                {
                    "last_accessed_at": current_time,
                    "access_count": access_count
                }
            )

            logger.debug(f"Updated access info: id={id}, access_count={access_count}")
            return True

        except Exception as e:
            logger.error(f"Failed to update access info: {e}")
            return False
    
    async def delete_vector(
        self,
        id: str
    ) -> bool:
        """
        删除向量

        Args:
            id: 向量ID

        Returns:
            是否成功
        """
        collection = self.collection_knowledge

        try:
            # 删除向量
            collection.delete(f"id == '{id}'")
            collection.flush()
            logger.debug(f"Deleted vector: id={id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete vector: {e}")
            return False

    async def update_vector(
        self,
        id: str,
        content: str,
        embedding: List[float]
    ) -> bool:
        """
        更新向量

        Args:
            id: 向量ID
            content: 新内容
            embedding: 新向量

        Returns:
            是否成功
        """
        collection = self.collection_knowledge

        try:
            # 更新向量和内容
            collection.update(
                id,
                {
                    "content": content,
                    "embedding": embedding
                }
            )
            collection.flush()
            logger.debug(f"Updated vector: id={id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update vector: {e}")
            return False

    def close(self):
        """关闭连接"""
        try:
            # 断开连接
            connections.disconnect("default")
            logger.info("Disconnected from Milvus Lite")
        except Exception as e:
            logger.error(f"Error closing vector store: {e}")


# 全局向量存储实例 - 使用懒加载
_vector_store = None
_vector_store_lock = threading.Lock()


def get_vector_store() -> VectorStore:
    """获取向量存储实例（线程安全的懒加载）"""
    global _vector_store
    if _vector_store is None:
        with _vector_store_lock:
            if _vector_store is None:  # 双重检查锁定
                _vector_store = VectorStore()
    return _vector_store


# 向后兼容的属性访问器
class VectorStoreProxy:
    """向量存储代理类，支持懒加载"""
    
    def __getattr__(self, name):
        return getattr(get_vector_store(), name)


vector_store = VectorStoreProxy()
