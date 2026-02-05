# MemPoint - 带记忆注入的OpenAI风格API (KùzuDB版)

## 项目概述

MemPoint是一个轻量级的智能API中间件，通过集成长短期记忆系统（Milvus Lite + KùzuDB）为LLM提供上下文增强能力，同时兼容OpenAI API风格接口。采用完全standalone部署方式，所有数据存储在本地文件中，无需任何外部服务。

## 技术栈

### 后端
- **框架**: FastAPI 0.104+
- **语言**: Python 3.10+
- **向量数据库**: Milvus Lite 2.3+ (嵌入式向量搜索)
- **图数据库**: KùzuDB 0.3+ (嵌入式图数据库，支持Cypher)
- **关系数据库**: SQLite 3 (元数据存储)
- **嵌入模型**: OpenAI风格嵌入API (支持外部服务或本地兼容服务)
- **LLM客户端**: OpenAI SDK (支持多端点配置)
- **缓存**: Python内存缓存 (functools.lru_cache)

### 前端
- **框架**: Vue 3 + TypeScript
- **UI库**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **HTTP客户端**: Axios
- **图表库**: ECharts (用于知识图谱可视化)
- **构建工具**: Vite

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                           客户端应用                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  聊天界面     │  │  API配置管理  │  │  记忆管理界面  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI 后端                               │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    API 路由层                               │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │ │
│  │  │/chat/        │  │/completions/ │  │/models/      │      │ │
│  │  │completions   │  │              │  │              │      │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘      │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                              ▼                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   业务逻辑层                                 │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │ │
│  │  │  请求处理    │  │  记忆注入    │  │  响应转换    │      │ │
│  │  │  中间件      │  │  引擎        │  │  适配器      │      │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘      │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                              ▼                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   记忆系统层                                 │ │
│  │  ┌──────────────────────────────────────────────────────┐  │ │
│  │  │              Milvus Lite (本地文件)                    │  │ │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │  │ │
│  │  │  │ 短期记忆  │  │ 长期记忆  │  │ 语义索引  │          │  │ │
│  │  │  └──────────┘  └──────────┘  └──────────┘          │  │ │
│  │  └──────────────────────────────────────────────────────┘  │ │
│  │                              │                               │ │
│  │                              ▼                               │ │
│  │  ┌──────────────────────────────────────────────────────┐  │ │
│  │  │              KùzuDB (本地文件)                         │  │ │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │  │ │
│  │  │  │ 实体节点  │  │ 关系边    │  │ Cypher查询 │          │  │ │
│  │  │  └──────────┘  └──────────┘  └──────────┘          │  │ │
│  │  └──────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                              ▼                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   SQLite (元数据存储)                        │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │ │
│  │  │ 用户数据  │  │ 会话数据  │  │ 配置数据  │                  │ │
│  │  └──────────┘  └──────────┘  └──────────┘                  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                              ▼                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   LLM 代理层                                 │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │ │
│  │  │  配置管理    │  │  请求转发    │  │  流式响应    │      │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘      │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                   ┌─────────────────┐   ┌─────────────────┐
                   │   外部 LLM API   │   │ 外部 Embedding  │
                   │  (Chat/Comp)    │   │      API        │
                   └─────────────────┘   └─────────────────┘
```

## 分层架构设计

MemPoint后端采用清晰的分层架构，各层职责明确：

### 架构层次

```
┌─────────────────────────────────────────────────────────────┐
│                    API路由层 (api/)                          │
│  - 接收HTTP请求                                              │
│  - 请求参数验证（Pydantic）                                  │
│  - 调用业务服务层                                            │
│  - 返回响应（流式/非流式）                                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                 业务服务层 (services/)                       │
│  - 实现业务逻辑                                              │
│  - 协调多个核心模块                                          │
│  - 事务管理                                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                 核心业务逻辑层 (core/)                       │
│  - memory_engine: 记忆检索与注入                            │
│  - llm_client: LLM API代理转发                              │
│  - embedding_client: 向量化服务                             │
│  - response_adapter: 响应格式适配                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                 记忆系统层 (memory/)                         │
│  - vector_store: Milvus Lite向量存储                        │
│  - graph_store: KùzuDB图数据库                              │
│  - memory_manager: 记忆生命周期管理                         │
│  - retrieval: 检索策略与评分                                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              数据模型层 (models/)                            │
│  - schemas: API请求/响应Pydantic模型                        │
│  - database: SQLite ORM模型（SQLAlchemy）                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              数据存储层 (data/)                              │
│  - SQLite: 元数据（用户、会话、记忆索引）                   │
│  - Milvus Lite: 向量数据（嵌入式文件存储）                  │
│  - KùzuDB: 知识图谱（嵌入式文件存储）                       │
└─────────────────────────────────────────────────────────────┘
```

### 层次职责详解

**1. API路由层 (api/)**
- [`chat.py`](backend/api/chat.py): 处理 `/v1/chat/completions` 请求
- [`completions.py`](backend/api/completions.py): 处理 `/v1/completions` 请求
- [`models.py`](backend/api/models.py): 处理 `/v1/models` 请求
- 职责：参数验证、路由分发、响应格式化

**2. 业务服务层 (services/)**
- [`chat_service.py`](backend/services/chat_service.py): 聊天业务逻辑
- [`memory_service.py`](backend/services/memory_service.py): 记忆管理业务逻辑
- [`config_service.py`](backend/services/config_service.py): 配置管理业务逻辑
- 职责：业务流程编排、事务控制

**3. 核心业务逻辑层 (core/)**
- [`memory_engine.py`](backend/core/memory_engine.py): 记忆检索、评分、注入
- [`llm_client.py`](backend/core/llm_client.py): LLM API请求转发（支持流式）
- [`embedding_client.py`](backend/core/embedding_client.py): 文本向量化
- [`response_adapter.py`](backend/core/response_adapter.py): 响应格式适配
- 职责：独立可复用的核心功能

**4. 记忆系统层 (memory/)**
- [`vector_store.py`](backend/memory/vector_store.py): Milvus Lite CRUD操作
- [`graph_store.py`](backend/memory/graph_store.py): KùzuDB Cypher查询
- [`memory_manager.py`](backend/memory/memory_manager.py): 记忆生命周期管理
- [`retrieval.py`](backend/memory/retrieval.py): 检索策略实现
- 职责：记忆存储与检索的底层实现

**5. 数据模型层 (models/)**
- [`schemas.py`](backend/models/schemas.py): Pydantic数据模型（API层）
- [`database.py`](backend/models/database.py): SQLAlchemy ORM模型（数据层）
- 职责：数据结构定义、序列化/反序列化

**6. 工具层 (utils/)**
- [`logger.py`](backend/utils/logger.py): 日志配置
- [`helpers.py`](backend/utils/helpers.py): 通用辅助函数
- [`cache.py`](backend/utils/cache.py): 缓存工具
- 职责：通用工具函数

## 核心功能模块

### 1. API接口层

#### 1.1 Chat Completions API

- **端点**: `POST /v1/chat/completions`
- **实现文件**: [`backend/api/chat.py`](backend/api/chat.py)
- **功能**:
  - 接收OpenAI风格的聊天请求
  - 从记忆系统检索相关上下文
  - 将记忆注入到system prompt或messages中
  - 转发请求到LLM后端
  - 支持流式和非流式响应

**处理流程：**

```python
# 1. 提取用户查询
user_message = [msg for msg in messages if msg.role == "user"][-1]

# 2. 检索相关记忆（如果启用）
if memory_config.enabled:
    query_embedding = await embedding_client.embed(user_message)
    memories = await memory_engine.retrieve_memories(query=user_message)
    enhanced_messages = memory_engine.inject_memory(messages, memories)

# 3. 调用LLM API
if request.stream:
    return StreamingResponse(_stream_chat_completion(...))
else:
    response = await llm_client.chat_completion(enhanced_messages, ...)
    return response_adapter.adapt_chat_completion(response, model)
```

#### 1.2 Completions API

- **端点**: `POST /v1/completions`
- **实现文件**: [`backend/api/completions.py`](backend/api/completions.py)
- **功能**:
  - 接收文本补全请求
  - 记忆注入逻辑（可选）
  - 转发请求到LLM后端

#### 1.3 Models API

- **端点**: `GET /v1/models`
- **实现文件**: [`backend/api/models.py`](backend/api/models.py)
- **功能**:
  - 返回可用的模型列表
  - 聚合LLM后端和Embedding后端的模型
  - 支持自定义模型配置

### 2. 记忆系统架构

#### 2.1 记忆引擎实现

**核心模块：** [`backend/core/memory_engine.py`](backend/core/memory_engine.py)

**主要功能：**

1. **记忆检索** (`retrieve_memories`)
   ```python
   async def retrieve_memories(
       query: str,
       session_id: Optional[str] = None,
       user_id: Optional[str] = None
   ) -> Dict[str, List[Dict[str, Any]]]:
       # 1. 查询向量化（通过embedding_client）
       # 2. Milvus Lite向量检索（相似度搜索）
       # 3. KùzuDB图谱查询（关系扩展）
       # 4. 返回短期和长期记忆
   ```

2. **记忆评分** (`calculate_memory_score`)
   ```python
   final_score = (
       similarity_score * 0.4 +    # 相似度权重
       access_score * 0.3 +        # 访问频率权重
       recency_score * 0.2 +       # 时效性权重
       graph_score * 0.1           # 图谱权重
   )
   ```

3. **记忆注入** (`inject_memory`)
   - **System模式**: 注入到system prompt
   - **Messages模式**: 作为独立消息插入
   - **Mixed模式**: 长期记忆→system，短期记忆→messages

#### 2.2 向量存储层

**实现文件：** [`backend/memory/vector_store.py`](backend/memory/vector_store.py)

**Milvus Lite集合结构：**

```python
# knowledge_vectors (长期记忆)
{
    "id": "string",
    "content": "string",
    "embedding": "float_vector(1024)",  # 维度由EMBEDDING_DIMENSIONS配置
    "entity_id": "string",
    "created_at": "INT64",
    "last_accessed_at": "INT64",
    "access_count": "INT64",
    "score": "FLOAT"
}

# session_vectors (短期记忆)
{
    "id": "string",
    "session_id": "string",
    "content": "string",
    "embedding": "float_vector(1024)",
    "created_at": "INT64",
    "last_accessed_at": "INT64"
}
```

#### 2.3 图存储层

**实现文件：** [`backend/memory/graph_store.py`](backend/memory/graph_store.py)

**KùzuDB Schema：**

```cypher
-- 节点表
CREATE NODE TABLE User(name STRING, id STRING, PRIMARY KEY (id))
CREATE NODE TABLE Entity(
    name STRING, 
    type STRING, 
    description STRING, 
    created_at INT64, 
    last_accessed_at INT64, 
    PRIMARY KEY (name)
)
CREATE NODE TABLE Concept(
    name STRING, 
    description STRING, 
    created_at INT64, 
    PRIMARY KEY (name)
)

-- 关系表
CREATE REL TABLE MENTIONS(FROM User, TO Entity, timestamp INT64)
CREATE REL TABLE RELATED_TO(FROM Entity, TO Entity, weight DOUBLE, created_at INT64)
CREATE REL TABLE BELONGS_TO(FROM Entity, TO Concept, created_at INT64)
```

**典型查询示例：**

```cypher
-- 查找相关实体
MATCH (e1:Entity)-[r:RELATED_TO]->(e2:Entity)
WHERE e1.name = $entity_name
RETURN e2.name, e2.description, r.weight
ORDER BY r.weight DESC
LIMIT 5

-- 查找实体所属概念
MATCH (e:Entity)-[:BELONGS_TO]->(c:Concept)
WHERE e.name = $entity_name
RETURN c.name, c.description
```

#### 2.4 记忆管理器

**实现文件：** [`backend/memory/memory_manager.py`](backend/memory/memory_manager.py)

**生命周期管理：**

- `create_memory()`: 创建新记忆，初始化评分
- `get_memory()`: 获取记忆详情
- `update_memory_access()`: 更新访问统计
- `update_memory_score()`: 重新计算评分
- `delete_memory()`: 删除记忆
- `list_memories()`: 列出记忆
- `search_memories()`: 语义搜索记忆

#### 2.5 Milvus Lite + KùzuDB 协作机制

```
用户查询
    │
    ▼
┌─────────────────────┐
│  查询向量化          │
│  (调用Embedding API) │
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│  Milvus Lite 向量检索│
│  - 语义相似度搜索    │
│  - 返回Top-K结果     │
│  - 获取Entity ID     │
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│  KùzuDB 图谱查询     │
│  - 使用Cypher查询     │
│  - 查找相邻节点       │
│  - 多跳关系推理       │
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│  知识扩展与聚合       │
│  - 合并相关实体       │
│  - 构建上下文         │
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│  生成增强Prompt       │
│  (注入到LLM请求)      │
└─────────────────────┘
```

#### 2.2 记忆类型

**短期记忆 (Short-term Memory)**
- 存储位置: Milvus Lite (会话集合) + SQLite (Messages表)
- 内容: 当前对话的最近几轮记录

**长期记忆 (Long-term Memory)**
- 存储位置: Milvus Lite (知识集合) + KùzuDB (知识图谱)
- 内容: 从对话中提取的事实、实体、关系、用户偏好

#### 2.3 KùzuDB Schema设计

```python
import kuzu

# 初始化数据库
db = kuzu.Database("./data/kuzu")
conn = kuzu.Connection(db)

# 定义节点表
conn.execute("CREATE NODE TABLE User(name STRING, id STRING, PRIMARY KEY (id))")
conn.execute("CREATE NODE TABLE Entity(name STRING, type STRING, description STRING, created_at INT64, last_accessed_at INT64, PRIMARY KEY (name))")
conn.execute("CREATE NODE TABLE Concept(name STRING, description STRING, created_at INT64, PRIMARY KEY (name))")

# 定义关系表
conn.execute("CREATE REL TABLE MENTIONS(FROM User, TO Entity, timestamp INT64)")
conn.execute("CREATE REL TABLE RELATED_TO(FROM Entity, TO Entity, weight DOUBLE, created_at INT64)")
conn.execute("CREATE REL TABLE BELONGS_TO(FROM Entity, TO Concept, created_at INT64)")
```

### 3. 记忆注入策略

#### 3.1 注入时机
- **System Prompt注入**: 将记忆作为system message
- **Messages注入**: 将记忆作为assistant/user message插入
- **混合注入**: 结合system和messages注入

#### 3.2 注入内容选择
- 基于相似度的Top-K检索
- 基于KùzuDB的图谱关联查询
- 基于时间衰减的权重计算

#### 3.3 记忆评分机制

记忆评分采用多维度加权计算，综合评估记忆的重要性：

**评分公式：**
```
final_score = (similarity_score * 0.4) + (access_score * 0.3) + (recency_score * 0.2) + (graph_score * 0.1)
```

**评分维度：**

1. **相似度评分 (similarity_score, 40%)**
   - 基于向量相似度计算
   - 使用余弦相似度
   - 范围：0-1，值越高表示与查询越相关

2. **访问评分 (access_score, 30%)**
   - 基于访问次数和访问频率
   - 计算公式：`access_score = min(access_count / max_access_count, 1.0)`
   - 访问次数越多，评分越高
   - 范围：0-1

3. **时效性评分 (recency_score, 20%)**
   - 基于最后访问时间和创建时间
   - 考虑时间衰减：越近期的记忆权重越高
   - 计算公式：`recency_score = exp(-lambda * (current_time - last_accessed_at))`
   - lambda为衰减系数，默认为0.0001 (毫秒级)
   - 范围：0-1

4. **图谱评分 (graph_score, 10%)**
   - 基于KùzuDB中的图谱结构
   - 考虑节点的连接度、关系强度等
   - 计算公式：`graph_score = (node_degree / max_degree) * avg_relation_weight`
   - 范围：0-1

**评分更新策略：**

- 创建时：初始评分 = similarity_score (0.4)
- 每次访问时：更新 access_score 和 recency_score
- 图谱更新时：同步更新 graph_score
- 定期重新计算：每天重新计算所有记忆的评分

**时间戳管理：**

- `created_at`: 记忆创建时设置，永不修改
- `last_accessed_at`: 每次访问记忆时更新
- `access_count`: 每次访问记忆时递增

#### 3.4 注入格式

**System Prompt注入示例：**

```python
system_prompt = f"""你是一个智能助手。以下是相关的背景信息：

[相关知识]
{knowledge_graph_context}

[历史记忆]
{vector_memory_context}

请基于以上信息回答用户的问题。"""
```

**实现细节：** 见 [`backend/core/memory_engine.py`](backend/core/memory_engine.py) 的 `_inject_to_system()` 方法

### 4. LLM与Embedding客户端

#### 4.1 LLM客户端

**实现文件：** [`backend/core/llm_client.py`](backend/core/llm_client.py)

**功能：**
- 使用OpenAI SDK进行API调用
- 支持流式和非流式响应
- 可配置base_url、api_key、model
- 超时控制和错误处理

**使用示例：**

```python
from core.llm_client import llm_client

# 非流式
response = await llm_client.chat_completion(
    messages=[{"role": "user", "content": "Hello"}],
    temperature=0.7,
    max_tokens=1000
)

# 流式
async for chunk in llm_client.chat_completion_stream(messages=[...]):
    print(chunk, end="")
```

#### 4.2 Embedding客户端

**实现文件：** [`backend/core/embedding_client.py`](backend/core/embedding_client.py)

**功能：**
- 文本向量化（独立的API配置）
- 支持批量向量化
- 结果缓存（可选）
- 维度验证

**配置：**
```python
EMBEDDING_BASE_URL: str = "https://api.siliconflow.com/v1"
EMBEDDING_MODEL: str = "BAAI/bge-m3"
EMBEDDING_DIMENSIONS: int = 1024
```

**使用示例：**

```python
from core.embedding_client import embedding_client

# 单文本向量化
embedding = await embedding_client.embed("Hello world")
# 返回: List[float] (长度=1024)

# 批量向量化
embeddings = await embedding_client.embed_batch([
    "Text 1",
    "Text 2",
    "Text 3"
])
# 返回: List[List[float]]
```

#### 4.3 响应适配器

**实现文件：** [`backend/core/response_adapter.py`](backend/core/response_adapter.py)

**功能：**
- 将不同LLM后端的响应格式统一为OpenAI风格
- 处理流式响应的格式转换
- 添加必要的元数据（model、usage等）

### 5. 前端功能模块（规划中）

前端将使用 Vue 3 + TypeScript + Element Plus 开发，计划实现以下功能：

#### 5.1 聊天界面
- 多轮对话界面
- 流式响应显示
- 对话历史管理
- 实时记忆注入预览
- Markdown渲染
- 代码高亮

#### 5.2 API配置管理
- LLM API配置 (base_url, api_key, model)
- 嵌入模型配置 (base_url, api_key, model, dimensions) - 独立于LLM配置
- 记忆系统配置
- 记忆注入策略配置
- 配置持久化 (通过后端API)

#### 5.3 记忆管理界面
- 记忆内容浏览
- 记忆搜索与过滤
- 记忆编辑与删除
- 记忆分类管理
- 记忆导入导出

#### 5.4 知识图谱可视化
- 实体关系图展示（使用ECharts）
- 交互式图谱浏览
- 节点详情查看
- 关系路径追踪

**技术栈：**
- 框架: Vue 3 + TypeScript
- UI库: Element Plus
- 状态管理: Pinia
- 路由: Vue Router 4
- HTTP客户端: Axios
- 图表库: ECharts
- 构建工具: Vite

### 6. 数据库Schema设计

#### 6.1 SQLite (元数据存储)

**实现文件：** [`backend/models/database.py`](backend/models/database.py)

**ORM模型（SQLAlchemy）：**

```python
class User(Base):
    """用户表"""
    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Session(Base):
    """会话表"""
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship("User", backref="sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")

class Message(Base):
    """消息表"""
    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False, index=True)
    role = Column(String, nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    memory_ids = Column(Text, nullable=True)  # JSON格式的记忆ID列表
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    session = relationship("Session", back_populates="messages")

class Memory(Base):
    """记忆表 - 用于追踪记忆的元数据"""
    id = Column(String, primary_key=True, index=True)
    vector_id = Column(String, nullable=False, index=True)  # Milvus中的向量ID
    entity_id = Column(String, nullable=True, index=True)  # KùzuDB中的实体ID
    type = Column(String, nullable=False)  # 'short_term', 'long_term'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed_at = Column(DateTime, default=datetime.utcnow)
    access_count = Column(Integer, default=0)
    score = Column(Float, default=0.0)
    meta_data = Column(Text, nullable=True)  # JSON格式的其他元数据
    
    def get_metadata(self) -> dict:
        """获取元数据"""
        if self.meta_data:
            return json.loads(self.meta_data)
        return {}
    
    def set_metadata(self, metadata: dict):
        """设置元数据"""
        self.meta_data = json.dumps(metadata)

class Configuration(Base):
    """配置表"""
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    config_key = Column(String, nullable=False)
    config_value = Column(Text, nullable=False)  # JSON格式
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 唯一约束
    __table_args__ = (UniqueConstraint('user_id', 'config_key', name='unique_user_config'),)
```

**数据库初始化：**

```python
from models.database import init_db

# 创建所有表
init_db()
```

#### 6.2 Milvus Lite Collection结构

**实现文件：** [`backend/memory/vector_store.py`](backend/memory/vector_store.py)

**知识向量集合 (knowledge_vectors):**

```python
from pymilvus import CollectionSchema, FieldSchema, DataType

fields = [
    FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=64),
    FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=4096),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1024),  # 维度由配置决定
    FieldSchema(name="entity_id", dtype=DataType.VARCHAR, max_length=64),
    FieldSchema(name="created_at", dtype=DataType.INT64),
    FieldSchema(name="last_accessed_at", dtype=DataType.INT64),
    FieldSchema(name="access_count", dtype=DataType.INT64),
    FieldSchema(name="score", dtype=DataType.FLOAT)
]

schema = CollectionSchema(
    fields=fields,
    description="Knowledge vectors for long-term memory"
)
```

**会话向量集合 (session_vectors):**

```python
fields = [
    FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=64),
    FieldSchema(name="session_id", dtype=DataType.VARCHAR, max_length=64),
    FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=4096),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1024),
    FieldSchema(name="created_at", dtype=DataType.INT64),
    FieldSchema(name="last_accessed_at", dtype=DataType.INT64)
]

schema = CollectionSchema(
    fields=fields,
    description="Session vectors for short-term memory"
)
```

**索引配置：**

```python
from pymilvus import Collection

# 创建向量索引
index_params = {
    "metric_type": "COSINE",  # 或 "L2", "IP"
    "index_type": "IVF_FLAT",
    "params": {"nlist": 128}
}

collection.create_index(
    field_name="embedding",
    index_params=index_params
)
```

### 7. API接口规范

#### 7.1 Chat Completions

**端点：** `POST /v1/chat/completions`

**请求示例：**

```json
{
  "model": "deepseek-ai/DeepSeek-V3.2",
  "messages": [
    {"role": "system", "content": "你是一个智能助手。"},
    {"role": "user", "content": "你好"}
  ],
  "temperature": 0.7,
  "max_tokens": 1000,
  "stream": false,
  "memory_config": {
    "enabled": true,
    "max_short_term": 5,
    "max_long_term": 3,
    "injection_mode": "system"
  }
}
```

**响应示例（非流式）：**

```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "deepseek-ai/DeepSeek-V3.2",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "你好！有什么我可以帮助你的吗？"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 10,
    "total_tokens": 25
  }
}
```

**响应示例（流式）：**

```
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"deepseek-ai/DeepSeek-V3.2","choices":[{"index":0,"delta":{"content":"你"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"deepseek-ai/DeepSeek-V3.2","choices":[{"index":0,"delta":{"content":"好"},"finish_reason":null}]}

data: [DONE]
```

#### 7.2 Completions

**端点：** `POST /v1/completions`

**请求示例：**

```json
{
  "model": "deepseek-ai/DeepSeek-V3.2",
  "prompt": "Once upon a time",
  "temperature": 0.7,
  "max_tokens": 100,
  "stream": false
}
```

#### 7.3 Models

**端点：** `GET /v1/models`

**响应示例：**

```json
{
  "object": "list",
  "data": [
    {
      "id": "deepseek-ai/DeepSeek-V3.2",
      "object": "model",
      "created": 1677652288,
      "owned_by": "system"
    },
    {
      "id": "BAAI/bge-m3",
      "object": "model",
      "created": 1677652288,
      "owned_by": "system"
    }
  ]
}
```

#### 7.4 Memory配置参数

**memory_config字段说明：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enabled` | boolean | `true` | 是否启用记忆注入 |
| `max_short_term` | integer | `5` | 最大短期记忆数量 |
| `max_long_term` | integer | `3` | 最大长期记忆数量 |
| `injection_mode` | string | `"system"` | 注入模式：`"system"`, `"messages"`, `"mixed"` |

**injection_mode说明：**

- `"system"`: 将记忆注入到system prompt中
- `"messages"`: 将记忆作为独立消息插入
- `"mixed"`: 长期记忆注入system，短期记忆作为消息

### 7. 项目目录结构

```
mempoint/
├── backend/                    # 后端项目
│   ├── main.py                # FastAPI应用入口
│   ├── config.py              # 配置管理
│   ├── api/                   # API路由层
│   │   ├── __init__.py
│   │   ├── chat.py           # Chat Completions API
│   │   ├── completions.py    # Completions API
│   │   └── models.py         # Models API
│   ├── core/                  # 核心业务逻辑层
│   │   ├── __init__.py
│   │   ├── memory_engine.py    # 记忆注入引擎
│   │   ├── llm_client.py       # LLM客户端（代理转发）
│   │   ├── embedding_client.py # Embedding客户端
│   │   └── response_adapter.py # 响应格式适配器
│   ├── memory/                # 记忆系统层
│   │   ├── __init__.py
│   │   ├── vector_store.py     # Milvus Lite向量存储
│   │   ├── graph_store.py      # KùzuDB图数据库操作
│   │   ├── memory_manager.py   # 记忆生命周期管理
│   │   └── retrieval.py        # 记忆检索策略
│   ├── models/                # 数据模型层
│   │   ├── database.py         # SQLite ORM模型（SQLAlchemy）
│   │   └── schemas.py          # API请求/响应模型（Pydantic）
│   ├── services/              # 业务服务层
│   │   ├── __init__.py
│   │   ├── chat_service.py     # 聊天服务
│   │   ├── memory_service.py   # 记忆服务
│   │   └── config_service.py   # 配置服务
│   ├── utils/                 # 工具函数层
│   │   ├── __init__.py
│   │   ├── logger.py          # 日志工具
│   │   ├── helpers.py         # 辅助函数
│   │   └── cache.py           # 缓存工具
│   ├── data/                  # 数据存储目录
│   │   ├── milvus/           # Milvus Lite数据文件
│   │   ├── kuzu/             # KùzuDB数据文件
│   │   └── mempoint.db       # SQLite数据库文件
│   ├── tests/                # 单元测试
│   ├── requirements.txt      # Python依赖清单
│   └── init_dirs.py          # 数据目录初始化脚本
│
├── frontend/                # 前端项目（待实现）
│   └── README.md
│
├── docs/                    # 文档
│   └── README.md
│
├── plans/                   # 规划文档
│   └── architecture.md     # 本架构文档
│
├── init_dirs.py            # 项目初始化脚本
└── README.md               # 项目说明
```

**目录说明：**

- `backend/`: 后端主要代码目录
  - `api/`: API路由处理
  - `core/`: 核心业务逻辑（LLM客户端、记忆引擎等）
  - `memory/`: 记忆系统（向量存储、图存储）
  - `models/`: 数据模型（Pydantic + SQLAlchemy）
  - `services/`: 业务服务层
  - `utils/`: 工具函数
  - `data/`: 本地数据存储目录
- `frontend/`: 前端项目（Vue 3，待实现）
- `docs/`: 项目文档
- `plans/`: 设计规划文档

### 8. 部署架构

#### 8.1 本地开发部署

**启动后端服务：**

```bash
# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt

# 启动服务（开发模式）
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**服务启动流程：**

1. 加载配置（`config.py`）
2. 初始化数据目录（`data/milvus`, `data/kuzu`）
3. 初始化SQLite数据库（`init_db()`）
4. 注册API路由（chat, completions, models）
5. 启动FastAPI应用

**健康检查：**

```bash
# 根路径
curl http://localhost:8000/

# 健康检查
curl http://localhost:8000/health

# API文档
open http://localhost:8000/docs
```

#### 8.2 Standalone部署

```
┌─────────────────────────────────────────────────────────────┐
│                   单机部署环境                                │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │  FastAPI     │  │   Vue App    │                         │
│  │  (Backend)   │  │  (Frontend)  │                         │
│  │  :8000       │  │  :80/3000    │                         │
│  └──────────────┘  └──────────────┘                         │
│         │                  │                                 │
│         └──────────────────┼─────────────────┐               │
│                            │                 │               │
│         ┌──────────────────┼─────────────────┼───────┐       │
│         ▼                  ▼                 ▼       │       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │       │
│  │ Milvus Lite  │  │   KùzuDB     │  │   SQLite     │ │       │
│  │  (本地文件)   │  │  (本地文件)   │  │  (本地文件)   │ │       │
│  │  ./data/     │  │  ./data/     │  │  ./data/     │ │       │
│  │  milvus/     │  │  kuzu/       │  │  mempoint.db │ │       │
│  └──────────────┘  └──────────────┘  └──────────────┘ │       │
│                                                         │       │
│  ┌──────────────┐  ┌──────────────┐                    │       │
│  │ LLM Client   │  │ Embedding    │                    │       │
│  │ (OpenAI SDK) │  │ Client       │                    │       │
│  └──────────────┘  └──────────────┘                    │       │
└─────────────────────────────────────────────────────────┘       │
                                                                  │
                     ┌─────────────────┐   ┌─────────────────┐   │
                     │   外部 LLM API   │   │ 外部 Embedding  │   │
                     │ (SiliconFlow等) │   │      API        │   │
                     └─────────────────┘   └─────────────────┘   │
```

#### 8.3 生产部署建议

**使用Gunicorn + Uvicorn Worker：**

```bash
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

**使用Docker：**

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 初始化数据目录
RUN python init_dirs.py

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**数据持久化：**

所有数据存储在 `backend/data/` 目录：
- `milvus/`: Milvus Lite数据文件
- `kuzu/`: KùzuDB数据文件
- `mempoint.db`: SQLite数据库

建议挂载 `data/` 目录为持久卷。

## 配置管理

### 配置文件结构

配置通过 [`config.py`](backend/config.py) 集中管理，使用 `pydantic-settings` 实现：

```python
class Settings(BaseSettings):
    # API配置
    API_V1_STR: str = "/v1"
    PROJECT_NAME: str = "MemPoint"
    
    # 存储路径
    DATA_DIR: str = "backend/data"
    MILVUS_URI: str = "backend/data/milvus/milvus.db"
    KUZU_DB_PATH: str = "backend/data/kuzu"
    SQLITE_DB_PATH: str = "backend/data/mempoint.db"
    
    # LLM API配置
    LLM_BASE_URL: str = "https://api.siliconflow.com/v1"
    LLM_API_KEY: Optional[str]
    LLM_MODEL: str = "deepseek-ai/DeepSeek-V3.2"
    LLM_TIMEOUT: int = 60
    
    # Embedding API配置（独立于LLM）
    EMBEDDING_BASE_URL: str = "https://api.siliconflow.com/v1"
    EMBEDDING_API_KEY: Optional[str]
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    EMBEDDING_DIMENSIONS: int = 1024
    EMBEDDING_TIMEOUT: int = 30
    
    # 记忆系统配置
    MEMORY_ENABLED: bool = True
    MEMORY_MAX_SHORT_TERM: int = 5
    MEMORY_MAX_LONG_TERM: int = 3
    MEMORY_INJECTION_MODE: str = "system"  # 'system', 'messages', 'mixed'
    
    # 记忆评分权重
    MEMORY_SCORE_SIMILARITY_WEIGHT: float = 0.4
    MEMORY_SCORE_ACCESS_WEIGHT: float = 0.3
    MEMORY_SCORE_RECENCY_WEIGHT: float = 0.2
    MEMORY_SCORE_GRAPH_WEIGHT: float = 0.1
    MEMORY_RECENCY_DECAY_LAMBDA: float = 0.0001
```

### 环境变量支持

支持通过 `.env` 文件或系统环境变量覆盖配置：

```bash
# .env 示例
LLM_API_KEY=your-llm-api-key
EMBEDDING_API_KEY=your-embedding-api-key
LLM_BASE_URL=https://api.openai.com/v1
EMBEDDING_BASE_URL=https://api.openai.com/v1
```

## 依赖清单

### 后端依赖 (requirements.txt)

```
# Web框架
fastapi==0.104.1
uvicorn[standard]==0.24.0

# 数据验证
pydantic==2.5.0
pydantic-settings==2.1.0

# 数据库
pymilvus==2.3.4
kuzu==0.3.0
sqlalchemy==2.0.23

# LLM客户端
openai==1.3.0
httpx==0.25.2

# 工具
python-multipart==0.0.6
```

**依赖说明：**
- `fastapi`: Web框架，提供高性能异步API
- `pydantic-settings`: 配置管理，支持环境变量
- `pymilvus`: Milvus Lite客户端，嵌入式向量数据库
- `kuzu`: KùzuDB Python绑定，嵌入式图数据库
- `sqlalchemy`: ORM框架，用于SQLite操作
- `openai`: OpenAI SDK，用于LLM和Embedding API调用
