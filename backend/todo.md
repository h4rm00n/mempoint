# MemPoint 后端待办事项

## 📊 当前状态总结 (2026-02-04)

### ✅ 已完成的核心功能
- **极简架构重构**：已成功从多用户/多会话模式转型为单用户/多人格模式
- **记忆体（Persona）系统**：完整的Persona CRUD API已实现
- **记忆注入引擎**：基于`persona_id`的长期记忆检索和注入已完全实现
- **综合评分机制**：相似度、访问频率、时间衰减、图谱评分的综合重排序已实现
- **OpenAI兼容API**：`GET /v1/models`列出记忆体，`POST /v1/chat/completions`使用`model`参数指定记忆体
- **三重存储架构**：Milvus Lite（向量）+ KùzuDB（图谱）+ SQLite（元数据）已完全集成

### ⚠️ 待完善的功能
- **记忆删除**：向量库删除逻辑待实现（`services/memory_service.py:178`）
- **记忆更新评分**：更新记忆内容后未重新计算评分（`services/memory_service.py:136-144`）
- **代码清理**：残留的短期记忆配置和代码建议清理

### 🎯 下一步优先级
1. 实现向量库删除功能（高优先级）
2. 完善记忆更新时的评分重算（中优先级）
3. 清理残留的短期记忆代码（低优先级）

---

## 🎯 设计理念变更

### 原设计问题
- 使用 `session_id` 进行会话过滤，但对话历史已在messages中
- 短期记忆与messages内容重复，增加系统复杂度
- User、Session、Message、Configuration 等模型过于臃肿
- 无法支持多人格/多场景的记忆隔离

### 新设计理念（极简架构）
- **单一部署者模式**：项目只对部署者服务，不需要多用户系统
- **移除 User、Session、Message、Configuration**：这些模型全部删除
- **移除 session_id**：对话历史由下游软件通过messages参数传递
- **移除短期记忆**：专注于长期记忆的存储和检索
- **引入记忆体（Persona）概念**：支持多人格/多场景的记忆隔离
- **单层过滤机制**：仅使用 `persona_id` 进行记忆过滤
- **API Key 仅作权限控制**：API Key 不绑定 Persona，只验证是否有访问权限
- **Persona 像模型一样调用**：通过 models 接口列出，在 chat/completions 中通过参数指定

### 记忆体（Persona）概念
记忆体是独立的记忆空间，类似于"人格"或"角色"：
- 工作助手：存储工作相关的知识、项目信息
- 学习伙伴：存储学习笔记、知识点
- 生活助手：存储个人偏好、生活习惯

每个记忆体有：
- 独立的记忆空间（完全隔离）
- 可选的专属system prompt
- 像大模型一样，通过 models 接口列出和调用

### 设计简化
- **不需要用户概念**：记忆体本身就是独立的实体
- **不需要会话概念**：对话由下游软件管理
- **不需要消息存储**：messages由客户端传递
- **不需要配置表**：配置在 config.py 中管理
- **API Key 仅作权限控制**：不绑定 Persona，只验证访问权限
- **记忆体像模型一样调用**：通过 `persona` 参数指定使用哪个记忆体

### 数据模型（极简）
```
Persona (记忆体)
  - id
  - name
  - description
  - system_prompt
  - created_at
  - updated_at

Memory (长期记忆)
  - id
  - persona_id (外键)
  - vector_id
  - entity_id
  - content
  - created_at
  - last_accessed_at
  - access_count
  - score
  - metadata
```

### 配置管理
```
config.py
  - API_KEY: 全局访问密钥（用于权限控制）
  - DEFAULT_PERSONA_ID: 默认记忆体ID
```

---

## 记忆注入实现情况分析

### ✅ 已实现的功能

#### 1. 核心引擎 (`MemoryEngine`)
- 记忆检索：`retrieve_memories()` 方法支持检索长期记忆（已移除短期记忆）
- 记忆注入：`inject_memory()` 支持三种注入模式
  - `system` - 注入到system prompt
  - `messages` - 作为消息注入
  - `mixed` - 混合模式（等同于system模式）
- 记忆评分：`calculate_memory_score()` 计算综合评分（相似度、访问频率、时间衰减、图谱评分）
- 记忆体过滤：支持通过 `persona_id` 进行记忆空间隔离

#### 2. 检索策略 (`RetrievalStrategy`)
- 长期记忆检索：`_retrieve_long_term()` 从知识向量存储中检索，支持 `persona_id` 过滤
- 图谱增强：`_enhance_with_graph()` 使用图谱信息增强检索结果
- 图谱评分：`_calculate_graph_score()` 计算图谱评分
- 综合评分重排：`_rescore_with_memory_score()` 使用综合评分重新排序检索结果

#### 3. 记忆服务 (`MemoryService`)
- 记忆创建：`create_memory()` 创建记忆并存储到向量库和数据库
- 记忆搜索：`search_memories()` 搜索记忆并更新访问信息
- 记忆更新：`update_memory()` 更新记忆内容和元数据
- 记忆删除：`delete_memory()` 删除记忆（向量删除待完善）

#### 4. 记忆体服务 (`PersonaService`)
- 记忆体CRUD：完整的创建、查询、列表、更新、删除功能
- 记忆体管理：支持独立记忆空间的创建和管理

#### 5. API层
- `chat_completions`：集成记忆检索和注入到聊天补全接口，支持通过 `model` 参数指定记忆体
- `list_models`：`GET /v1/models` 列出所有可用的记忆体（像大模型一样）
- `persona_management`：完整的记忆体管理API（POST/GET/PUT/DELETE /v1/personas）
- API Key验证：全局API Key权限控制

#### 6. 存储层
- 向量存储：`VectorStore` 使用Milvus Lite进行向量存储和检索，支持 `persona_id` 过滤
- 图谱存储：`GraphStore` 使用KùzuDB进行图数据存储和查询
- 数据库存储：SQLite存储Persona和Memory元数据

#### 7. 配置系统 (`config.py`)
- 记忆配置：启用状态、最大长期记忆数量、注入模式
- 评分权重：相似度、访问频率、时间衰减、图谱评分的权重配置
- API配置：全局API_KEY、默认记忆体ID、LLM模型配置

---

## 🎯 优先级任务

### 🔴 高优先级

#### 1. 重构数据库模型（极简架构）✅ **已完成**
**设计目标**：
- 删除 `User`、`Session`、`Message`、`Configuration` 模型
- 添加 `Persona` 模型
- 修改 `Memory` 模型，添加 `persona_id` 字段
- 实现单层过滤机制：仅使用 `persona_id`

**已完成的文件**：
- [x] `models/database.py` - 已删除旧模型；已添加 Persona；已在 Memory 中添加 persona_id 外键
- [x] `models/schemas.py` - 已添加 PersonaCreate, PersonaUpdate, PersonaResponse
- [x] `services/chat_service.py` - 已删除（如果存在的话）

**数据模型设计**：
```
Persona (记忆体)
  - id
  - name (记忆体名称)
  - description (记忆体描述)
  - system_prompt (专属system prompt)
  - created_at
  - updated_at

Memory (长期记忆)
  - id
  - persona_id (外键，关联到Persona)
  - vector_id
  - entity_id
  - type (仅保留 long_term)
  - content
  - created_at
  - last_accessed_at
  - access_count
  - score
  - metadata
```

---

#### 2. 重构记忆过滤机制（仅记忆体过滤）✅ **已完成**
**设计目标**：
- 移除 `session_id`，不使用会话过滤
- 引入"记忆体"（Persona）概念，支持记忆体过滤
- API Key 仅作权限控制，不绑定 Persona

**已完成的文件**：
- [x] `memory/vector_store.py` - 已添加 `persona_id` 字段，实现硬过滤
- [x] `memory/retrieval.py` - 已支持 `persona_id` 过滤
- [x] `core/memory_engine.py` - `retrieve_memories()` 已接收 `persona_id`
- [x] `api/chat.py` - 已从 `model` 参数获取 `persona_id`，已集成 API Key 验证
- [x] `api/models.py` - 已实现列出所有可用记忆体作为 "models"
- [x] `config.py` - 已添加全局 API_KEY 和 DEFAULT_PERSONA_ID 配置

**API设计**：
```
GET /v1/models
Headers:
  X-API-Key: {api_key}

Response:
{
  "object": "list",
  "data": [
    {
      "id": "persona-1",
      "object": "model",
      "created": 1234567890,
      "owned_by": "you"
    },
    {
      "id": "persona-2",
      "object": "model",
      "created": 1234567890,
      "owned_by": "you"
    }
  ]
}

POST /v1/chat/completions
Headers:
  X-API-Key: {api_key}

Body:
{
  "model": "persona-1",  // 使用model参数指定记忆体
  "messages": [...]
}
```

**说明**：
- `model` 参数用于指定记忆体 ID（如 `persona-1`）
- LLM 模型名称在 `config.py` 中配置（`LLM_MODEL`）
- 如果不指定 `model` 参数，则使用默认记忆体（`DEFAULT_PERSONA_ID`）
- 这样设计完全兼容 OpenAI 风格的 API 调用方式

---

#### 3. 移除短期记忆相关逻辑 ✅ **已完成**
**原因**：
- 对话历史已在messages中，下游软件已发送完整对话
- LLM有上下文窗口，可直接处理历史消息
- 短期记忆与messages内容重复，增加系统复杂度

**已完成的文件**：
- [x] `core/memory_engine.py` - 已精简，仅保留长期记忆注入逻辑
- [x] `memory/retrieval.py` - 已移除 `_retrieve_short_term()` 方法
- [ ] `config.py` - 仍保留 MEMORY_MAX_SHORT_TERM 配置（可选清理）
- [ ] `memory/vector_store.py` - 仍保留 session 集合（可选清理）

---

#### 4. 记忆评分充分利用 ✅ **已完成**
**问题**：`RetrievalStrategy._retrieve_long_term()` 需要使用综合评分重新排序记忆

**已完成的文件**：
- [x] `memory/retrieval.py` - 已实现 `_rescore_with_memory_score()` 综合评分排序

---

### 🟡 中优先级

#### 5. 实现记忆体管理API ✅ **已完成**
**问题**：需要提供记忆体的完整CRUD接口

**已完成的文件**：
- [x] `models/database.py` - 已添加 `Persona` 模型
- [x] `models/schemas.py` - 已添加 `PersonaCreate`, `PersonaUpdate`, `PersonaResponse` schema
- [x] `api/models.py` - 已实现 `GET /v1/models` 列出记忆体
- [x] `services/persona_service.py` - 已实现完整的 Persona CRUD 服务
- [x] `api/persona.py` - 已实现以下接口：
  - POST   /v1/personas           # 创建记忆体
  - GET    /v1/personas           # 列出所有记忆体  
  - GET    /v1/personas/{id}      # 获取记忆体详情
  - PUT    /v1/personas/{id}      # 更新记忆体
  - DELETE /v1/personas/{id}      # 删除记忆体

**数据模型设计**：
```
Persona:
  - id
  - name (记忆体名称，如"工作助手"、"学习伙伴")
  - description (记忆体描述)
  - system_prompt (记忆体专属的system prompt)
  - created_at
  - updated_at
```

**API设计**：
```
POST   /v1/personas           # 创建记忆体
GET    /v1/personas           # 列出所有记忆体
GET    /v1/personas/{id}      # 获取记忆体详情
PUT    /v1/personas/{id}      # 更新记忆体
DELETE /v1/personas/{id}      # 删除记忆体
```

---

#### 6. 记忆删除功能不完整 ❌ **待完成**
**问题**：`MemoryService.delete_memory()` 中向量删除逻辑标记为 TODO

**需要修改的文件**：
- [ ] `services/memory_service.py` - 实现向量存储的删除功能（第178行）
- [ ] `memory/vector_store.py` - 添加 `delete_knowledge()` 和 `delete_session()` 方法

---

#### 7. 记忆更新未更新评分 ❌ **待完成**
**问题**：`MemoryService.update_memory()` 更新记忆内容后未重新计算评分

**需要修改的文件**：
- [ ] `services/memory_service.py` - 更新记忆后重新计算并更新记忆评分（第136-144行）

---

#### 7. 检索结果排序优化
**问题**：检索结果仅按向量相似度排序，未使用综合评分

**需要修改的文件**：
- [ ] `memory/retrieval.py` - 使用综合评分重新排序检索结果

---

### 🟢 低优先级

#### 8. 清理残留的短期记忆代码 ⚠️ **建议清理**
**问题**：虽然逻辑上已移除短期记忆，但代码中仍保留了一些相关代码

**需要修改的文件**：
- [ ] `config.py` - 移除 `MEMORY_MAX_SHORT_TERM` 配置（如果存在）
- [ ] `memory/vector_store.py` - 可以保留session集合（用于其他用途），但建议添加注释说明
- [ ] `models/schemas.py` - 检查并移除短期记忆相关schema定义

---

#### 9. 缺少对话记忆持久化
**问题**：对话完成后没有自动将对话内容存储为记忆

**需要修改的文件**：
- [ ] `api/chat.py` - 在对话完成后，自动将重要的对话内容转换为记忆并存储
- [ ] `services/memory_service.py` - 添加智能记忆提取逻辑（识别重要信息）

---

#### 10. 缺少记忆过期和清理机制
**问题**：没有实现记忆的过期和自动清理机制

**需要修改的文件**：
- [ ] `services/memory_service.py` - 实现记忆过期策略
- [ ] `utils/` - 添加定时任务，定期清理低分或长期未访问的记忆

---

## 📋 配置参数（当前设置）

### 记忆系统配置

| 参数 | 值 | 说明 |
|------|-----|------|
| `MEMORY_ENABLED` | `True` | 记忆功能启用 |
| `MEMORY_MAX_LONG_TERM` | `3` | 最大长期记忆数量 |
| `MEMORY_INJECTION_MODE` | `"system"` | 注入模式（system/messages/mixed） |
| `MEMORY_SCORE_SIMILARITY_WEIGHT` | `0.4` | 相似度权重 |
| `MEMORY_SCORE_ACCESS_WEIGHT` | `0.3` | 访问频率权重 |
| `MEMORY_SCORE_RECENCY_WEIGHT` | `0.2` | 时间衰减权重 |
| `MEMORY_SCORE_GRAPH_WEIGHT` | `0.1` | 图谱评分权重 |
| `MEMORY_RECENCY_DECAY_LAMBDA` | `0.0001` | 毫秒级衰减系数 |

### API配置

| 参数 | 值 | 说明 |
|------|-----|------|
| `API_KEY` | `""` | 全局API Key（用于权限控制） |
| `DEFAULT_PERSONA_ID` | `"default"` | 默认记忆体ID |

### LLM配置

| 参数 | 值 | 说明 |
|------|-----|------|
| `LLM_BASE_URL` | `https://api.siliconflow.com/v1` | LLM API基础URL |
| `LLM_API_KEY` | `sk-***` | LLM API密钥 |
| `LLM_MODEL` | `deepseek-ai/DeepSeek-V3.2` | LLM模型名称 |
| `LLM_TIMEOUT` | `60` | LLM请求超时时间（秒） |

### Embedding配置

| 参数 | 值 | 说明 |
|------|-----|------|
| `EMBEDDING_BASE_URL` | `https://api.siliconflow.com/v1` | Embedding API基础URL |
| `EMBEDDING_API_KEY` | `sk-***` | Embedding API密钥 |
| `EMBEDDING_MODEL` | `BAAI/bge-m3` | Embedding模型名称 |
| `EMBEDDING_DIMENSIONS` | `1024` | 向量维度 |
| `EMBEDDING_TIMEOUT` | `30` | Embedding请求超时时间（秒） |

### 存储配置

| 参数 | 值 | 说明 |
|------|-----|------|
| `MILVUS_URI` | `./data/milvus/milvus.db` | Milvus Lite数据库路径 |
| `MILVUS_COLLECTION_KNOWLEDGE` | `knowledge_vectors` | 知识向量集合名称 |
| `MILVUS_COLLECTION_SESSION` | `session_vectors` | 会话向量集合名称（保留） |
| `MILVUS_TOP_K` | `10` | 检索返回数量 |
| `KUZU_DB_PATH` | `./data/kuzu/kuzu.db` | KùzuDB数据库路径 |
| `SQLITE_DB_PATH` | `./data/mempoint.db` | SQLite数据库路径 |

### 待添加的配置参数（可选）

| 参数 | 建议值 | 说明 |
|------|--------|------|
| `MEMORY_AUTO_SAVE_ENABLED` | `True` | 是否自动保存对话为记忆 |
| `MEMORY_AUTO_SAVE_THRESHOLD` | `0.7` | 自动保存的记忆重要性阈值 |

---

## 📝 代码结构说明

```
backend/
├── core/
│   ├── memory_engine.py      # 记忆注入引擎（核心）
│   ├── embedding_client.py   # 向量化客户端
│   ├── llm_client.py         # LLM客户端
│   └── response_adapter.py   # 响应适配器
├── memory/
│   ├── memory_manager.py     # 记忆管理器（CRUD）
│   ├── vector_store.py       # 向量存储（Milvus），支持persona_id过滤
│   ├── graph_store.py        # 图谱存储（KùzuDB）
│   └── retrieval.py          # 检索策略，综合评分重排序
├── services/
│   ├── memory_service.py     # 记忆服务
│   └── persona_service.py    # 记忆体服务（已实现）
├── api/
│   ├── chat.py               # 聊天API（记忆注入入口）
│   ├── models.py             # 模型列表API（列出可用的记忆体）
│   └── persona.py            # 记忆体管理API（已实现）
├── models/
│   ├── database.py           # 数据库模型（Persona + Memory）
│   └── schemas.py            # Pydantic模型（Persona + Memory相关）
├── utils/
│   ├── cache.py              # 缓存工具
│   ├── helpers.py            # 辅助函数
│   └── logger.py             # 日志工具
└── config.py                 # 配置文件（已添加API_KEY和DEFAULT_PERSONA_ID）
```

### 已删除的文件
- `services/chat_service.py` - 不再需要会话服务（已删除）

### 已实现的文件说明

#### `services/persona_service.py` ✅
- 记忆体CRUD操作
- 记忆体与记忆的关联

#### `api/models.py` ✅
- GET /v1/models - 列出所有可用的记忆体（像大模型一样）

#### `api/persona.py` ✅
- POST /v1/personas - 创建记忆体
- GET /v1/personas - 列出所有记忆体
- GET /v1/personas/{id} - 获取记忆体详情
- PUT /v1/personas/{id} - 更新记忆体
- DELETE /v1/personas/{id} - 删除记忆体

---

## 🔄 记忆注入流程（极简设计）

1. **API入口**：`api/chat.py` 的 `chat_completions()` 接收请求
2. **权限验证**：从 `X-API-Key` header 提取 `api_key`，验证是否有访问权限
3. **获取记忆体ID**：从请求的 `model` 参数获取 `persona_id`（可选，默认使用 `DEFAULT_PERSONA_ID`）
4. **记忆检索**：调用 `memory_engine.retrieve_memories(query, persona_id)` 检索相关记忆
    - 将查询文本向量化
    - 使用单层过滤：`persona_id`（Milvus硬过滤）
    - 图谱增强：从KùzuDB获取实体关联信息
    - 综合评分重排序：相似度、访问频率、时间衰减、图谱评分
5. **记忆注入**：调用 `memory_engine.inject_memory()` 将记忆注入到消息中
    - 支持三种注入模式：system、messages、mixed
6. **LLM调用**：使用增强后的消息调用LLM（配置的 `LLM_MODEL`）
7. **响应返回**：返回LLM响应（OpenAI兼容格式）
8. **自动保存**（待实现）：将重要对话内容自动保存为记忆

### 记忆过滤逻辑

```
客户端请求 (api_key + model参数指定persona_id + messages)
    ↓
验证 api_key 权限
    ↓
从 model 参数获取 persona_id（或使用 DEFAULT_PERSONA_ID）
    ↓
将查询文本向量化
    ↓
Milvus检索：WHERE persona_id = ?（硬过滤）
    ↓
KùzuDB图谱增强：获取实体关联信息
    ↓
综合评分重排序：相似度 + 访问频率 + 时间衰减 + 图谱评分
    ↓
注入记忆到 LLM 上下文
    ↓
调用上游LLM（配置的 LLM_MODEL）
    ↓
返回 LLM 响应（OpenAI兼容格式）
```

### 记忆体隔离

每个记忆体是完全独立的记忆空间：
- 记忆体1 ≠ 记忆体2
- 记忆体1 ≠ 记忆体3

这样可以实现：
- 不同场景使用不同记忆体（工作/学习/生活）
- 不同人格/角色使用不同记忆体
- 完全的数据隔离和隐私保护
- 像选择大模型一样选择记忆体

### 极简架构优势

- **单一部署者**：项目只对部署者服务，不需要多用户系统
- **无会话管理**：对话历史由下游软件通过 messages 参数传递
- **无消息存储**：不存储对话消息，只存储长期记忆
- **无配置表**：配置在 config.py 中管理
- **记忆体即身份**：通过 persona_id 访问对应的记忆空间
- **OpenAI兼容**：完全兼容OpenAI API风格，可直接使用现有客户端
- **三重存储架构**：Milvus Lite（语义向量）+ KùzuDB（知识图谱）+ SQLite（元数据）
- **智能评分机制**：综合相似度、访问频率、时间衰减、图谱关联度进行记忆排序

---

## 📊 长期记忆的价值

长期记忆才是真正需要检索和存储的内容：
- 跨会话的重要信息
- 部署者的偏好和习惯
- 历史对话中的关键知识点
- 实体和概念关联

这些信息不会包含在messages中，需要从向量存储中检索并注入。

### 记忆体的价值

记忆体（Persona）机制提供了更细粒度的记忆管理：

1. **场景隔离**
   - 工作记忆体：存储工作相关的知识、项目信息
   - 学习记忆体：存储学习笔记、知识点
   - 生活记忆体：存储个人偏好、生活习惯

2. **人格隔离**
   - 不同人格可以有完全不同的记忆
   - 支持多角色对话场景
   - 保护隐私，不同人格间数据隔离

3. **灵活切换**
    - 像选择大模型一样选择记忆体
    - 每个记忆体有独立的system prompt
    - 支持定制化的AI助手体验

4. **极简设计**
     - 不需要用户概念
     - 不需要会话概念
     - 不需要消息存储
     - API Key 仅作权限控制
     - 记忆体像模型一样列出和调用
     - 单一部署者，无需复杂权限管理

---

## 🎉 项目总结

### 当前完成度：约 85%

#### 已完成的核心功能 ✅
1. **架构重构**：成功从多用户/多会话模式转型为单用户/多人格模式
2. **记忆体系统**：完整的Persona CRUD API和数据库模型
3. **记忆注入引擎**：基于`persona_id`的长期记忆检索和注入
4. **综合评分机制**：四维度评分（相似度、访问频率、时间衰减、图谱评分）
5. **OpenAI兼容API**：标准的`/v1/models`和`/v1/chat/completions`接口
6. **三重存储架构**：Milvus Lite + KùzuDB + SQLite完全集成
7. **权限控制**：全局API Key验证机制

#### 待完善的功能 ⚠️
1. **记忆删除**：向量库删除逻辑待实现（`services/memory_service.py:178`）
2. **记忆更新评分**：更新记忆内容后未重新计算评分（`services/memory_service.py:136-144`）
3. **代码清理**：残留的短期记忆配置和代码建议清理

#### 可选增强功能 🚀
1. **对话记忆持久化**：自动将重要对话内容保存为记忆
2. **记忆过期清理**：定期清理低分或长期未访问的记忆
3. **智能记忆提取**：识别并提取对话中的重要信息

### 技术亮点 ⭐
- **Persona-as-a-Model**：创新地将记忆体抽象为"模型"，完全兼容OpenAI API
- **硬过滤机制**：Milvus中使用`persona_id`进行硬过滤，确保记忆空间完全隔离
- **图谱增强**：KùzuDB提供实体关联信息，增强检索的语义理解
- **综合评分**：多维度评分机制，确保检索结果的相关性和质量

### 使用场景 📚
1. **工作助手**：存储工作相关的知识、项目信息、会议记录
2. **学习伙伴**：存储学习笔记、知识点、概念关联
3. **生活助手**：存储个人偏好、生活习惯、日程安排
4. **角色扮演**：不同人格可以有完全不同的记忆和system prompt

### 下一步建议 💡
1. **高优先级**：实现向量库删除功能，确保数据一致性
2. **中优先级**：完善记忆更新时的评分重算逻辑
3. **低优先级**：清理残留的短期记忆代码，保持代码整洁
4. **可选**：实现对话记忆持久化和智能记忆提取功能

---

**最后更新时间**：2026-02-04
**项目状态**：核心功能已完成，待完善细节功能
**推荐使用场景**：个人AI助手、知识管理、角色扮演对话
