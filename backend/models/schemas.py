"""
Pydantic 模型定义
"""
from pydantic import BaseModel, Field, computed_field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============ 记忆体相关 ============

class PersonaBase(BaseModel):
    description: Optional[str] = None
    system_prompt: Optional[str] = None


class PersonaCreate(BaseModel):
    id: str
    description: Optional[str] = None
    system_prompt: Optional[str] = None


class PersonaUpdate(BaseModel):
    description: Optional[str] = None
    system_prompt: Optional[str] = None


class PersonaResponse(BaseModel):
    id: str
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ 记忆相关 ============

class MemoryBase(BaseModel):
    type: str = Field(..., description="'long_term'")
    content: str
    event_time: Optional[datetime] = None  # 事件时间（LLM提取，用户提到的具体时间）


class MemoryCreate(MemoryBase):
    persona_id: str
    vector_id: str
    entity_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class MemoryUpdate(BaseModel):
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class MemoryResponse(MemoryBase):
    id: str
    persona_id: str
    vector_id: str
    entity_id: Optional[str] = None
    created_at: datetime
    last_accessed_at: datetime
    access_count: int
    score: float
    meta_data: Optional[str] = None  # 从 SQLAlchemy 模型读取的 JSON 字符串

    @computed_field
    @property
    def metadata(self) -> Optional[Dict[str, Any]]:
        """从 meta_data 解析元数据"""
        import json
        if self.meta_data is not None:
            return json.loads(str(self.meta_data))
        return None

    class Config:
        from_attributes = True


# ============ LLM API 相关 ============

class ToolFunction(BaseModel):
    """工具函数定义"""
    name: str
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class Tool(BaseModel):
    """工具定义"""
    type: str = "function"
    function: ToolFunction


class ToolCall(BaseModel):
    """工具调用"""
    id: str
    type: str = "function"
    function: Dict[str, Any]


class ChatMessage(BaseModel):
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000
    stream: Optional[bool] = False
    tools: Optional[List[Tool]] = None
    tool_choice: Optional[Any] = None  # "auto", "none", 或 {"type": "function", "function": {"name": "function_name"}}
    memory_config: Optional[Dict[str, Any]] = None

    # 支持透传其他参数（如top_k, thinking等）
    class Config:
        extra = "allow"  # 允许额外的字段，直接透传给LLM


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Optional[Dict[str, Any]] = None


# ============ Embedding API 相关 ============

class EmbeddingRequest(BaseModel):
    input: str
    model: str


class EmbeddingResponse(BaseModel):
    object: str = "list"
    data: List[Dict[str, Any]]
    model: str
    usage: Dict[str, int]


# ============ 记忆检索相关 ============

class MemorySearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 10
    memory_type: Optional[str] = None  # 'long_term', None (all)
    metadata: Optional[Dict[str, Any]] = None  # 搜索元数据，如 user_id


class MemorySearchResult(BaseModel):
    id: str
    content: str
    type: str
    score: float
    similarity: float
    created_at: datetime
    last_accessed_at: datetime
    access_count: int


# ============ 知识图谱相关 ============

class EntityNode(BaseModel):
    name: str
    type: str
    description: Optional[str] = None
    created_at: Optional[int] = None
    last_accessed_at: Optional[int] = None


class RelationEdge(BaseModel):
    from_entity: str
    to_entity: str
    relation_type: str
    weight: Optional[float] = None
    created_at: Optional[int] = None


class GraphQueryRequest(BaseModel):
    entity_name: str
    max_depth: Optional[int] = 2


class GraphQueryResponse(BaseModel):
    nodes: List[EntityNode]
    edges: List[RelationEdge]


# ============ 记忆注入配置相关 ============

class MemoryInjectionConfig(BaseModel):
    enabled: bool = True
    max_long_term: int = 3
    injection_mode: str = "system"  # 'system', 'messages', 'mixed'


# ============ 配置相关 ============

class ConfigurationBase(BaseModel):
    config_key: str
    config_value: Dict[str, Any]
    description: Optional[str] = None


class ConfigurationCreate(ConfigurationBase):
    user_id: Optional[str] = "system"  # 默认为系统级配置


class ConfigurationUpdate(BaseModel):
    config_value: Optional[Dict[str, Any]] = None
    description: Optional[str] = None


class ConfigurationResponse(ConfigurationBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SystemConfigResponse(BaseModel):
    """系统配置响应"""
    llm: Dict[str, Any]
    embedding: Dict[str, Any]
    memory_extraction: Dict[str, Any]
    memory_system: Dict[str, Any]
    memory_scoring: Dict[str, Any]
    milvus: Dict[str, Any]
    kuzu: Dict[str, Any]
    cache: Dict[str, Any]


class SystemConfigUpdate(BaseModel):
    """系统配置更新"""
    llm: Optional[Dict[str, Any]] = None
    embedding: Optional[Dict[str, Any]] = None
    memory_extraction: Optional[Dict[str, Any]] = None
    memory_system: Optional[Dict[str, Any]] = None
    memory_scoring: Optional[Dict[str, Any]] = None
    milvus: Optional[Dict[str, Any]] = None
    kuzu: Optional[Dict[str, Any]] = None
    cache: Optional[Dict[str, Any]] = None
