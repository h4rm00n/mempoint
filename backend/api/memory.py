"""
Memory Management API
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Header, Query
from pydantic import BaseModel, Field

from config import settings
from models.schemas import MemoryCreate, MemoryUpdate, MemoryResponse, MemorySearchRequest
from services.memory_service import get_memory_service
from utils.logger import logger


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


class MemoryListRequest(BaseModel):
    """记忆列表请求"""
    persona_id: Optional[str] = Field(None, description="记忆体ID，用于过滤")
    type: Optional[str] = Field(None, description="记忆类型，用于过滤")
    limit: int = Field(100, ge=1, le=1000, description="返回数量限制")


@router.post("/memories", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_memory(
    memory_data: MemoryCreate,
    authorization: Optional[str] = Header(None)
):
    """
    创建记忆

    Args:
        memory_data: 记忆创建数据
        authorization: Authorization header，格式为 'Bearer <token>'

    Returns:
        创建的记忆对象
    """
    verify_api_key(authorization)

    try:
        memory_service = get_memory_service()
        memory = await memory_service.create_memory(
            memory_data=memory_data,
            content=memory_data.content,
            event_time=memory_data.event_time
        )

        if not memory:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create memory"
            )

        logger.info(f"Created memory: id={memory.id}, persona_id={memory.persona_id}")
        return MemoryResponse.from_orm(memory)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/memories", response_model=list[MemoryResponse])
async def list_memories(
    persona_id: Optional[str] = Query(None, description="记忆体ID，用于过滤"),
    type: Optional[str] = Query(None, description="记忆类型，用于过滤"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    authorization: Optional[str] = Header(None)
):
    """
    列出记忆

    Args:
        persona_id: 记忆体ID，用于过滤
        type: 记忆类型，用于过滤
        limit: 返回数量限制
        authorization: Authorization header，格式为 'Bearer <token>'

    Returns:
        记忆列表
    """
    verify_api_key(authorization)

    try:
        memory_service = get_memory_service()
        memories = await memory_service.list_memories(
            type=type,
            limit=limit
        )

        # 如果提供了persona_id，在内存中过滤
        if persona_id:
            memories = [m for m in memories if getattr(m, 'persona_id', None) == persona_id]

        logger.debug(f"Listed {len(memories)} memories, persona_id={persona_id}")
        return [MemoryResponse.from_orm(m) for m in memories]

    except Exception as e:
        logger.error(f"Error listing memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/memories/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    获取记忆详情

    Args:
        memory_id: 记忆ID
        authorization: Authorization header，格式为 'Bearer <token>'

    Returns:
        记忆对象
    """
    verify_api_key(authorization)

    try:
        memory_service = get_memory_service()
        memory = await memory_service.get_memory(memory_id)

        if not memory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Memory not found: {memory_id}"
            )

        logger.debug(f"Retrieved memory: id={memory_id}")
        return MemoryResponse.from_orm(memory)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/memories/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memory_id: str,
    memory_data: MemoryUpdate,
    authorization: Optional[str] = Header(None)
):
    """
    更新记忆

    Args:
        memory_id: 记忆ID
        memory_data: 记忆更新数据
        authorization: Authorization header，格式为 'Bearer <token>'

    Returns:
        更新后的记忆对象
    """
    verify_api_key(authorization)

    try:
        memory_service = get_memory_service()
        memory = await memory_service.update_memory(
            memory_id=memory_id,
            memory_data=memory_data
        )

        if not memory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Memory not found: {memory_id}"
            )

        logger.info(f"Updated memory: id={memory_id}")
        return MemoryResponse.from_orm(memory)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/memories/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    删除记忆

    Args:
        memory_id: 记忆ID
        authorization: Authorization header，格式为 'Bearer <token>'

    Returns:
        204 No Content
    """
    verify_api_key(authorization)

    try:
        memory_service = get_memory_service()
        success = await memory_service.delete_memory(memory_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Memory not found: {memory_id}"
            )

        logger.info(f"Deleted memory: id={memory_id}")
        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/memories/search", response_model=list[Dict[str, Any]])
async def search_memories(
    search_request: MemorySearchRequest,
    authorization: Optional[str] = Header(None)
):
    """
    搜索记忆

    Args:
        search_request: 搜索请求
        authorization: Authorization header，格式为 'Bearer <token>'

    Returns:
        搜索结果列表
    """
    verify_api_key(authorization)

    try:
        memory_service = get_memory_service()
        results = await memory_service.search_memories(search_request)

        logger.info(f"Searched memories: query={search_request.query}, found {len(results)} results")
        return results

    except Exception as e:
        logger.error(f"Error searching memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
