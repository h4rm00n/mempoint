"""
配置服务
"""
from typing import Dict, Any, Optional
from datetime import datetime

from models.database import SessionLocal, Configuration
from models.schemas import ConfigurationCreate, ConfigurationResponse
from utils.logger import logger
from utils.helpers import generate_id


class ConfigService:
    """
    配置服务类
    负责管理用户配置
    """
    
    def __init__(self):
        """初始化配置服务"""
        self.db = SessionLocal()
        logger.info("ConfigService initialized")
    
    async def create_config(
        self,
        config_data: ConfigurationCreate
    ) -> Optional[Configuration]:
        """
        创建配置
        
        Args:
            config_data: 配置数据
        
        Returns:
            创建的配置对象
        """
        try:
            # 检查配置是否已存在
            existing_config = self.db.query(Configuration).filter(
                Configuration.user_id == config_data.user_id,
                Configuration.config_key == config_data.config_key
            ).first()
            
            if existing_config:
                logger.warning(f"Configuration '{config_data.config_key}' already exists for user '{config_data.user_id}'")
                return None
            
            # 创建新配置
            config = Configuration(
                id=generate_id(),
                user_id=config_data.user_id,
                config_key=config_data.config_key,
                config_value=config_data.config_value,
                description=config_data.description,
            )
            
            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)
            
            logger.info(f"Created config: key={config_data.config_key}, user_id={config_data.user_id}")
            return config
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create config: {e}")
            return None
    
    async def get_config(
        self,
        user_id: str,
        config_key: str
    ) -> Optional[Configuration]:
        """
        获取配置
        
        Args:
            user_id: 用户ID
            config_key: 配置键
        
        Returns:
            配置对象
        """
        try:
            config = self.db.query(Configuration).filter(
                Configuration.user_id == user_id,
                Configuration.config_key == config_key
            ).first()
            
            return config
            
        except Exception as e:
            logger.error(f"Failed to get config: {e}")
            return None
    
    async def update_config(
        self,
        user_id: str,
        config_key: str,
        config_value: Dict[str, Any]
    ) -> Optional[Configuration]:
        """
        更新配置
        
        Args:
            user_id: 用户ID
            config_key: 配置键
            config_value: 配置值
        
        Returns:
            更新后的配置对象
        """
        try:
            config = self.db.query(Configuration).filter(
                Configuration.user_id == user_id,
                Configuration.config_key == config_key
            ).first()
            
            if not config:
                # 创建新配置
                config = Configuration(
                    id=generate_id(),
                    user_id=user_id,
                    config_key=config_key,
                    config_value=config_value,
                )
                self.db.add(config)
            else:
                # 更新现有配置
                config.set_value(config_value)
                config.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(config)
            
            logger.info(f"Updated config: key={config_key}, user_id={user_id}")
            return config
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update config: {e}")
            return None
    
    async def delete_config(
        self,
        user_id: str,
        config_key: str
    ) -> bool:
        """
        删除配置
        
        Args:
            user_id: 用户ID
            config_key: 配置键
        
        Returns:
            是否成功
        """
        try:
            config = self.db.query(Configuration).filter(
                Configuration.user_id == user_id,
                Configuration.config_key == config_key
            ).first()
            
            if not config:
                return False
            
            self.db.delete(config)
            self.db.commit()
            
            logger.info(f"Deleted config: key={config_key}, user_id={user_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete config: {e}")
            return False
    
    async def list_configs(
        self,
        user_id: str
    ) -> list[Configuration]:
        """
        列出用户的所有配置
        
        Args:
            user_id: 用户ID
        
        Returns:
            配置列表
        """
        try:
            configs = self.db.query(Configuration).filter(
                Configuration.user_id == user_id
            ).all()
            
            logger.debug(f"Listed {len(configs)} configs for user {user_id}")
            return configs
            
        except Exception as e:
            logger.error(f"Failed to list configs: {e}")
            return []
    
    def close(self):
        """关闭数据库连接"""
        self.db.close()
        logger.info("ConfigService closed")


# 创建全局配置服务实例
config_service = ConfigService()
