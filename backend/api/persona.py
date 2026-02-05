"""
Persona API
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Header

from config import settings
from models.schemas import PersonaCreate, PersonaUpdate, PersonaResponse
from services.persona_service import persona_service
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


@router.post("/personas", response_model=PersonaResponse)
async def create_persona(persona_data: PersonaCreate, authorization: Optional[str] = Header(None)):
    """
    创建记忆体
    """
    # 验证API Key
    verify_api_key(authorization)

    try:
        persona = await persona_service.create_persona(persona_data)
        if not persona:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create persona"
            )
        return PersonaResponse.model_validate(persona)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in creating persona: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/personas", response_model=List[PersonaResponse])
async def list_personas(authorization: Optional[str] = Header(None)):
    """
    列出所有记忆体
    """
    # 验证API Key
    verify_api_key(authorization)

    try:
        personas = await persona_service.list_personas()
        return [PersonaResponse.model_validate(p) for p in personas]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in listing personas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/personas/{persona_id}", response_model=PersonaResponse)
async def get_persona(persona_id: str, authorization: Optional[str] = Header(None)):
    """
    获取记忆体详情
    """
    # 验证API Key
    verify_api_key(authorization)

    try:
        persona = await persona_service.get_persona(persona_id)
        if not persona:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Persona not found"
            )
        return PersonaResponse.model_validate(persona)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in getting persona: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/personas/{persona_id}", response_model=PersonaResponse)
async def update_persona(persona_id: str, persona_data: PersonaUpdate, authorization: Optional[str] = Header(None)):
    """
    更新记忆体
    """
    # 验证API Key
    verify_api_key(authorization)

    try:
        persona = await persona_service.update_persona(persona_id, persona_data)
        if not persona:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Persona not found"
            )
        return PersonaResponse.model_validate(persona)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in updating persona: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/personas/{persona_id}")
async def delete_persona(persona_id: str, authorization: Optional[str] = Header(None)):
    """
    删除记忆体
    """
    # 验证API Key
    verify_api_key(authorization)

    try:
        success = await persona_service.delete_persona(persona_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Persona not found"
            )
        return {"message": "Persona deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in deleting persona: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
