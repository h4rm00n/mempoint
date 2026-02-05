"""
配置管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from models.database import get_db, Configuration
from models.schemas import (
    ConfigurationCreate,
    ConfigurationResponse,
    ConfigurationUpdate,
    SystemConfigResponse,
    SystemConfigUpdate,
)
from utils.logger import logger
from utils.helpers import generate_id
from config import get_configuration_from_db, update_configuration_in_db


router = APIRouter()


@router.get("/config", response_model=SystemConfigResponse)
async def get_system_config():
    """
    获取系统配置
    """
    try:
        config = SystemConfigResponse(
            llm=get_configuration_from_db("llm") or {},
            embedding=get_configuration_from_db("embedding") or {},
            memory_extraction=get_configuration_from_db("memory_extraction") or {},
            memory_system=get_configuration_from_db("memory_system") or {},
            memory_scoring=get_configuration_from_db("memory_scoring") or {},
            milvus=get_configuration_from_db("milvus") or {},
            kuzu=get_configuration_from_db("kuzu") or {},
            cache=get_configuration_from_db("cache") or {},
        )
        return config
    except Exception as e:
        logger.error(f"Failed to get system config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system config: {str(e)}"
        )


@router.put("/config", response_model=SystemConfigResponse)
async def update_system_config(config_update: SystemConfigUpdate):
    """
    更新系统配置
    """
    try:
        # 更新各个配置
        if config_update.llm is not None:
            update_configuration_in_db("llm", config_update.llm)
        
        if config_update.embedding is not None:
            update_configuration_in_db("embedding", config_update.embedding)
        
        if config_update.memory_extraction is not None:
            update_configuration_in_db("memory_extraction", config_update.memory_extraction)
        
        if config_update.memory_system is not None:
            update_configuration_in_db("memory_system", config_update.memory_system)
        
        if config_update.memory_scoring is not None:
            update_configuration_in_db("memory_scoring", config_update.memory_scoring)
        
        if config_update.milvus is not None:
            update_configuration_in_db("milvus", config_update.milvus)
        
        if config_update.kuzu is not None:
            update_configuration_in_db("kuzu", config_update.kuzu)
        
        if config_update.cache is not None:
            update_configuration_in_db("cache", config_update.cache)
        
        # 返回更新后的配置
        return await get_system_config()
    
    except Exception as e:
        logger.error(f"Failed to update system config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update system config: {str(e)}"
        )


@router.get("/config/{config_key}", response_model=Dict[str, Any])
async def get_config_by_key(config_key: str):
    """
    根据配置键获取配置
    """
    try:
        config_value = get_configuration_from_db(config_key)
        if config_value is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration '{config_key}' not found"
            )
        return config_value
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get config '{config_key}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get config: {str(e)}"
        )


@router.put("/config/{config_key}", response_model=Dict[str, Any])
async def update_config_by_key(config_key: str, config_value: Dict[str, Any]):
    """
    根据配置键更新配置
    """
    try:
        success = update_configuration_in_db(config_key, config_value)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update configuration '{config_key}'"
            )
        return config_value
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update config '{config_key}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update config: {str(e)}"
        )


@router.get("/config/list", response_model=list[ConfigurationResponse])
async def list_configurations(
    user_id: Optional[str] = "system",
    db: Session = Depends(get_db)
):
    """
    列出所有配置
    """
    try:
        query = db.query(Configuration)
        if user_id:
            query = query.filter(Configuration.user_id == user_id)
        
        configs = query.all()
        
        # 解析配置值
        result = []
        for config in configs:
            result.append(ConfigurationResponse(
                id=config.id,
                user_id=config.user_id,
                config_key=config.config_key,
                config_value=config.get_value(),
                description=config.description,
                created_at=config.created_at,
                updated_at=config.updated_at,
            ))
        
        return result
    
    except Exception as e:
        logger.error(f"Failed to list configurations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list configurations: {str(e)}"
        )


@router.post("/config", response_model=ConfigurationResponse, status_code=status.HTTP_201_CREATED)
async def create_configuration(
    config_data: ConfigurationCreate,
    db: Session = Depends(get_db)
):
    """
    创建新配置
    """
    try:
        # 检查配置是否已存在
        existing_config = db.query(Configuration).filter(
            Configuration.user_id == config_data.user_id,
            Configuration.config_key == config_data.config_key
        ).first()
        
        if existing_config:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Configuration '{config_data.config_key}' already exists for user '{config_data.user_id}'"
            )
        
        # 创建新配置
        config = Configuration(
            id=generate_id(),
            user_id=config_data.user_id,
            config_key=config_data.config_key,
            config_value=config_data.config_value,
            description=config_data.description,
        )
        
        db.add(config)
        db.commit()
        db.refresh(config)
        
        logger.info(f"Created configuration: {config_data.config_key} for user {config_data.user_id}")
        
        return ConfigurationResponse(
            id=config.id,
            user_id=config.user_id,
            config_key=config.config_key,
            config_value=config.get_value(),
            description=config.description,
            created_at=config.created_at,
            updated_at=config.updated_at,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create configuration: {str(e)}"
        )


@router.delete("/config/{config_id}")
async def delete_configuration(
    config_id: str,
    db: Session = Depends(get_db)
):
    """
    删除配置
    """
    try:
        config = db.query(Configuration).filter(
            Configuration.id == config_id
        ).first()
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration with id '{config_id}' not found"
            )
        
        db.delete(config)
        db.commit()
        
        logger.info(f"Deleted configuration: {config_id}")
        
        return {"message": "Configuration deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete configuration: {str(e)}"
        )


@router.post("/config/reinitialize")
async def reinitialize_configurations():
    """
    重新初始化配置
    将默认配置重新写入数据库（仅更新不存在的配置）
    """
    try:
        from config import initialize_configurations
        initialize_configurations()
        return {"message": "Configurations reinitialized successfully"}
    except Exception as e:
        logger.error(f"Failed to reinitialize configurations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reinitialize configurations: {str(e)}"
        )
