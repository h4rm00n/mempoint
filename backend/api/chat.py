"""
Chat Completions API
"""
from typing import Dict, Any, Optional
from datetime import datetime
import json
import asyncio
from fastapi import APIRouter, HTTPException, status, Header, BackgroundTasks
from fastapi.responses import StreamingResponse

from config import settings
from models.schemas import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    Tool
)
from core.llm_client import llm_client
from core.embedding_client import embedding_client
from core.memory_engine import memory_engine
from core.response_adapter import response_adapter
from services.auto_memory_service import get_auto_memory_service
from services.persona_service import get_persona_service
from utils.logger import logger
from utils.helpers import generate_id


router = APIRouter()


async def _should_extract_memory_with_context(
    user_message: str,
    assistant_response: str,
    injected_memories: list,
    persona_id: str
) -> bool:
    """
    结合已注入的记忆，判断是否需要提取新记忆

    Args:
        user_message: 用户消息
        assistant_response: 助手响应
        injected_memories: 已注入到system prompt中的记忆
        persona_id: 记忆体ID

    Returns:
        是否需要提取记忆
    """
    # 构建已有记忆的摘要
    memory_summary = ""
    if injected_memories:
        memory_lines = []
        for i, memory in enumerate(injected_memories, 1):
            content = memory.get('content', '')
            event_time = memory.get('event_time')
            time_str = f" ({event_time})" if event_time else ""
            memory_lines.append(f"{i}. {content}{time_str}")
        memory_summary = "\n".join(memory_lines)
    else:
        memory_summary = "（无）"

    # 构建判断提示词
    judgment_prompt = f"""请判断以下最新对话是否包含值得记住的新信息。

【已有记忆】
{memory_summary}

【最新对话】
用户: {user_message}
助手: {assistant_response}

【判断标准】
1. 最新对话中是否包含用户的个人信息（如姓名、电话、邮箱、地址、生日等）
2. 最新对话中是否包含用户的偏好（如喜欢/不喜欢的东西）
3. 最新对话中是否包含用户明确要求记住的信息
4. 最新对话中的信息是否与已有记忆有冲突、补充或更新
5. 最新对话中是否包含对未来对话有帮助的关键信息

【回答格式】
请以JSON格式回答，包含以下字段：
{{
  "should_extract": true/false,
  "reason": "简短说明原因（1-2句话）"
}}

请只返回JSON，不要有其他内容。"""

    # 使用低温度、少token的快速判断
    try:
        response = await llm_client.chat_completion(
            messages=[{"role": "user", "content": judgment_prompt}],
            temperature=0.1,
            max_tokens=100,
            stream=False,
            response_format={"type": "json_object"}
        )

        result_text = response.get("choices", [{}])[0].get("message", {}).get("content", "")

        # 解析JSON结果
        result = json.loads(result_text)
        should_extract = result.get("should_extract", False)
        reason = result.get("reason", "")

        logger.info(f"Memory extraction judgment: should_extract={should_extract}, reason='{reason}'")
        return should_extract

    except Exception as e:
        logger.error(f"Error in memory extraction judgment: {e}")
        # 出错时保守处理，仍然提取
        return True


def verify_api_key(authorization: Optional[str] = Header(None)) -> None:
    """
    验证API Key权限

    Args:
        authorization: 从Authorization header中获取的Bearer token

    Raises:
        HTTPException: 如果API Key验证失败
    """
    if settings.API_KEY:
        # 从 Authorization header 中提取 Bearer token
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid Authorization header. Expected: 'Bearer <token>'"
            )
        token = authorization[7:]  # 移除 "Bearer " 前缀
        if token != settings.API_KEY:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API Key"
            )


@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    request: ChatCompletionRequest,
    background_tasks: BackgroundTasks,
    authorization: Optional[str] = Header(None)
):
    """
    Chat Completions API
    兼容OpenAI风格的聊天补全接口

    model参数格式：persona_id/llm_model（如 "默认助手/deepseek-ai/DeepSeek-V3.2"）
    如果只提供persona_id，则使用默认LLM模型
    """
    # 验证API Key
    verify_api_key(authorization)

    try:
        # 获取用户查询
        user_message = None
        for msg in reversed(request.messages):
            if msg.role == "user":
                user_message = msg.content
                break
        # print(request.messages)  # 注释掉无关的日志
        if not user_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No user message found"
            )

        # 解析model参数：persona_id/llm_model 或 persona_id
        model_param = request.model or settings.DEFAULT_PERSONA_ID
        if "/" in model_param:
            parts = model_param.split("/", 1)
            persona_id = parts[0]
            llm_model = parts[1]
        else:
            persona_id = model_param
            llm_model = settings.LLM_MODEL  # 使用默认LLM模型

        logger.info(f"Chat request: persona_id='{persona_id}', llm_model='{llm_model}'")

        # 获取persona的system_prompt
        persona_service = get_persona_service()
        persona = await persona_service.get_persona(persona_id)
        
        # 检查persona是否存在
        if persona is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Persona '{persona_id}' not found. Please create the persona first or use an existing one."
            )
        
        system_prompt = None
        # 使用 getattr 安全地获取 system_prompt
        prompt_value = getattr(persona, 'system_prompt', None)
        if prompt_value is not None and prompt_value != '':
            system_prompt = str(prompt_value)

        # 检索相关记忆
        memory_config = request.memory_config or {}
        memories = []  # 初始化memories变量
        if memory_config.get("enabled", True):
            # 检索记忆（内部会自动进行向量化）
            logger.info(f"[DEBUG] Starting memory retrieval: query='{user_message}', persona_id='{persona_id}'")
            memories = await memory_engine.retrieve_memories(
                query=user_message,
                persona_id=persona_id
            )
            logger.info(f"[DEBUG] Retrieved {len(memories)} memories from memory_engine")

            # 打印插入的记忆
            if memories:
                logger.info(f"Injected {len(memories)} memories for persona={persona_id}:")
                for i, memory in enumerate(memories, 1):
                    event_time = memory.get('event_time')
                    time_str = f" [event_time: {event_time}]" if event_time else ""
                    logger.info(f"  {i}. {memory.get('content', '')}{time_str}")

            # 将记忆注入到消息中
            logger.info(f"[DEBUG] Injecting memories into messages")
            enhanced_messages = memory_engine.inject_memory(
                [msg.dict() for msg in request.messages],
                memories
            )
            logger.info(f"[DEBUG] Enhanced messages count: {len(enhanced_messages)}")
        else:
            enhanced_messages = [msg.dict() for msg in request.messages]

        # 注入persona的system_prompt（如果有）
        if system_prompt:
            # 查找是否已有system消息
            has_system = False
            for msg in enhanced_messages:
                if msg.get("role") == "system":
                    logger.info(f"[DEBUG] Found existing system message, appending persona prompt")
                    # 追加到现有的system消息，而不是覆盖
                    # 保留下游程序提供的系统提示词
                    msg["content"] = f"{msg['content']}\n\n{system_prompt}"
                    has_system = True
                    break

            # 如果没有system消息，插入一条
            if not has_system:
                logger.info(f"[DEBUG] No system message found, inserting new one")
                enhanced_messages.insert(0, {
                    "role": "system",
                    "content": system_prompt
                })

            # 打印注入的系统提示词
            logger.info(f"Injected system prompt for persona={persona_id}: {system_prompt}")

        # 打印发送给LLM的消息
        logger.info(f"[DEBUG] Sending messages to LLM (persona={persona_id}):")
        for i, msg in enumerate(enhanced_messages, 1):
            role = msg.get("role", "")
            content = msg.get("content", "")
            # 对于system消息，打印完整内容（不截断）
            if role == "system":
                logger.info(f"  {i}. [{role}] (full content):\n{content}")
            else:
                # 截断过长的内容
                if len(content) > 200:
                    content = content[:200] + "..."
                logger.info(f"  {i}. [{role}] {content}")

        # 调用LLM API
        if request.stream:
            # 流式响应
            logger.info(f"Using streaming mode (persona={persona_id}, llm_model={llm_model})")
            # 流式响应也会触发自动记忆提取
            return StreamingResponse(
                _stream_chat_completion(
                    messages=enhanced_messages,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    tools=[tool.dict() for tool in request.tools] if request.tools else None,
                    tool_choice=request.tool_choice,
                    original_messages=[msg.dict() for msg in request.messages],
                    persona_id=persona_id,
                    llm_model=llm_model,
                    memory_config=memory_config,
                    user_message=user_message,
                    injected_memories=memories,
                    **request.model_dump(exclude={'model', 'messages', 'temperature', 'max_tokens', 'stream', 'tools', 'tool_choice', 'memory_config'})  # 透传额外参数
                ),
                media_type="text/event-stream"
            )
        else:
            # 非流式响应
            response_data = await llm_client.chat_completion(
                messages=enhanced_messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=False,
                tools=[tool.dict() for tool in request.tools] if request.tools else None,
                tool_choice=request.tool_choice,
                model=llm_model,  # 使用解析出的LLM模型
                **request.model_dump(exclude={'model', 'messages', 'temperature', 'max_tokens', 'stream', 'tools', 'tool_choice', 'memory_config'})  # 透传额外参数
            )

            # 打印LLM原始响应
            logger.info(f"LLM raw response (persona={persona_id}):")
            logger.info(f"  {json.dumps(response_data, ensure_ascii=False, indent=2)}")

            # 适配响应格式
            adapted_response = response_adapter.adapt_chat_completion(
                response_data,
                llm_model  # 使用解析出的LLM模型
            )

            # 打印适配后的响应
            logger.info(f"Adapted response (persona={persona_id}):")
            logger.info(f"  {json.dumps(adapted_response.dict(), ensure_ascii=False, indent=2)}")

            # 提取助手响应内容
            assistant_response = ""
            if "choices" in response_data and len(response_data["choices"]) > 0:
                assistant_response = response_data["choices"][0].get("message", {}).get("content", "")

            # 判断是否需要提取记忆
            auto_save_enabled = memory_config.get("auto_save", True)
            if auto_save_enabled:
                logger.info(f"Checking if memory extraction is needed (persona={persona_id})")

                # 使用已注入的记忆进行判断
                should_extract = await _should_extract_memory_with_context(
                    user_message=user_message,
                    assistant_response=assistant_response,
                    injected_memories=memories,
                    persona_id=persona_id
                )

                if should_extract:
                    logger.info(f"Scheduling memory extraction for persona={persona_id}")
                    auto_memory_service = get_auto_memory_service()
                    background_tasks.add_task(
                        auto_memory_service.extract_and_save_memories,
                        [msg.dict() for msg in request.messages],
                        persona_id,
                        auto_save_enabled
                    )
                    logger.info(f"Auto memory extraction task scheduled (persona={persona_id})")
                else:
                    logger.info(f"Skipping memory extraction (no new information) for persona={persona_id}")
            else:
                logger.info(f"Auto memory extraction disabled (persona={persona_id})")

            logger.info(f"Chat completion successful: persona={persona_id}")
            return adapted_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat completion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


async def _stream_chat_completion(
    messages: list,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    tools: Optional[list] = None,
    tool_choice: Optional[Any] = None,
    original_messages: Optional[list] = None,
    persona_id: Optional[str] = None,
    llm_model: Optional[str] = None,
    memory_config: Optional[Dict[str, Any]] = None,
    user_message: Optional[str] = None,
    injected_memories: Optional[list] = None,
    **kwargs  # 支持传递其他参数（如top_k, thinking等）
):
    """
    流式聊天补全

    Args:
        messages: 消息列表
        temperature: 温度参数
        max_tokens: 最大token数
        tools: 工具列表
        tool_choice: 工具选择策略
        original_messages: 原始消息列表（用于记忆提取）
        persona_id: 记忆体ID（用于记忆提取）
        llm_model: LLM模型名称
        memory_config: 记忆配置（用于记忆提取）
        user_message: 用户消息（用于记忆提取判断）
        injected_memories: 已注入的记忆（用于记忆提取判断）
        **kwargs: 其他参数（如top_k, thinking等）

    Yields:
        流式响应的文本片段
    """
    assistant_response = ""
    finish_reason = None
    try:
        async for chunk in llm_client.chat_completion_stream(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            tool_choice=tool_choice,
            model=llm_model,
            **kwargs
        ):
            # 直接返回原始chunk数据，保持工具调用信息
            yield f"data: {json.dumps(chunk)}\n\n"
            # 收集响应内容和finish_reason
            if "choices" in chunk and len(chunk["choices"]) > 0:
                choice = chunk["choices"][0]
                delta = choice.get("delta", {})
                if "content" in delta and delta["content"] is not None:
                    assistant_response += delta["content"]
                # 记录finish_reason
                if "finish_reason" in choice and choice["finish_reason"] is not None:
                    finish_reason = choice["finish_reason"]
                    logger.info(f"Stream chunk with finish_reason: {finish_reason}")

        # 发送结束标记
        yield "data: [DONE]\n\n"

        # 只有在finish_reason为"stop"（正常结束）时才触发记忆提取
        # 如果finish_reason是"tool_calls"，说明还有工具调用需要处理，不应该提取记忆
        if original_messages and persona_id and finish_reason == "stop":
            auto_save_enabled = memory_config.get("auto_save", True) if memory_config else True
            if auto_save_enabled:
                logger.info(f"Stream completed with finish_reason=stop, checking if memory extraction is needed (persona={persona_id})")
                # 使用asyncio.create_task异步执行记忆提取判断和提取，不阻塞响应
                asyncio.create_task(
                    _extract_memory_after_stream(
                        original_messages=original_messages,
                        persona_id=persona_id,
                        auto_save_enabled=auto_save_enabled,
                        user_message=user_message,
                        assistant_response=assistant_response,
                        injected_memories=injected_memories
                    )
                )
        elif finish_reason and finish_reason != "stop":
            logger.info(f"Stream completed with finish_reason={finish_reason}, skipping memory extraction (tool calls in progress)")

    except Exception as e:
        logger.error(f"Error in streaming chat completion: {e}")
        raise


async def _extract_memory_after_stream(
    original_messages: list,
    persona_id: str,
    auto_save_enabled: bool,
    user_message: Optional[str] = None,
    assistant_response: Optional[str] = None,
    injected_memories: Optional[list] = None
):
    """
    流式响应完成后提取记忆

    Args:
        original_messages: 原始消息列表
        persona_id: 记忆体ID
        auto_save_enabled: 是否启用自动保存
        user_message: 用户消息（用于记忆提取判断）
        assistant_response: 助手响应（用于记忆提取判断）
        injected_memories: 已注入的记忆（用于记忆提取判断）
    """
    try:
        # 判断是否需要提取记忆
        if user_message and assistant_response is not None:
            should_extract = await _should_extract_memory_with_context(
                user_message=user_message,
                assistant_response=assistant_response,
                injected_memories=injected_memories or [],
                persona_id=persona_id
            )

            if should_extract:
                logger.info(f"Extracting memory after stream (persona={persona_id})")
                auto_memory_service = get_auto_memory_service()
                await auto_memory_service.extract_and_save_memories(
                    messages=original_messages,
                    persona_id=persona_id,
                    auto_save_enabled=auto_save_enabled
                )
            else:
                logger.info(f"Skipping memory extraction after stream (no new information) for persona={persona_id}")
        else:
            # 如果没有用户消息或助手响应，保守处理，仍然提取
            logger.info(f"Missing user_message or assistant_response, extracting memory (persona={persona_id})")
            auto_memory_service = get_auto_memory_service()
            await auto_memory_service.extract_and_save_memories(
                messages=original_messages,
                persona_id=persona_id,
                auto_save_enabled=auto_save_enabled
            )
    except Exception as e:
        logger.error(f"Error in post-stream memory extraction: {e}")
