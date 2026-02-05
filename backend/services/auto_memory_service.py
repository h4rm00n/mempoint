"""
自动记忆提取服务
在对话结束后自动提取并保存重要记忆
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import BackgroundTasks
import threading

from config import settings
from models.schemas import MemoryCreate
from services.memory_service import get_memory_service
from core.llm_client import memory_extraction_llm_client
from core.embedding_client import embedding_client
from memory.graph_store import graph_store
from memory.vector_store import vector_store
from utils.logger import logger
from utils.helpers import generate_id


class AutoMemoryService:
    """
    自动记忆提取服务
    负责在对话结束后分析对话内容，提取重要信息并保存为记忆
    """

    def __init__(self):
        """初始化自动记忆服务"""
        self.memory_service = get_memory_service()
        # 记忆去重的相似度阈值（从配置中读取）
        self.dedup_similarity_threshold = settings.MEMORY_DEDUP_THRESHOLD
        logger.info(f"AutoMemoryService initialized: dedup_threshold={self.dedup_similarity_threshold}")

    async def _is_duplicate_memory(
        self,
        content: str,
        persona_id: str
    ) -> bool:
        """
        检查是否为重复记忆

        Args:
            content: 记忆内容
            persona_id: 记忆体ID

        Returns:
            是否为重复记忆
        """
        try:
            # 转换为向量
            embedding = await embedding_client.embed(content)

            # 检索相似记忆
            similar_memories = await vector_store.search_knowledge(
                embedding=embedding,
                top_k=5,
                persona_id=persona_id
            )

            # 如果有相似度超过阈值的记忆，认为是重复
            for memory in similar_memories:
                similarity = memory.get('similarity', 0)
                if similarity > self.dedup_similarity_threshold:
                    logger.info(f"Duplicate memory detected: similarity={similarity:.4f}, content='{content[:50]}...'")
                    return True

            return False

        except Exception as e:
            logger.warning(f"Error checking duplicate memory: {e}")
            return False

    async def extract_and_save_memories(
        self,
        messages: List[Dict[str, str]],
        persona_id: str,
        auto_save_enabled: bool = True
    ) -> List[str]:
        """
        从对话中自动提取并保存记忆

        Args:
            messages: 对话消息列表
            persona_id: 记忆体ID
            auto_save_enabled: 是否启用自动保存

        Returns:
            保存的记忆ID列表
        """
        if not auto_save_enabled:
            logger.debug("Auto memory save is disabled")
            return []

        try:
            # 打印开始提取的日志
            logger.info(f"Starting auto memory extraction for persona={persona_id}")

            # 构建提取提示词
            extraction_prompt = self._build_extraction_prompt(messages)

            # 打印提取提示词
            logger.info(f"Memory extraction prompt (persona={persona_id}):\n{extraction_prompt}")

            # 调用LLM提取记忆
            extraction_response = await memory_extraction_llm_client.chat_completion(
                messages=[
                    {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                    {"role": "user", "content": extraction_prompt}
                ],
                temperature=0.3,  # 较低的温度以获得更稳定的提取结果
                max_tokens=500,
                stream=False,
                response_format={"type": "json_object"}
            )

            # 打印LLM原始响应
            logger.info(f"LLM extraction response (persona={persona_id}):")
            logger.info(f"  {extraction_response}")

            # 解析提取结果
            extraction_result = self._parse_extraction_result(
                extraction_response.get("choices", [{}])[0].get("message", {}).get("content", "")
            )

            extracted_memories = extraction_result.get("memories", [])
            extracted_entities = extraction_result.get("entities", [])
            extracted_relations = extraction_result.get("relations", [])

            # 打印提取的记忆
            if extracted_memories:
                logger.info(f"Extracted {len(extracted_memories)} memories from conversation:")
                for i, memory_content in enumerate(extracted_memories, 1):
                    logger.info(f"  {i}. {memory_content.get('content', '')}")

            # 打印提取的实体
            if extracted_entities:
                logger.info(f"Extracted {len(extracted_entities)} entities:")
                for i, entity in enumerate(extracted_entities, 1):
                    logger.info(f"  {i}. {entity.get('name', '')} ({entity.get('type', 'unknown')})")

            # 打印提取的关系
            if extracted_relations:
                logger.info(f"Extracted {len(extracted_relations)} relations:")
                for i, relation in enumerate(extracted_relations, 1):
                    logger.info(f"  {i}. {relation.get('from', '')} --{relation.get('type', '')}--> {relation.get('to', '')}")

            # 保存提取的记忆
            saved_memory_ids = []
            for memory_content in extracted_memories:
                try:
                    content = memory_content.get("content", "")

                    # 检查是否为重复记忆
                    is_duplicate = await self._is_duplicate_memory(content, persona_id)
                    if is_duplicate:
                        logger.info(f"Skipping duplicate memory: {content[:50]}...")
                        continue

                    vector_id = generate_id()

                    # 解析event_time
                    event_time_str = memory_content.get("event_time")
                    event_time = None
                    if event_time_str:
                        try:
                            event_time = datetime.fromisoformat(event_time_str)
                        except ValueError:
                            logger.warning(f"Failed to parse event_time: {event_time_str}")

                    memory_data = MemoryCreate(
                        persona_id=persona_id,
                        vector_id=vector_id,
                        type="long_term",
                        content=content
                    )

                    memory = await self.memory_service.create_memory(
                        memory_data=memory_data,
                        content=content,
                        event_time=event_time  # 传递event_time
                    )

                    if memory:
                        saved_memory_ids.append(memory.id)
                        event_time_str = event_time.isoformat() if event_time else "None"
                        logger.info(f"Auto-saved memory: id={memory.id}, persona_id={persona_id}, event_time={event_time_str}")

                except Exception as e:
                    logger.error(f"Failed to save auto-extracted memory: {e}")

            logger.info(f"Auto-saved {len(saved_memory_ids)} memories from conversation")

            # 创建实体和关系
            if extracted_entities:
                for entity in extracted_entities:
                    try:
                        await graph_store.create_entity(
                            name=entity.get("name", ""),
                            type=entity.get("type", "unknown"),
                            description=f"Auto-extracted entity from conversation"
                        )
                        logger.info(f"Created entity: {entity.get('name', '')}")
                    except Exception as e:
                        logger.error(f"Failed to create entity: {e}")

            if extracted_relations:
                for relation in extracted_relations:
                    try:
                        await graph_store.create_relation(
                            from_entity=relation.get("from", ""),
                            to_entity=relation.get("to", ""),
                            relation_type=relation.get("type", "RELATED_TO"),
                            weight=1.0
                        )
                        logger.info(f"Created relation: {relation.get('from', '')} --{relation.get('type', '')}--> {relation.get('to', '')}")
                    except Exception as e:
                        logger.error(f"Failed to create relation: {e}")

            return saved_memory_ids

        except Exception as e:
            logger.error(f"Error in auto memory extraction: {e}")
            return []

    def _build_extraction_prompt(self, messages: List[Dict[str, str]]) -> str:
        """
        构建记忆提取提示词

        Args:
            messages: 对话消息列表

        Returns:
            提取提示词
        """
        # 提取完整对话（包括用户和助手）
        conversation_lines = []
        for msg in messages[-5:]:  # 最近5条消息（包括用户和助手）
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                conversation_lines.append(f"用户: {content}")
            elif role == "assistant":
                conversation_lines.append(f"助手: {content}")

        conversation_text = "\n".join(conversation_lines)

        # 获取当前时间作为时间锚点
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_date = datetime.now().strftime("%Y-%m-%d")

        # 使用配置中的提示词模板
        prompt = settings.MEMORY_EXTRACTION_PROMPT.format(
            current_time=current_time,
            current_date=current_date,
            conversation_text=conversation_text
        )

        return prompt

    def _parse_extraction_result(self, result: str) -> Dict[str, Any]:
        """
        解析LLM提取结果

        Args:
            result: LLM返回的提取结果

        Returns:
            提取结果字典，包含memories、entities、relations
        """
        import json

        try:
            # 尝试直接解析JSON
            data = json.loads(result)

            # 验证数据结构
            if not isinstance(data, dict):
                raise ValueError("Result is not a dictionary")

            required_keys = ["memories", "entities", "relations"]
            for key in required_keys:
                if key not in data:
                    raise ValueError(f"Missing required key: {key}")
                if not isinstance(data[key], list):
                    raise ValueError(f"Key '{key}' is not a list")

            # 返回解析后的数据
            return {
                "memories": data.get("memories", []),
                "entities": data.get("entities", []),
                "relations": data.get("relations", [])
            }

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            logger.error(f"Raw result: {result[:500]}")
            return {
                "memories": [],
                "entities": [],
                "relations": [],
                "parse_error": str(e)
            }
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {
                "memories": [],
                "entities": [],
                "relations": [],
                "validation_error": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error in _parse_extraction_result: {e}", exc_info=True)
            return {
                "memories": [],
                "entities": [],
                "relations": [],
                "unexpected_error": str(e)
            }

    def close(self):
        """关闭服务"""
        logger.info("AutoMemoryService closed")


# 全局自动记忆服务实例 - 使用懒加载
_auto_memory_service = None
_auto_memory_service_lock = threading.Lock()


def get_auto_memory_service() -> AutoMemoryService:
    """获取自动记忆服务实例（线程安全的懒加载）"""
    global _auto_memory_service
    if _auto_memory_service is None:
        with _auto_memory_service_lock:
            if _auto_memory_service is None:  # 双重检查锁定
                _auto_memory_service = AutoMemoryService()
    return _auto_memory_service


# 向后兼容的属性访问器
class AutoMemoryServiceProxy:
    """自动记忆服务代理类，支持懒加载"""

    def __getattr__(self, name):
        return getattr(get_auto_memory_service(), name)


auto_memory_service = AutoMemoryServiceProxy()
