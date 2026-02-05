"""
记忆体服务
"""
from typing import List, Optional
from datetime import datetime

from models.database import SessionLocal, Persona, Memory
from models.schemas import PersonaCreate, PersonaUpdate, PersonaResponse
from utils.logger import logger
from utils.helpers import generate_id
from memory.vector_store import vector_store


class PersonaService:
    """
    记忆体服务类
    负责管理记忆体的CRUD操作
    """

    def __init__(self):
        """初始化记忆体服务"""
        self.db = SessionLocal()
        logger.info("PersonaService initialized")

    async def create_persona(self, persona_data: PersonaCreate) -> Optional[Persona]:
        """
        创建记忆体

        Args:
            persona_data: 记忆体数据

        Returns:
            创建的记忆体对象
        """
        try:
            persona = Persona(
                id=persona_data.id,
                description=persona_data.description,
                system_prompt=persona_data.system_prompt
            )

            self.db.add(persona)
            self.db.commit()
            self.db.refresh(persona)

            logger.info(f"Created persona: id={persona.id}")
            return persona

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create persona: {e}")
            return None

    async def get_persona(self, persona_id: str) -> Optional[Persona]:
        """
        获取记忆体

        Args:
            persona_id: 记忆体ID

        Returns:
            记忆体对象
        """
        try:
            persona = self.db.query(Persona).filter(Persona.id == persona_id).first()
            return persona
        except Exception as e:
            logger.error(f"Failed to get persona: {e}")
            return None

    async def list_personas(self, limit: int = 100) -> List[Persona]:
        """
        列出所有记忆体

        Args:
            limit: 返回数量限制

        Returns:
            记忆体列表
        """
        try:
            personas = self.db.query(Persona).order_by(
                Persona.updated_at.desc()
            ).limit(limit).all()

            logger.debug(f"Listed {len(personas)} personas")
            return personas

        except Exception as e:
            logger.error(f"Failed to list personas: {e}")
            return []

    async def update_persona(self, persona_id: str, persona_data: PersonaUpdate) -> Optional[Persona]:
        """
        更新记忆体

        Args:
            persona_id: 记忆体ID
            persona_data: 更新数据

        Returns:
            更新后的记忆体对象
        """
        try:
            persona = self.db.query(Persona).filter(Persona.id == persona_id).first()

            if not persona:
                return None

            # 更新字段
            if persona_data.description is not None:
                persona.description = persona_data.description
            if persona_data.system_prompt is not None:
                persona.system_prompt = persona_data.system_prompt

            persona.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(persona)

            logger.info(f"Updated persona: id={persona_id}")
            return persona

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update persona: {e}")
            return None

    async def delete_persona(self, persona_id: str) -> bool:
        """
        删除记忆体（包括相关的记忆和向量）

        Args:
            persona_id: 记忆体ID

        Returns:
            是否成功
        """
        try:
            persona = self.db.query(Persona).filter(Persona.id == persona_id).first()

            if not persona:
                return False

            # 删除相关的记忆和向量
            memories = self.db.query(Memory).filter(Memory.persona_id == persona_id).all()

            for memory in memories:
                # 删除向量存储中的向量
                await vector_store.delete_vector(memory.vector_id)

                # 删除记忆记录
                self.db.delete(memory)

            # 删除人格记录
            self.db.delete(persona)
            self.db.commit()

            logger.info(f"Deleted persona: id={persona_id}, memories={len(memories)}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete persona: {e}")
            return False

    def close(self):
        """关闭数据库连接"""
        self.db.close()
        logger.info("PersonaService closed")


# 全局记忆体服务实例 - 使用懒加载
_persona_service = None


def get_persona_service() -> PersonaService:
    """获取记忆体服务实例（懒加载）"""
    global _persona_service
    if _persona_service is None:
        _persona_service = PersonaService()
    return _persona_service


# 向后兼容的属性访问器
class PersonaServiceProxy:
    """记忆体服务代理类，支持懒加载"""
    
    def __getattr__(self, name):
        return getattr(get_persona_service(), name)


persona_service = PersonaServiceProxy()
