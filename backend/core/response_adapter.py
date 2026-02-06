"""
响应适配器 - 转换API响应格式
"""
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone

from models.schemas import (
    ChatCompletionResponse,
    ChatMessage,
    EmbeddingResponse
)


class ResponseAdapter:
    """
    响应适配器类
    用于转换不同API的响应格式为统一格式
    """
    
    @staticmethod
    def adapt_chat_completion(
        response: Dict[str, Any],
        model: str
    ) -> ChatCompletionResponse:
        """
        适配聊天补全响应

        Args:
            response: 原始API响应
            model: 模型名称

        Returns:
            适配后的响应
        """
        # 提取选择项
        choices = []
        if "choices" in response:
            for choice in response["choices"]:
                message_data = choice.get("message", {})

                # 构建消息对象，支持工具调用
                message_dict = {
                    "role": message_data.get("role", "assistant"),
                    "content": message_data.get("content"),
                    "tool_calls": message_data.get("tool_calls")
                }

                message = ChatMessage(**message_dict)
                choices.append({
                    "index": choice.get("index", 0),
                    "message": message,
                    "finish_reason": choice.get("finish_reason")
                })

        # 提取使用情况
        usage = response.get("usage")

        # 构建响应
        adapted_response = ChatCompletionResponse(
            id=response.get("id", ""),
            created=int(datetime.now(timezone.utc).timestamp()),
            model=model,
            choices=choices,
            usage=usage
        )

        return adapted_response
    
    @staticmethod
    def adapt_embedding(
        response: Dict[str, Any],
        model: str
    ) -> EmbeddingResponse:
        """
        适配嵌入响应
        
        Args:
            response: 原始API响应
            model: 模型名称
        
        Returns:
            适配后的响应
        """
        # 提取数据
        data = []
        if "data" in response:
            for item in response["data"]:
                data.append({
                    "embedding": item.get("embedding", []),
                    "index": item.get("index", 0),
                    "object": item.get("object", "embedding")
                })
        
        # 提取使用情况
        usage = response.get("usage", {})
        
        # 构建响应
        adapted_response = EmbeddingResponse(
            data=data,
            model=model,
            usage=usage
        )
        
        return adapted_response
    
    @staticmethod
    def adapt_models(
        response: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        适配模型列表响应
        
        Args:
            response: 原始API响应
        
        Returns:
            模型列表
        """
        models = []
        if "data" in response:
            for model_data in response["data"]:
                models.append({
                    "id": model_data.get("id", ""),
                    "object": model_data.get("object", "model"),
                    "created": model_data.get("created", 0),
                    "owned_by": model_data.get("owned_by", "")
                })
        
        return models
    
    @staticmethod
    def format_memory_context(
        long_term_memories: List[Dict[str, Any]],
        mode: str = "system"
    ) -> Union[str, List[Dict[str, str]]]:
        """
        格式化记忆上下文

        Args:
            long_term_memories: 长期记忆列表
            mode: 注入模式 ('system', 'messages', 'mixed')

        Returns:
            格式化后的记忆上下文（字符串或消息列表）
        """
        context_parts = []

        # 添加长期记忆
        if long_term_memories:
            context_parts.append("[长期记忆]")
            for i, memory in enumerate(long_term_memories, 1):
                context_parts.append(f"{i}. {memory.get('content', '')}")
            context_parts.append("")

        # 根据模式格式化
        if mode == "system":
            return "\n".join(context_parts)
        elif mode == "messages":
            # 返回消息列表
            messages = []
            for memory in long_term_memories:
                messages.append({
                    "role": "system",
                    "content": memory.get('content', '')
                })
            return messages
        else:  # mixed
            # 混合模式：返回system prompt格式
            return "\n".join(context_parts)
    
    @staticmethod
    def create_system_prompt_with_memory(
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
        if not memory_context:
            return base_prompt
        
        enhanced_prompt = f"""{base_prompt}

以下是相关的背景信息：

{memory_context}

请基于以上信息回答用户的问题。"""
        
        return enhanced_prompt


# 创建全局响应适配器实例
response_adapter = ResponseAdapter()
