"""
记忆注入引擎
"""
from typing import List, Dict, Any, Optional
from datetime import datetime

from config import settings
from utils.logger import logger
from utils.helpers import calculate_similarity_score, get_current_timestamp_ms
from memory.retrieval import retrieval_strategy
from core.embedding_client import embedding_client


class MemoryEngine:
    """
    记忆注入引擎
    负责从记忆系统中检索相关记忆并注入到LLM请求中
    """
    
    def __init__(self):
        """初始化记忆注入引擎"""
        self.enabled = settings.MEMORY_ENABLED
        self.max_long_term = settings.MEMORY_MAX_LONG_TERM
        self.injection_mode = settings.MEMORY_INJECTION_MODE
        
        # 评分权重
        self.similarity_weight = settings.MEMORY_SCORE_SIMILARITY_WEIGHT
        self.access_weight = settings.MEMORY_SCORE_ACCESS_WEIGHT
        self.recency_weight = settings.MEMORY_SCORE_RECENCY_WEIGHT
        self.graph_weight = settings.MEMORY_SCORE_GRAPH_WEIGHT
        self.lambda_decay = settings.MEMORY_RECENCY_DECAY_LAMBDA
        
        logger.info(f"MemoryEngine initialized: enabled={self.enabled}, mode={self.injection_mode}")
    
    async def retrieve_memories(
        self,
        query: str,
        persona_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        检索相关记忆

        Args:
            query: 查询文本
            persona_id: 记忆体ID（用于长期记忆过滤）

        Returns:
            长期记忆列表
        """
        if not self.enabled:
            logger.debug("Memory is disabled, skipping retrieval")
            return []

        try:
            logger.info(f"[DEBUG] MemoryEngine.retrieve_memories: query='{query}', persona_id='{persona_id}'")
            # 将查询文本转换为向量
            query_embedding = await embedding_client.embed(query)
            logger.info(f"[DEBUG] Query embedding created, dimension: {len(query_embedding)}")

            # 调用检索策略获取记忆
            memories = await retrieval_strategy.retrieve(
                query_embedding=query_embedding,
                query_text=query,
                persona_id=persona_id
            )

            logger.info(f"[DEBUG] MemoryEngine retrieved {len(memories)} long-term memories")
            for i, mem in enumerate(memories[:3]):
                logger.info(f"[DEBUG]   Memory {i+1}: id={mem.get('id')}, content={mem.get('content', '')[:50]}...")

            return memories

        except Exception as e:
            logger.error(f"Failed to retrieve memories: {e}")
            return []
    
    def calculate_memory_score(
        self,
        memory: Dict[str, Any],
        similarity: float,
        graph_score: float = 0.0
    ) -> float:
        """
        计算记忆的综合评分
        
        Args:
            memory: 记忆数据
            similarity: 相似度评分
            graph_score: 图谱评分
        
        Returns:
            综合评分
        """
        access_count = memory.get("access_count", 0)
        last_accessed_at = memory.get("last_accessed_at", get_current_timestamp_ms())
        created_at = memory.get("created_at", get_current_timestamp_ms())
        
        # 计算评分
        score = calculate_similarity_score(
            similarity=similarity,
            access_count=access_count,
            max_access_count=100,  # 假设最大访问次数为100
            last_accessed_at=last_accessed_at,
            created_at=created_at,
            lambda_decay=self.lambda_decay,
            graph_score=graph_score
        )
        
        return score
    
    def inject_memory(
        self,
        messages: List[Dict[str, str]],
        memories: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """
        将记忆注入到消息列表中

        Args:
            messages: 原始消息列表
            memories: 长期记忆列表

        Returns:
            增强后的消息列表
        """
        logger.info(f"[DEBUG] inject_memory: enabled={self.enabled}, memories_count={len(memories)}")
        if not self.enabled:
            return messages

        if not memories:
            logger.info("[DEBUG] No memories to inject")
            return messages

        # 限制记忆数量
        long_term_memories = memories[:self.max_long_term]
        logger.info(f"[DEBUG] Limited to {len(long_term_memories)} memories (max={self.max_long_term})")

        # 根据注入模式处理
        if self.injection_mode == "system":
            # System Prompt注入模式
            logger.info("[DEBUG] Using system injection mode")
            return self._inject_to_system(messages, long_term_memories)
        elif self.injection_mode == "messages":
            # Messages注入模式
            logger.info("[DEBUG] Using messages injection mode")
            return self._inject_to_messages(messages, long_term_memories)
        else:  # mixed
            # 混合模式（等同于system模式，因为已移除短期记忆）
            logger.info("[DEBUG] Using mixed injection mode (same as system)")
            return self._inject_to_system(messages, long_term_memories)
    
    def _inject_to_system(
        self,
        messages: List[Dict[str, str]],
        long_term_memories: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """
        将记忆注入到system prompt中

        Args:
            messages: 原始消息列表
            long_term_memories: 长期记忆列表

        Returns:
            增强后的消息列表
        """
        logger.info(f"[DEBUG] _inject_to_system: messages_count={len(messages)}, memories_count={len(long_term_memories)}")
        # 构建记忆上下文
        memory_context = self._format_memory_context(long_term_memories)
        logger.info(f"[DEBUG] Memory context created: {memory_context[:100] if memory_context else 'None'}...")

        # 打印注入的记忆上下文
        if memory_context:
            logger.info(f"Memory context injected into system prompt:\n{memory_context}")

        # 查找或创建system消息
        system_message = None
        for msg in messages:
            if msg.get("role") == "system":
                system_message = msg
                break

        if system_message:
            # 更新现有的system消息
            original_content = system_message["content"]
            enhanced_content = self._create_system_prompt_with_memory(
                original_content,
                memory_context
            )
            system_message["content"] = enhanced_content
            logger.info(f"[DEBUG] Enhanced existing system message")

            # 打印增强后的system prompt
            logger.info(f"Enhanced system prompt (original length: {len(original_content)}, enhanced length: {len(enhanced_content)})")
        else:
            # 创建新的system消息
            enhanced_content = self._create_system_prompt_with_memory(
                "你是一个智能助手。",
                memory_context
            )
            system_message = {
                "role": "system",
                "content": enhanced_content
            }
            messages.insert(0, system_message)
            logger.info(f"[DEBUG] Created new system message")

            # 打印创建的system prompt
            logger.info(f"Created system prompt with memory context (length: {len(enhanced_content)})")

        return messages
    
    def _inject_to_messages(
        self,
        messages: List[Dict[str, str]],
        long_term_memories: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """
        将记忆作为消息注入
        
        Args:
            messages: 原始消息列表
            long_term_memories: 长期记忆列表
        
        Returns:
            增强后的消息列表
        """
        # 将记忆转换为消息格式
        memory_messages = []
        for memory in long_term_memories:
            memory_messages.append({
                "role": "system",
                "content": f"[记忆] {memory.get('content', '')}"
            })
        
        # 将记忆消息插入到第一条消息之前
        return memory_messages + messages
    
    
    def _format_memory_context(
        self,
        long_term_memories: List[Dict[str, Any]]
    ) -> str:
        """
        格式化记忆上下文

        Args:
            long_term_memories: 长期记忆列表

        Returns:
            格式化后的记忆上下文（XML格式）
        """
        logger.info(f"[DEBUG] _format_memory_context: received {len(long_term_memories)} memories")
        
        if not long_term_memories:
            logger.info("[DEBUG] No long_term_memories to format")
            return ""

        # 构建XML格式的记忆上下文
        xml_parts = ["<memory_context>"]
        xml_parts.append("  <related_knowledge>")
        
        for i, memory in enumerate(long_term_memories, 1):
            content = memory.get('content', '')
            event_time = memory.get('event_time')
            logger.info(f"[DEBUG] Formatting memory {i}: content='{content[:50]}...', event_time={event_time}")
            
            # 转义XML特殊字符
            content_escaped = self._escape_xml(content)
            
            # 如果有event_time，格式化时间信息
            if event_time:
                # 尝试解析ISO格式并格式化显示
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(event_time)
                    time_str = dt.strftime('%Y-%m-%d %H:%M')
                    xml_parts.append(f"    <memory index=\"{i}\">")
                    xml_parts.append(f"      <content>{content_escaped}</content>")
                    xml_parts.append(f"      <event_time>{time_str}</event_time>")
                    xml_parts.append(f"    </memory>")
                except:
                    # 解析失败，直接显示原始字符串
                    xml_parts.append(f"    <memory index=\"{i}\">")
                    xml_parts.append(f"      <content>{content_escaped}</content>")
                    xml_parts.append(f"      <event_time>{event_time}</event_time>")
                    xml_parts.append(f"    </memory>")
            else:
                xml_parts.append(f"    <memory index=\"{i}\">")
                xml_parts.append(f"      <content>{content_escaped}</content>")
                xml_parts.append(f"    </memory>")
        
        xml_parts.append("  </related_knowledge>")
        xml_parts.append("</memory_context>")
        
        result = "\n".join(xml_parts)
        logger.info(f"[DEBUG] Formatted memory context:\n{result}")
        return result
    
    def _escape_xml(self, text: str) -> str:
        """
        转义XML特殊字符

        Args:
            text: 原始文本

        Returns:
            转义后的文本
        """
        if not text:
            return text
        # 转义XML特殊字符
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        text = text.replace('"', "&quot;")
        text = text.replace("'", "&apos;")
        return text
    
    def _create_system_prompt_with_memory(
        self,
        base_prompt: str,
        memory_context: str
    ) -> str:
        """
        创建带有记忆的system prompt

        Args:
            base_prompt: 基础system prompt
            memory_context: 记忆上下文

        Returns:
            增强的system prompt
        """
        logger.info(f"[DEBUG] _create_system_prompt_with_memory: base_prompt_len={len(base_prompt)}, memory_context_len={len(memory_context) if memory_context else 0}")
        if not memory_context:
            logger.info("[DEBUG] No memory context, returning base prompt")
            return base_prompt

        enhanced_prompt = f"""{base_prompt}

以下是相关的背景信息：

{memory_context}

请基于以上信息回答用户的问题。"""

        logger.info(f"[DEBUG] Enhanced prompt length: {len(enhanced_prompt)}")
        return enhanced_prompt


# 创建全局记忆注入引擎实例
memory_engine = MemoryEngine()
