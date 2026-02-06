from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any
import os
import json
from datetime import datetime, timezone


class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/v1"
    PROJECT_NAME: str = "MemPoint"

    # Security
    API_KEY: str = "test_key"  # 全局访问密钥（用于权限控制）
    SECRET_KEY: str = "your-secret-key-please-change-it"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Storage Paths
    DATA_DIR: str = os.path.join(os.path.dirname(__file__), "data")
    MILVUS_URI: str = os.path.join(DATA_DIR, "milvus", "milvus.db")
    KUZU_DB_PATH: str = os.path.join(DATA_DIR, "kuzu", "kuzu.db")
    SQLITE_DB_PATH: str = os.path.join(DATA_DIR, "mempoint.db")

    # LLM API Configuration
    LLM_BASE_URL: str = "https://api.siliconflow.cn/v1"
    LLM_API_KEY: Optional[str] = "sk-xxx"
    LLM_MODEL: str = "deepseek-ai/DeepSeek-V3.2"
    LLM_TIMEOUT: int = 60

    # Embedding API Configuration (独立于LLM配置)
    EMBEDDING_BASE_URL: str = "https://api.siliconflow.cn/v1"
    EMBEDDING_API_KEY: Optional[str] = "sk-xxx"
    EMBEDDING_MODEL: str = "Pro/BAAI/bge-m3"
    EMBEDDING_DIMENSIONS: int = 1024
    EMBEDDING_TIMEOUT: int = 30

    # Memory Extraction LLM Configuration (独立于LLM配置)
    MEMORY_EXTRACTION_BASE_URL: str = "https://api.siliconflow.cn/v1"
    MEMORY_EXTRACTION_API_KEY: Optional[str] = "sk-xxx"
    MEMORY_EXTRACTION_MODEL: str = "deepseek-ai/DeepSeek-V3.2"
    MEMORY_EXTRACTION_TIMEOUT: int = 60

    # Memory System Configuration
    MEMORY_ENABLED: bool = True
    MEMORY_MAX_LONG_TERM: int = 3
    MEMORY_INJECTION_MODE: str = "system"  # 'system', 'messages', 'mixed'
    MEMORY_DEDUP_THRESHOLD: float = 0.85  # 记忆去重的相似度阈值（0-1）

    # Memory Extraction Prompt
    MEMORY_EXTRACTION_PROMPT: str = """分析对话，提取重要信息、实体和关系。

当前时间：{current_time}
当前日期：{current_date}

对话内容：
{conversation_text}

返回JSON格式（必须严格遵循）：
{{
  "memories": [
    {{
      "content": "记忆内容",
      "event_time": "事件发生时间（ISO格式，精确到分钟，如2024-01-15T14:30:00）"  // 如果对话中提到具体时间
    }}
  ],
  "entities": [
    {{"name": "实体名称", "type": "实体类型"}}
  ],
  "relations": [
    {{"from": "实体1", "to": "实体2", "type": "关系类型"}}
  ]
}}

提取类型：
1. 记忆：用户的重要偏好（如喜欢/不喜欢）、重要事实（如生日、联系方式）、用户要求记住的信息
2. 实体：人名、地名、物品、日期等
3. 关系：实体间的关系（如"喜欢"、"出生于"、"工作于"等）
4. 时间：
   - event_time：事件发生时间（从对话内容中提取，如"昨天"、"上周"、"2024年1月15日"）
   - 时间格式要求：精确到分钟（ISO 8601格式：YYYY-MM-DDTHH:MM:SS）
   - 重要：event_time必须使用与当前时间相同的时区（北京时间），不要转换为UTC或其他时区
   - 如果对话中没有提到具体时间，event_time为null

时间参考：
- 刚才：{current_time}的前几分钟
- 半小时前：{current_time}的30分钟前
- 一小时前：{current_time}的1小时前
- 昨天：{current_date}的前一天
- 今天：{current_date}
- 上周：{current_date}的前7天
- 本月：{current_date}的月份

如果对话中没有重要信息，返回空数组。"""

    # Memory Scoring Configuration
    MEMORY_SCORE_SIMILARITY_WEIGHT: float = 0.4
    MEMORY_SCORE_ACCESS_WEIGHT: float = 0.3
    MEMORY_SCORE_RECENCY_WEIGHT: float = 0.2
    MEMORY_SCORE_GRAPH_WEIGHT: float = 0.1
    MEMORY_RECENCY_DECAY_LAMBDA: float = 0.000001  # 毫秒级衰减系数（调整后：1小时后评分≈0.69，1天后≈0.48，1周后≈0.23）

    # Persona Configuration
    DEFAULT_PERSONA_ID: str = "默认助手"  # 默认记忆体ID/名称
    DEFAULT_PERSONA_DESCRIPTION: str = "MemPoint 默认助手"  # 默认记忆体描述
    DEFAULT_PERSONA_SYSTEM_PROMPT: str = """你是一个智能助手，能够记住用户的对话内容并根据记忆提供个性化的回复。

你的特点：
- 友好、专业、乐于助人
- 能够根据记忆中的信息理解用户的偏好和需求
- 在适当的时候引用用户之前提到的信息
- 保持对话的连贯性和个性化

注意事项：
- 如果记忆中有相关信息，请自然地融入你的回复中
- 如果没有相关记忆，就正常回答用户的问题
- 不要明确提及"记忆"或"我记得"，而是自然地使用这些信息"""  # 默认记忆体系统提示词

    # Milvus Configuration
    MILVUS_COLLECTION_KNOWLEDGE: str = "knowledge_vectors"
    MILVUS_TOP_K: int = 10

    # KùzuDB Configuration
    KUZU_NODE_TABLE_USER: str = "User"
    KUZU_NODE_TABLE_ENTITY: str = "Entity"
    KUZU_NODE_TABLE_CONCEPT: str = "Concept"
    KUZU_REL_TABLE_MENTIONS: str = "MENTIONS"
    KUZU_REL_TABLE_RELATED_TO: str = "RELATED_TO"
    KUZU_REL_TABLE_BELONGS_TO: str = "BELONGS_TO"

    # Cache Configuration
    CACHE_TTL: int = 3600  # 缓存过期时间（秒）

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()


def get_default_configurations() -> Dict[str, Dict[str, Any]]:
    """
    获取默认配置
    返回一个字典，键为配置键，值为配置值和描述
    """
    return {
        "llm": {
            "value": {
                "base_url": settings.LLM_BASE_URL,
                "api_key": settings.LLM_API_KEY,
                "model": settings.LLM_MODEL,
                "timeout": settings.LLM_TIMEOUT,
            },
            "description": "LLM API 配置"
        },
        "embedding": {
            "value": {
                "base_url": settings.EMBEDDING_BASE_URL,
                "api_key": settings.EMBEDDING_API_KEY,
                "model": settings.EMBEDDING_MODEL,
                "dimensions": settings.EMBEDDING_DIMENSIONS,
                "timeout": settings.EMBEDDING_TIMEOUT,
            },
            "description": "Embedding API 配置"
        },
        "memory_extraction": {
            "value": {
                "base_url": settings.MEMORY_EXTRACTION_BASE_URL,
                "api_key": settings.MEMORY_EXTRACTION_API_KEY,
                "model": settings.MEMORY_EXTRACTION_MODEL,
                "timeout": settings.MEMORY_EXTRACTION_TIMEOUT,
                "prompt": settings.MEMORY_EXTRACTION_PROMPT,
            },
            "description": "记忆提取 LLM 配置"
        },
        "memory_system": {
            "value": {
                "enabled": settings.MEMORY_ENABLED,
                "max_long_term": settings.MEMORY_MAX_LONG_TERM,
                "injection_mode": settings.MEMORY_INJECTION_MODE,
                "dedup_threshold": settings.MEMORY_DEDUP_THRESHOLD,
            },
            "description": "记忆系统配置"
        },
        "memory_scoring": {
            "value": {
                "similarity_weight": settings.MEMORY_SCORE_SIMILARITY_WEIGHT,
                "access_weight": settings.MEMORY_SCORE_ACCESS_WEIGHT,
                "recency_weight": settings.MEMORY_SCORE_RECENCY_WEIGHT,
                "graph_weight": settings.MEMORY_SCORE_GRAPH_WEIGHT,
                "recency_decay_lambda": settings.MEMORY_RECENCY_DECAY_LAMBDA,
            },
            "description": "记忆评分配置"
        },
        "milvus": {
            "value": {
                "collection_knowledge": settings.MILVUS_COLLECTION_KNOWLEDGE,
                "top_k": settings.MILVUS_TOP_K,
            },
            "description": "Milvus 向量数据库配置"
        },
        "kuzu": {
            "value": {
                "node_table_user": settings.KUZU_NODE_TABLE_USER,
                "node_table_entity": settings.KUZU_NODE_TABLE_ENTITY,
                "node_table_concept": settings.KUZU_NODE_TABLE_CONCEPT,
                "rel_table_mentions": settings.KUZU_REL_TABLE_MENTIONS,
                "rel_table_related_to": settings.KUZU_REL_TABLE_RELATED_TO,
                "rel_table_belongs_to": settings.KUZU_REL_TABLE_BELONGS_TO,
            },
            "description": "KùzuDB 图数据库配置"
        },
        "cache": {
            "value": {
                "ttl": settings.CACHE_TTL,
            },
            "description": "缓存配置"
        },
    }


def initialize_configurations():
    """
    初始化配置到数据库
    将默认配置写入数据库，如果配置已存在则跳过
    """
    from models.database import SessionLocal, Configuration
    from utils.logger import logger
    from utils.helpers import generate_id

    db = SessionLocal()
    try:
        default_configs = get_default_configurations()

        for config_key, config_data in default_configs.items():
            # 检查配置是否已存在
            existing_config = db.query(Configuration).filter(
                Configuration.user_id == "system",
                Configuration.config_key == config_key
            ).first()

            if existing_config:
                logger.debug(f"Configuration '{config_key}' already exists, skipping")
                continue

            # 创建新配置
            config = Configuration(
                id=generate_id(),
                user_id="system",
                config_key=config_key,
                config_value=json.dumps(config_data["value"]),
                description=config_data["description"],
                created_at=datetime.now(),  # 使用本地时间（北京时间）
                updated_at=datetime.now()  # 使用本地时间（北京时间）
            )
            db.add(config)
            logger.info(f"Initialized configuration: {config_key}")

        db.commit()
        logger.info(f"Configuration initialization completed. Total configs: {len(default_configs)}")

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to initialize configurations: {e}")
        raise
    finally:
        db.close()


def get_configuration_from_db(config_key: str) -> Optional[Dict[str, Any]]:
    """
    从数据库获取配置
    如果配置不存在，返回默认值
    """
    from models.database import SessionLocal, Configuration
    from utils.logger import logger

    db = SessionLocal()
    try:
        config = db.query(Configuration).filter(
            Configuration.user_id == "system",
            Configuration.config_key == config_key
        ).first()

        if config:
            return config.get_value()
        else:
            # 返回默认配置
            default_configs = get_default_configurations()
            if config_key in default_configs:
                logger.warning(f"Configuration '{config_key}' not found in database, using default value")
                return default_configs[config_key]["value"]
            return None

    except Exception as e:
        logger.error(f"Failed to get configuration '{config_key}': {e}")
        return None
    finally:
        db.close()


def update_configuration_in_db(config_key: str, config_value: Dict[str, Any]) -> bool:
    """
    更新数据库中的配置
    """
    from models.database import SessionLocal, Configuration
    from utils.logger import logger

    db = SessionLocal()
    try:
        config = db.query(Configuration).filter(
            Configuration.user_id == "system",
            Configuration.config_key == config_key
        ).first()

        if config:
            config.set_value(config_value)
            config.updated_at = datetime.now()  # 使用本地时间（北京时间）
            logger.info(f"Updated configuration: {config_key}")
        else:
            # 创建新配置
            from utils.helpers import generate_id
            default_configs = get_default_configurations()
            description = default_configs.get(config_key, {}).get("description", "")

            config = Configuration(
                id=generate_id(),
                user_id="system",
                config_key=config_key,
                config_value=json.dumps(config_value),
                description=description,
                created_at=datetime.now(),  # 使用本地时间（北京时间）
                updated_at=datetime.now()  # 使用本地时间（北京时间）
            )
            db.add(config)
            logger.info(f"Created configuration: {config_key}")

        db.commit()
        return True

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update configuration '{config_key}': {e}")
        return False
    finally:
        db.close()


def initialize_default_persona():
    """
    初始化默认人格
    如果默认人格不存在，则创建它
    """
    from models.database import SessionLocal, Persona
    from utils.logger import logger

    db = SessionLocal()
    try:
        # 检查默认人格是否已存在
        existing_persona = db.query(Persona).filter(
            Persona.id == settings.DEFAULT_PERSONA_ID
        ).first()

        if existing_persona:
            logger.debug(f"Default persona '{settings.DEFAULT_PERSONA_ID}' already exists, skipping")
            return

        # 创建默认人格
        persona = Persona(
            id=settings.DEFAULT_PERSONA_ID,
            description=settings.DEFAULT_PERSONA_DESCRIPTION,
            system_prompt=settings.DEFAULT_PERSONA_SYSTEM_PROMPT,
        )

        db.add(persona)
        db.commit()
        logger.info(f"Initialized default persona: {settings.DEFAULT_PERSONA_ID}")

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to initialize default persona: {e}")
        raise
    finally:
        db.close()
