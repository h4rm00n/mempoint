"""
数据库模型定义 - SQLite
"""
from sqlalchemy import create_engine, Column, String, Integer, Float, Text, DateTime, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
import json

from config import settings

# 创建数据库引擎
engine = create_engine(
    f"sqlite:///{settings.SQLITE_DB_PATH}",
    connect_args={"check_same_thread": False}
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()


class Persona(Base):
    """记忆体表 - 独立的记忆空间"""
    __tablename__ = "personas"

    id = Column(String, primary_key=True, index=True)  # 记忆体ID/名称
    description = Column(String, nullable=True)  # 记忆体描述
    system_prompt = Column(Text, nullable=True)  # 记忆体专属的system prompt
    created_at = Column(DateTime, default=lambda: datetime.now())  # 使用本地时间（北京时间）
    updated_at = Column(DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())  # 使用本地时间（北京时间）


class Memory(Base):
    """记忆表 - 用于追踪记忆的元数据"""
    __tablename__ = "memories"

    id = Column(String, primary_key=True, index=True)
    persona_id = Column(String, ForeignKey("personas.id"), nullable=False, index=True)  # 关联到记忆体
    vector_id = Column(String, nullable=False, index=True)  # Milvus中的向量ID
    entity_id = Column(String, nullable=True, index=True)  # KùzuDB中的实体ID
    type = Column(String, nullable=False, index=True)  # 'long_term'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(), index=True)  # 记录时间（系统当前时间，本地时间）
    event_time = Column(DateTime, nullable=True, index=True)  # 事件时间（LLM提取，用户提到的具体时间）
    last_accessed_at = Column(DateTime, default=lambda: datetime.now(), index=True)  # 使用本地时间（北京时间）
    access_count = Column(Integer, default=0)
    meta_data = Column(Text, nullable=True)  # JSON格式的其他元数据

    # 添加复合索引
    __table_args__ = (
        Index('idx_persona_type', 'persona_id', 'type'),
        Index('idx_persona_created', 'persona_id', 'created_at'),
        Index('idx_vector_entity', 'vector_id', 'entity_id'),
        Index('idx_event_time_persona', 'event_time', 'persona_id'),
    )

    def get_metadata(self) -> dict:
        """获取元数据"""
        if self.meta_data is not None:
            return json.loads(str(self.meta_data))
        return {}

    def set_metadata(self, metadata: dict):
        """设置元数据"""
        self.meta_data = json.dumps(metadata)


class Configuration(Base):
    """配置表 - 用于存储系统配置"""
    __tablename__ = "configurations"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True, default="system")  # 用户ID，system表示系统级配置
    config_key = Column(String, nullable=False, index=True)  # 配置键
    config_value = Column(Text, nullable=False)  # 配置值（JSON格式）
    description = Column(Text, nullable=True)  # 配置描述
    created_at = Column(DateTime, default=lambda: datetime.now())  # 使用本地时间（北京时间）
    updated_at = Column(DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())  # 使用本地时间（北京时间）

    # 添加复合索引
    __table_args__ = (
        Index('idx_user_key', 'user_id', 'config_key', unique=True),
    )

    def get_value(self) -> dict:
        """获取配置值"""
        if self.config_value is not None:
            return json.loads(str(self.config_value))
        return {}

    def set_value(self, value: dict):
        """设置配置值"""
        self.config_value = json.dumps(value)


# 创建所有表
def init_db():
    """初始化数据库"""
    Base.metadata.create_all(bind=engine)


# 数据库依赖
def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
