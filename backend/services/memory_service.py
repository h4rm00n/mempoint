"""
记忆服务
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from contextlib import contextmanager
import threading

from models.database import SessionLocal, Memory
from models.schemas import MemoryCreate, MemoryUpdate, MemoryResponse, MemorySearchRequest
from memory.vector_store import vector_store
from memory.graph_store import graph_store
from memory.memory_manager import memory_manager, MemoryManager, get_db
from memory.retrieval import retrieval_strategy
from core.embedding_client import embedding_client
from utils.logger import logger
from utils.helpers import generate_id


@contextmanager
def get_memory_manager():
    """获取记忆管理器的上下文管理器"""
    db = SessionLocal()
    try:
        manager = MemoryManager(db=db)
        yield manager
    finally:
        db.close()
        logger.info("MemoryManager context closed")


class MemoryService:
    """
    记忆服务类
    负责管理记忆的CRUD操作
    """

    def __init__(self):
        """初始化记忆服务"""
        self.db = SessionLocal()
        logger.info("MemoryService initialized")
    
    async def create_memory(
        self,
        memory_data: MemoryCreate,
        content: str,
        event_time: Optional[datetime] = None  # 新增参数
    ) -> Optional[Memory]:
        """
        创建记忆（带事务保护和回滚机制）

        Args:
            memory_data: 记忆数据
            content: 原始内容
            event_time: 事件时间（LLM提取）

        Returns:
            创建的记忆对象
        """
        embedding = None
        vector_id = None
        memory = None

        try:
            # 将内容转换为向量
            embedding = await embedding_client.embed(content)

            # 插入向量存储
            vector_id = generate_id()
            success = await vector_store.insert_knowledge(
                id=vector_id,
                persona_id=memory_data.persona_id,
                content=content,
                embedding=embedding,
                entity_id=memory_data.entity_id,
                metadata=memory_data.metadata
            )

            if not success:
                raise Exception("Failed to insert vector")

            # 创建记忆记录（包含event_time）
            memory = await memory_manager.create_memory(
                vector_id=vector_id,
                persona_id=memory_data.persona_id,
                content=content,
                type=memory_data.type,
                entity_id=memory_data.entity_id,
                metadata=memory_data.metadata,
                event_time=event_time  # 新增
            )

            if not memory:
                raise Exception("Failed to create memory record")

            logger.info(f"Created memory: id={memory.id}, type={memory_data.type}, persona_id={memory_data.persona_id}, event_time={event_time}")
            return memory

        except Exception as e:
            # 回滚已执行的操作
            logger.error(f"Failed to create memory, rolling back: {e}")

            # 回滚向量存储
            if vector_id:
                try:
                    await vector_store.delete_vector(vector_id)
                    logger.info(f"Rolled back vector: {vector_id}")
                except Exception as rollback_error:
                    logger.error(f"Failed to rollback vector: {rollback_error}")

            # 回滚图谱数据（如果需要）
            if memory_data.entity_id:
                try:
                    # KùzuDB可能不支持删除，这里需要根据实际情况处理
                    logger.warning(f"Graph data rollback not implemented for entity: {memory_data.entity_id}")
                except Exception as rollback_error:
                    logger.error(f"Failed to rollback graph data: {rollback_error}")

            return None
    
    async def get_memory(self, memory_id: str) -> Optional[Memory]:
        """
        获取记忆
        
        Args:
            memory_id: 记忆ID
        
        Returns:
            记忆对象
        """
        try:
            memory = await memory_manager.get_memory(memory_id)
            return memory
        except Exception as e:
            logger.error(f"Failed to get memory: {e}")
            return None
    
    async def update_memory(
        self,
        memory_id: str,
        memory_data: MemoryUpdate
    ) -> Optional[Memory]:
        """
        更新记忆（带事务保护）

        Args:
            memory_id: 记忆ID
            memory_data: 更新数据

        Returns:
            更新后的记忆对象
        """
        try:
            memory = await memory_manager.get_memory(memory_id)
            if not memory:
                return None

            # 更新内容
            if memory_data.content is not None:
                # 重新计算向量
                embedding = await embedding_client.embed(memory_data.content)

                # 更新向量存储中的向量和内容
                await vector_store.update_vector(
                    id=memory.vector_id,
                    content=memory_data.content,
                    embedding=embedding
                )

                # 更新记忆记录
                memory.content = memory_data.content

            # 更新元数据
            if memory_data.metadata is not None:
                memory.set_metadata(memory_data.metadata)

            # 使用try-finally确保事务正确处理
            try:
                self.db.commit()
                self.db.refresh(memory)
            except Exception as commit_error:
                self.db.rollback()
                raise commit_error

            logger.info(f"Updated memory: id={memory_id}")
            return memory

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update memory: {e}")
            return None
    
    async def delete_memory(self, memory_id: str) -> bool:
        """
        删除记忆（带完整清理）

        Args:
            memory_id: 记忆ID

        Returns:
            是否成功
        """
        try:
            # 获取记忆
            memory = await memory_manager.get_memory(memory_id)
            if not memory:
                return False

            vector_id = memory.vector_id
            entity_id = memory.entity_id

            # 1. 删除向量存储中的数据
            vector_deleted = await vector_store.delete_vector(vector_id)
            if not vector_deleted:
                logger.warning(f"Failed to delete vector: {vector_id}")

            # 2. 删除图谱中的实体和关系（如果存在）
            if entity_id:
                try:
                    # 注意：KùzuDB的删除语法需要根据实际情况调整
                    # 这里假设有delete_entity方法
                    # await graph_store.delete_entity(entity_id)
                    logger.info(f"Would delete graph entity: {entity_id} (not implemented)")
                except Exception as graph_error:
                    logger.warning(f"Failed to delete graph entity: {graph_error}")

            # 3. 删除记忆记录
            success = await memory_manager.delete_memory(memory_id)

            if success:
                logger.info(f"Deleted memory: id={memory_id}")
            else:
                # 如果数据库删除失败，尝试回滚向量删除
                logger.error(f"Failed to delete memory record, attempting rollback")
                try:
                    # 重新插入向量（简化处理）
                    # 实际应用中需要更复杂的恢复逻辑
                    pass
                except Exception as rollback_error:
                    logger.error(f"Rollback failed: {rollback_error}")

            return success

        except Exception as e:
            logger.error(f"Failed to delete memory: {e}")
            return False
    
    async def search_memories(
        self,
        search_request: MemorySearchRequest
    ) -> List[Dict[str, Any]]:
        """
        搜索记忆

        Args:
            search_request: 搜索请求

        Returns:
            搜索结果列表（使用memory_id作为ID）
        """
        try:
            # 将查询转换为向量
            query_embedding = await embedding_client.embed(search_request.query)

            # 使用检索策略搜索
            results = await retrieval_strategy.retrieve(
                query_embedding=query_embedding,
                query_text=search_request.query,
                persona_id=search_request.metadata.get("persona_id") if search_request.metadata else None
            )

            # 更新访问信息（使用memory_id）
            for result in results:
                memory_id = result.get("memory_id")
                if memory_id:
                    await memory_manager.update_memory_access(memory_id)
            
            logger.info(f"Searched memories: query={search_request.query}, found {len(results)} results")

            return results

        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return []
    
    async def list_memories(
        self,
        type: Optional[str] = None,
        limit: int = 100
    ) -> List[Memory]:
        """
        列出记忆
        
        Args:
            type: 记忆类型过滤
            limit: 返回数量限制
        
        Returns:
            记忆列表
        """
        try:
            memories = await memory_manager.list_memories(
                type=type,
                limit=limit
            )
            
            logger.debug(f"Listed {len(memories)} memories")
            return memories
            
        except Exception as e:
            logger.error(f"Failed to list memories: {e}")
            return []
    
    def close(self):
        """关闭数据库连接"""
        self.db.close()
        logger.info("MemoryService closed")


# 全局记忆服务实例 - 使用懒加载
_memory_service = None
_memory_service_lock = threading.Lock()


def get_memory_service() -> MemoryService:
    """获取记忆服务实例（线程安全的懒加载）"""
    global _memory_service
    if _memory_service is None:
        with _memory_service_lock:
            if _memory_service is None:  # 双重检查锁定
                _memory_service = MemoryService()
    return _memory_service


# 向后兼容的属性访问器
class MemoryServiceProxy:
    """记忆服务代理类，支持懒加载"""
    
    def __getattr__(self, name):
        return getattr(get_memory_service(), name)


memory_service = MemoryServiceProxy()
