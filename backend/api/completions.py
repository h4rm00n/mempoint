"""
Completions API
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status

from models.schemas import ChatCompletionResponse
from core.llm_client import llm_client
from core.response_adapter import response_adapter
from utils.logger import logger


router = APIRouter()


@router.post("/completions", response_model=ChatCompletionResponse)
async def completions(
    prompt: str,
    model: str,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    stream: Optional[bool] = False
):
    """
    Completions API
    兼容OpenAI风格的文本补全接口
    """
    try:
        # 调用LLM API
        response_data = await llm_client.completion(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )
        
        # 适配响应格式
        adapted_response = response_adapter.adapt_chat_completion(
            response_data,
            model
        )
        
        logger.info(f"Completion successful: model={model}")
        return adapted_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in completion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
