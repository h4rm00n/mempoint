"""
记忆管理器
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from contextlib import contextmanager
import threading

from config import settings
from utils.logger import logger
from utils.helpers import generate_id, get_current_timestamp_ms
from models.database import SessionLocal, Memory


@contextmanager
def get_db():
    """数据库会话上下文管理器"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class MemoryManager:
    """
    记忆管理器
    负责管理记忆的生命周期
    """

    def __init__(self, db=None):
        """初始化记忆管理器"""
        self.db = db if db is not None else SessionLocal()
        self._external_db = db is not None
        logger.info("MemoryManager initialized")
    
    async def create_memory(
        self,
        vector_id: str,
        persona_id: str,
        content: str,
        type: str,
        entity_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        event_time: Optional[datetime] = None  # 新增参数
    ) -> Optional[Memory]:
        """
        创建记忆

        Args:
            vector_id: 向量ID
            persona_id: 记忆体ID
            content: 内容
            type: 记忆类型 ('long_term')
            entity_id: 实体ID
            metadata: 元数据
            event_time: 事件时间（LLM提取）

        Returns:
            创建的记忆对象
        """
        try:
            memory = Memory(
                id=generate_id(),
                persona_id=persona_id,
                vector_id=vector_id,
                entity_id=entity_id,
                type=type,
                content=content,
                created_at=datetime.utcnow(),
                event_time=event_time,  # 新增
                last_accessed_at=datetime.utcnow(),
                access_count=0,
                score=0.0
            )

            if metadata:
                memory.set_metadata(metadata)

            self.db.add(memory)
            self.db.commit()
            self.db.refresh(memory)

            logger.debug(f"Created memory: id={memory.id}, type={type}, persona_id={persona_id}")
            return memory

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create memory: {e}")
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
            memory = self.db.query(Memory).filter(Memory.id == memory_id).first()
            return memory
        except Exception as e:
            logger.error(f"Failed to get memory: {e}")
            return None
    
    async def update_memory_access(self, memory_id: str) -> bool:
        """
        更新记忆的访问信息
        
        Args:
            memory_id: 记忆ID
        
        Returns:
            是否成功
        """
        try:
            memory = self.db.query(Memory).filter(Memory.id == memory_id).first()
            if not memory:
                return False
            
            memory.last_accessed_at = datetime.utcnow()
            memory.access_count += 1
            
            self.db.commit()
            
            logger.debug(f"Updated memory access: id={memory_id}, count={memory.access_count}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update memory access: {e}")
            return False
    
    async def update_memory_score(self, memory_id: str, score: float) -> bool:
        """
        更新记忆的评分
        
        Args:
            memory_id: 记忆ID
            score: 新的评分
        
        Returns:
            是否成功
        """
        try:
            memory = self.db.query(Memory).filter(Memory.id == memory_id).first()
            if not memory:
                return False
            
            memory.score = score
            self.db.commit()
            
            logger.debug(f"Updated memory score: id={memory_id}, score={score}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update memory score: {e}")
            return False
    
    async def delete_memory(self, memory_id: str) -> bool:
        """
        删除记忆
        
        Args:
            memory_id: 记忆ID
        
        Returns:
            是否成功
        """
        try:
            memory = self.db.query(Memory).filter(Memory.id == memory_id).first()
            if not memory:
                return False
            
            self.db.delete(memory)
            self.db.commit()
            
            logger.debug(f"Deleted memory: id={memory_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete memory: {e}")
            return False
    
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
            query = self.db.query(Memory)
            
            if type:
                query = query.filter(Memory.type == type)
            
            memories = query.order_by(Memory.created_at.desc()).limit(limit).all()
            
            logger.debug(f"Listed {len(memories)} memories")
            return memories
            
        except Exception as e:
            logger.error(f"Failed to list memories: {e}")
            return []
    
    async def search_memories(
        self,
        query: str,
        type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        搜索记忆
        
        Args:
            query: 搜索查询
            type: 记忆类型过滤
            limit: 返回数量限制
        
        Returns:
            搜索结果列表
        """
        try:
            # 这里应该调用向量存储进行搜索
            # 由于向量存储还没有完全实现，这里先返回空列表
            # TODO: 实现实际的记忆搜索逻辑
            
            logger.debug(f"Search memories: query={query}, type={type}")
            return []
            
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return []
    
    def close(self):
        """关闭数据库连接"""
        # 只关闭内部创建的数据库连接
        if not self._external_db:
            self.db.close()
            logger.info("MemoryManager closed")


# 全局记忆管理器实例 - 使用懒加载
_memory_manager = None
_memory_manager_lock = threading.Lock()


def get_memory_manager() -> MemoryManager:
    """获取记忆管理器实例（线程安全的懒加载）"""
    global _memory_manager
    if _memory_manager is None:
        with _memory_manager_lock:
            if _memory_manager is None:  # 双重检查锁定
                _memory_manager = MemoryManager()
    return _memory_manager


# 向后兼容的属性访问器
class MemoryManagerProxy:
    """记忆管理器代理类，支持懒加载"""
    
    def __getattr__(self, name):
        return getattr(get_memory_manager(), name)


memory_manager = MemoryManagerProxy()
