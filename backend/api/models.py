"""
Models API
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status, Header

from config import settings
from models.database import SessionLocal, Persona
from models.schemas import PersonaResponse
from core.llm_client import llm_client
from core.embedding_client import embedding_client
from core.response_adapter import response_adapter
from utils.logger import logger
from utils.memory_tools import get_memory_tools


router = APIRouter()


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


@router.get("/models")
async def list_models(authorization: Optional[str] = Header(None)):
    """
    Models API
    返回所有可用的模型（记忆体与LLM模型的组合）
    格式：persona_id/llm_model
    """
    # 验证API Key
    verify_api_key(authorization)

    try:
        db = SessionLocal()
        try:
            # 获取所有记忆体
            personas = db.query(Persona).all()

            # 从LLM供应商获取模型列表
            llm_models = []
            try:
                llm_models = await llm_client.list_models()
                logger.info(f"Retrieved {len(llm_models)} models from LLM provider")
            except Exception as e:
                logger.warning(f"Failed to retrieve models from LLM provider: {e}")
                # 如果无法获取LLM模型列表，使用默认模型
                llm_models = [{
                    "id": settings.LLM_MODEL,
                    "object": "model",
                    "created": int(datetime.now(timezone.utc).timestamp()),
                    "owned_by": "llm_provider"
                }]

            # 将记忆体与LLM模型组合
            model_list = []
            for persona in personas:
                for llm_model in llm_models:
                    model_id = f"{persona.id}/{llm_model['id']}"
                    model_list.append({
                        "id": model_id,
                        "object": "model",
                        "created": int(persona.created_at.timestamp()),
                        "owned_by": "you"
                    })

            logger.info(f"Listed {len(model_list)} combined models ({len(personas)} personas × {len(llm_models)} LLM models)")
            return {
                "object": "list",
                "data": model_list
            }

        finally:
            db.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in listing models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/memory-tools")
async def get_memory_tools_endpoint(authorization: Optional[str] = Header(None)):
    """
    Memory Tools API
    返回所有可用的记忆管理工具定义
    这些工具可以传递给 LLM 的 tools 参数，让 LLM 主动调用
    """
    # 验证API Key
    verify_api_key(authorization)

    try:
        tools = get_memory_tools()
        logger.info(f"Returned {len(tools)} memory tools")
        return {
            "object": "list",
            "data": tools
        }

    except Exception as e:
        logger.error(f"Error getting memory tools: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
