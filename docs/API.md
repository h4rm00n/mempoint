# MemPoint API 接口文档

## 认证

所有 API（除根路径和健康检查外）都需要在请求头中携带 API Key：

```
Authorization: Bearer your-api-key
```

---

## 基础信息

| 项目 | 值 |
|------|-----|
| 基础路径 | `/v1` |
| 内容类型 | `application/json` |

---

## 1. Chat Completions API

### 1.1 聊天补全

**端点**: `POST /v1/chat/completions`

**描述**: OpenAI 风格的聊天补全接口，支持记忆注入、流式传输和工具调用

**请求头**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| Authorization | string | 是 | Bearer token 认证 |

**请求体**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| model | string | 是 | 记忆体 ID（如 "persona-1"）或记忆体与LLM模型的组合（如 "persona-1/deepseek-ai/DeepSeek-V3.2"）。如果只提供记忆体ID，则使用默认LLM模型 |
| messages | array | 是 | 消息列表，每个消息包含 role 和 content |
| temperature | number | 否 | 温度参数，默认 0.7 |
| max_tokens | integer | 否 | 最大 token 数，默认 1000 |
| stream | boolean | 否 | 是否流式输出，默认 false |
| tools | array | 否 | 工具列表，每个工具包含 type 和 function |
| tool_choice | any | 否 | 工具选择策略，如 "auto"、"none" 或具体工具 |
| memory_config | object | 否 | 记忆配置，包含 enabled 和 max_long_term |

**消息格式**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| role | string | 是 | 消息角色，如 "user"、"assistant"、"system"、"tool" |
| content | string | 否 | 消息内容 |
| tool_calls | array | 否 | 工具调用列表（assistant 消息） |
| tool_call_id | string | 否 | 工具调用 ID（tool 消息） |

**工具格式**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| type | string | 是 | 工具类型，固定为 "function" |
| function | object | 是 | 函数定义，包含 name、description、parameters |

**响应** (非流式):
```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "deepseek-ai/DeepSeek-V3.2",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "回复内容",
        "tool_calls": null
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

**响应** (流式): Server-Sent Events (SSE) 格式

---

## 2. Completions API

### 2.1 文本补全

**端点**: `POST /v1/completions`

**描述**: OpenAI 风格的文本补全接口

**请求头**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| Authorization | string | 是 | Bearer token 认证 |

**请求体**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| prompt | string | 是 | 提示文本 |
| model | string | 是 | 模型名称 |
| temperature | number | 否 | 温度参数 |
| max_tokens | integer | 否 | 最大 token 数 |
| stream | boolean | 否 | 是否流式输出 |

**响应**: 与 Chat Completions 相同格式

---

## 3. Models API

### 3.1 列出模型

**端点**: `GET /v1/models`

**描述**: 返回所有可用的模型（记忆体与LLM模型的组合），格式为 "persona_id/llm_model"

**请求头**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| Authorization | string | 是 | Bearer token 认证 |

**响应**:
```json
{
  "object": "list",
  "data": [
    {
      "id": "persona-1/deepseek-ai/DeepSeek-V3.2",
      "object": "model",
      "created": 1234567890,
      "owned_by": "you"
    }
  ]
}
```

---

## 4. Persona API

### 4.1 创建记忆体

**端点**: `POST /v1/personas`

**请求头**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| Authorization | string | 是 | Bearer token 认证 |

**请求体**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| name | string | 是 | 记忆体名称 |
| description | string | 否 | 记忆体描述 |
| system_prompt | string | 否 | 记忆体专属的 system prompt |

**响应**:
```json
{
  "id": "persona-xxx",
  "name": "工作助手",
  "description": "工作场景的记忆体",
  "system_prompt": "你是一个专业的工作助手...",
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

### 4.2 列出所有记忆体

**端点**: `GET /v1/personas`

**请求头**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| Authorization | string | 是 | Bearer token 认证 |

**响应**: 记忆体数组

### 4.3 获取记忆体详情

**端点**: `GET /v1/personas/{persona_id}`

**路径参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| persona_id | string | 是 | 记忆体 ID |

**请求头**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| Authorization | string | 是 | Bearer token 认证 |

**响应**: 单个记忆体对象

### 4.4 更新记忆体

**端点**: `PUT /v1/personas/{persona_id}`

**路径参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| persona_id | string | 是 | 记忆体 ID |

**请求头**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| Authorization | string | 是 | Bearer token 认证 |

**请求体**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| name | string | 否 | 记忆体名称 |
| description | string | 否 | 记忆体描述 |
| system_prompt | string | 否 | 记忆体专属的 system prompt |

**响应**: 更新后的记忆体对象

### 4.5 删除记忆体

**端点**: `DELETE /v1/personas/{persona_id}`

**路径参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| persona_id | string | 是 | 记忆体 ID |

**请求头**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| Authorization | string | 是 | Bearer token 认证 |

**响应**:
```json
{
  "message": "Persona deleted successfully"
}
```

---

## 5. Config API

### 5.1 获取系统配置

**端点**: `GET /v1/config`

**描述**: 获取系统配置

**请求头**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| Authorization | string | 是 | Bearer token 认证 |

**响应**:
```json
{
  "llm": {},
  "embedding": {},
  "memory_extraction": {},
  "memory_system": {},
  "memory_scoring": {},
  "milvus": {},
  "kuzu": {},
  "cache": {}
}
```

### 5.2 更新系统配置

**端点**: `PUT /v1/config`

**描述**: 更新系统配置

**请求头**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| Authorization | string | 是 | Bearer token 认证 |

**请求体**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| llm | object | 否 | LLM 配置 |
| embedding | object | 否 | Embedding 配置 |
| memory_extraction | object | 否 | 记忆提取配置 |
| memory_system | object | 否 | 记忆系统配置 |
| memory_scoring | object | 否 | 记忆评分配置 |
| milvus | object | 否 | Milvus 配置 |
| kuzu | object | 否 | KùzuDB 配置 |
| cache | object | 否 | 缓存配置 |

**响应**: 更新后的系统配置

### 5.3 根据配置键获取配置

**端点**: `GET /v1/config/{config_key}`

**描述**: 根据配置键获取配置

**路径参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| config_key | string | 是 | 配置键 |

**请求头**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| Authorization | string | 是 | Bearer token 认证 |

**响应**: 配置值对象

### 5.4 根据配置键更新配置

**端点**: `PUT /v1/config/{config_key}`

**描述**: 根据配置键更新配置

**路径参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| config_key | string | 是 | 配置键 |

**请求头**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| Authorization | string | 是 | Bearer token 认证 |

**请求体**: 配置值对象

**响应**: 更新后的配置值

### 5.5 列出所有配置

**端点**: `GET /v1/config/list`

**描述**: 列出所有配置

**请求头**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| Authorization | string | 是 | Bearer token 认证 |

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| user_id | string | 否 | 用户ID，默认为 "system" |

**响应**: 配置数组

### 5.6 创建新配置

**端点**: `POST /v1/config`

**描述**: 创建新配置

**请求头**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| Authorization | string | 是 | Bearer token 认证 |

**请求体**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| user_id | string | 是 | 用户ID |
| config_key | string | 是 | 配置键 |
| config_value | object | 是 | 配置值 |
| description | string | 否 | 配置描述 |

**响应**: 创建的配置对象

### 5.7 删除配置

**端点**: `DELETE /v1/config/{config_id}`

**描述**: 删除配置

**路径参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| config_id | string | 是 | 配置ID |

**请求头**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| Authorization | string | 是 | Bearer token 认证 |

**响应**:
```json
{
  "message": "Configuration deleted successfully"
}
```

### 5.8 重新初始化配置

**端点**: `POST /v1/config/reinitialize`

**描述**: 重新初始化配置，将默认配置重新写入数据库（仅更新不存在的配置）

**请求头**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| Authorization | string | 是 | Bearer token 认证 |

**响应**:
```json
{
  "message": "Configurations reinitialized successfully"
}
```

---

## 6. Memory API

### 6.1 创建记忆

**端点**: `POST /v1/memories`

**描述**: 创建一条新的记忆

**请求头**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| Authorization | string | 是 | Bearer token 认证 |

**请求体**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| persona_id | string | 是 | 记忆体 ID |
| content | string | 是 | 记忆内容 |
| type | string | 是 | 记忆类型（如 "long_term"） |
| entity_id | string | 否 | 关联的实体 ID |
| metadata | object | 否 | 其他元数据 |

**响应**:
```json
{
  "id": "memory-xxx",
  "persona_id": "persona-1",
  "vector_id": "vector-xxx",
  "entity_id": null,
  "type": "long_term",
  "content": "记忆内容",
  "created_at": "2024-01-01T00:00:00",
  "last_accessed_at": "2024-01-01T00:00:00",
  "access_count": 0,
  "score": 0.0,
  "metadata": {}
}
```

### 6.2 列出记忆

**端点**: `GET /v1/memories`

**描述**: 列出记忆，支持按记忆体和类型过滤

**请求头**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| Authorization | string | 是 | Bearer token 认证 |

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| persona_id | string | 否 | 记忆体 ID，用于过滤 |
| type | string | 否 | 记忆类型，用于过滤 |
| limit | integer | 否 | 返回数量限制，默认 100，最大 1000 |

**响应**: 记忆数组

### 6.3 获取记忆详情

**端点**: `GET /v1/memories/{memory_id}`

**描述**: 获取指定记忆的详细信息

**路径参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| memory_id | string | 是 | 记忆 ID |

**请求头**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| Authorization | string | 是 | Bearer token 认证 |

**响应**: 单个记忆对象

### 6.4 更新记忆

**端点**: `PUT /v1/memories/{memory_id}`

**描述**: 更新记忆的内容或元数据

**路径参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| memory_id | string | 是 | 记忆 ID |

**请求头**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| Authorization | string | 是 | Bearer token 认证 |

**请求体**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| content | string | 否 | 新的记忆内容 |
| metadata | object | 否 | 新的元数据 |

**响应**: 更新后的记忆对象

### 6.5 删除记忆

**端点**: `DELETE /v1/memories/{memory_id}`

**描述**: 删除指定的记忆（包括向量存储和数据库记录）

**路径参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| memory_id | string | 是 | 记忆 ID |

**请求头**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| Authorization | string | 是 | Bearer token 认证 |

**响应**: 204 No Content

### 6.6 搜索记忆

**端点**: `POST /v1/memories/search`

**描述**: 基于语义搜索相关记忆

**请求头**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| Authorization | string | 是 | Bearer token 认证 |

**请求体**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| query | string | 是 | 搜索查询 |
| top_k | integer | 否 | 返回结果数量，默认 10 |
| metadata | object | 否 | 元数据过滤条件 |

**响应**: 搜索结果数组，包含记忆内容和相似度评分

---

## 7. Memory Tools API

### 7.1 获取记忆工具定义

**端点**: `GET /v1/memory-tools`

**描述**: 返回所有可用的记忆管理工具定义，这些工具可以传递给 LLM 的 `tools` 参数，让 LLM 主动调用

**请求头**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| Authorization | string | 是 | Bearer token 认证 |

**响应**:
```json
{
  "object": "list",
  "data": [
    {
      "type": "function",
      "function": {
        "name": "save_memory",
        "description": "记住用户提到的重要事实、偏好或背景信息，以便在未来的对话中参考。",
        "parameters": {
          "type": "object",
          "properties": {
            "content": {
              "type": "string",
              "description": "需要记住的具体信息内容，例如：'用户喜欢喝红茶' 或 '用户的生日是5月12日'。"
            },
            "entity_id": {
              "type": "string",
              "description": "可选。如果这段记忆关联到特定的实体（人、地点、事物），可以指定实体名称。"
            },
            "importance": {
              "type": "integer",
              "description": "可选。记忆的重要性级别（1-10），默认为5。",
              "minimum": 1,
              "maximum": 10
            }
          },
          "required": ["content"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "update_memory",
        "description": "更新或修正之前记住的信息。当用户改变了主意或提供了更准确的信息时使用。",
        "parameters": {
          "type": "object",
          "properties": {
            "memory_id": {
              "type": "string",
              "description": "需要更新的记忆ID。你可以从之前的对话上下文或检索结果中获取此ID。"
            },
            "new_content": {
              "type": "string",
              "description": "修正后的完整信息内容。"
            }
          },
          "required": ["memory_id", "new_content"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "delete_memory",
        "description": "当某条记忆已经过期、错误或用户明确要求忘记时，使用此工具删除记忆。",
        "parameters": {
          "type": "object",
          "properties": {
            "memory_id": {
              "type": "string",
              "description": "需要删除的记忆ID。"
            },
            "reason": {
              "type": "string",
              "description": "可选。为什么要删除这条记忆的原因。"
            }
          },
          "required": ["memory_id"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "search_memories",
        "description": "主动搜索特定的历史记忆或知识。当需要更精确地核实某个事实时使用。",
        "parameters": {
          "type": "object",
          "properties": {
            "query": {
              "type": "string",
              "description": "搜索关键词或语义查询。"
            }
          },
          "required": ["query"]
        }
      }
    }
  ]
}
```

### 工具使用说明

#### 1. save_memory
- **用途**：记住用户提到的重要事实、偏好或背景信息
- **参数**：
  - `content`（必填）：需要记住的具体信息内容
  - `entity_id`（可选）：关联的实体名称
  - `importance`（可选）：记忆的重要性级别（1-10）
- **示例**：`save_memory(content="用户喜欢喝红茶", importance=7)`

#### 2. update_memory
- **用途**：更新或修正之前记住的信息
- **参数**：
  - `memory_id`（必填）：需要更新的记忆ID
  - `new_content`（必填）：修正后的完整信息内容
- **示例**：`update_memory(memory_id="memory-123", new_content="用户更喜欢喝绿茶而不是红茶")`

#### 3. delete_memory
- **用途**：删除过期、错误或用户明确要求忘记的记忆
- **参数**：
  - `memory_id`（必填）：需要删除的记忆ID
  - `reason`（可选）：删除原因
- **示例**：`delete_memory(memory_id="memory-123", reason="用户已改变主意")`

#### 4. search_memories
- **用途**：主动搜索特定的历史记忆或知识
- **参数**：
  - `query`（必填）：搜索关键词或语义查询
- **示例**：`search_memories(query="用户的生日")`

---

## 8. 自动记忆保存

### 8.1 功能说明

MemPoint 支持在对话结束后自动提取并保存重要记忆。这个功能通过后台任务实现，不会阻塞主响应。

### 8.2 配置参数

在 `Chat Completions API` 的 `memory_config` 中配置：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| enabled | boolean | true | 是否启用记忆检索和注入 |
| auto_save | boolean | true | 是否启用对话后自动保存记忆 |

**请求示例**：
```json
{
  "model": "persona-1",
  "messages": [
    {"role": "user", "content": "我的生日是5月12日"}
  ],
  "memory_config": {
    "enabled": true,
    "auto_save": true
  }
}
```

### 8.3 工作原理

1. **对话完成**：LLM 返回响应后，后台任务启动
2. **提取分析**：使用 LLM 分析对话内容，提取值得长期记住的信息
3. **智能判断**：只提取以下类型的信息：
   - 用户的重要偏好（如喜欢/不喜欢的东西）
   - 用户的重要事实（如生日、联系方式、工作信息）
   - 用户明确要求记住的信息
   - 对未来对话有帮助的关键信息
4. **自动保存**：将提取的信息保存为长期记忆

### 8.4 使用建议

- **启用自动保存**：适用于个人助手、知识管理等场景
- **禁用自动保存**：适用于临时对话、测试环境或需要完全手动控制的场景
- **结合工具调用**：LLM 可以同时使用自动保存和手动工具调用，实现更灵活的记忆管理

---

## 9. MCP (Model Context Protocol) API

### 9.1 MCP Streamable HTTP 端点

**端点**: `POST /v1/mcp`

**描述**: MCP Streamable HTTP 端点，基于 MCP Streamable HTTP 标准，支持 JSON-RPC 2.0 协议

**请求头**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| Authorization | string | 是 | Bearer token 认证 |
| Content-Type | string | 是 | application/json |

**请求体** (JSON-RPC 2.0 格式):
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {}
}
```

**支持的方法**:
| 方法 | 说明 |
|------|------|
| initialize | 初始化连接 |
| tools/list | 列出可用工具 |
| resources/list | 列出可用资源 |
| tools/call | 调用工具 |

**响应**: Server-Sent Events (SSE) 格式

**注意事项**:
- 通知类型的请求（没有 id 字段）不会返回响应数据
- 响应使用 SSE 格式，事件类型为 `message` 和 `end`

### 9.2 获取MCP服务器信息

**端点**: `GET /v1/mcp/info`

**描述**: 获取 MCP 服务器的基本信息和协议版本

**请求头**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| Authorization | string | 是 | Bearer token 认证 |

**响应**:
```json
{
  "name": "MemPoint Memory Server",
  "version": "0.1.0",
  "protocolVersion": "2024-11-05"
}
```

### 9.3 列出MCP工具

**端点**: `GET /v1/mcp/tools`

**描述**: 列出所有可用的 MCP 工具，这些工具可以通过 MCP 协议被 LLM 调用

**请求头**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| Authorization | string | 是 | Bearer token 认证 |

**响应**:
```json
{
  "tools": [
    {
      "name": "save_memory",
      "description": "记住用户提到的重要事实、偏好或背景信息，以便在未来的对话中参考。",
      "inputSchema": {
        "type": "object",
        "properties": {
          "content": {
            "type": "string",
            "description": "需要记住的具体信息内容，例如：'用户喜欢喝红茶' 或 '用户的生日是5月12日'。"
          },
          "entity_id": {
            "type": "string",
            "description": "可选。如果这段记忆关联到特定的实体（人、地点、事物），可以指定实体名称。"
          },
          "importance": {
            "type": "integer",
            "description": "可选。记忆的重要性级别（1-10），默认为5。",
            "minimum": 1,
            "maximum": 10
          }
        },
        "required": ["content"]
      }
    },
    {
      "name": "update_memory",
      "description": "更新或修正之前记住的信息。当用户改变了主意或提供了更准确的信息时使用。",
      "inputSchema": {
        "type": "object",
        "properties": {
          "memory_id": {
            "type": "string",
            "description": "需要更新的记忆ID。你可以从之前的对话上下文或检索结果中获取此ID。"
          },
          "new_content": {
            "type": "string",
            "description": "修正后的完整信息内容。"
          }
        },
        "required": ["memory_id", "new_content"]
      }
    },
    {
      "name": "delete_memory",
      "description": "当某条记忆已经过期、错误或用户明确要求忘记时，使用此工具删除记忆。",
      "inputSchema": {
        "type": "object",
        "properties": {
          "memory_id": {
            "type": "string",
            "description": "需要删除的记忆ID。"
          },
          "reason": {
            "type": "string",
            "description": "可选。为什么要删除这条记忆的原因。"
          }
        },
        "required": ["memory_id"]
      }
    },
    {
      "name": "search_memories",
      "description": "主动搜索特定的历史记忆或知识。当需要更精确地核实某个事实时使用。",
      "inputSchema": {
        "type": "object",
        "properties": {
          "query": {
            "type": "string",
            "description": "搜索关键词或语义查询。"
          }
        },
        "required": ["query"]
      }
    }
  ]
}
```

### 9.4 列出MCP资源

**端点**: `GET /v1/mcp/resources`

**描述**: 列出所有可用的 MCP 资源，这些资源可以通过 MCP 协议被 LLM 访问

**请求头**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| Authorization | string | 是 | Bearer token 认证 |

**响应**:
```json
{
  "resources": [
    {
      "uri": "memory://list",
      "name": "列出记忆",
      "description": "列出所有记忆，支持按记忆体和类型过滤"
    },
    {
      "uri": "memory://get",
      "name": "获取记忆详情",
      "description": "根据记忆ID获取详细信息"
    },
    {
      "uri": "memory://search",
      "name": "搜索记忆",
      "description": "基于语义搜索相关记忆"
    }
  ]
}
```

### 9.5 调用MCP工具

**端点**: `POST /v1/mcp/tools/{tool_name}`

**描述**: 调用指定的 MCP 工具

**路径参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| tool_name | string | 是 | 工具名称（save_memory、update_memory、delete_memory、search_memories） |

**请求头**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| Authorization | string | 是 | Bearer token 认证 |

**请求体**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|--------|------|
| arguments | object | 是 | 工具参数，根据不同工具有不同的参数 |

**响应**:
```json
{
  "success": true,
  "memory_id": "memory-xxx",
  "message": "记忆已保存"
}
```

---

## 10. 系统接口

### 10.1 根路径

**端点**: `GET /`

**描述**: 欢迎信息和 API 概览

**响应**:
```json
{
  "message": "Welcome to MemPoint API",
  "version": "0.1.0",
  "docs": "/docs",
  "health": "/health"
}
```

### 10.2 健康检查

**端点**: `GET /health`

**描述**: 服务健康状态检查

**响应**:
```json
{
  "status": "healthy",
  "service": "MemPoint"
}
```

---

## 数据类型说明

### PersonaCreate
| 字段 | 类型 | 说明 |
|------|------|------|
| name | string | 记忆体名称 |
| description | string | 记忆体描述 |
| system_prompt | string | 记忆体专属的 system prompt |

### PersonaUpdate
| 字段 | 类型 | 说明 |
|------|------|------|
| name | string | 记忆体名称 |
| description | string | 记忆体描述 |
| system_prompt | string | 记忆体专属的 system prompt |

### PersonaResponse
| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 记忆体 ID |
| name | string | 记忆体名称 |
| description | string | 记忆体描述 |
| system_prompt | string | 记忆体专属的 system prompt |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### ChatMessage
| 字段 | 类型 | 说明 |
|------|------|------|
| role | string | 消息角色 |
| content | string | 消息内容 |
| tool_calls | array | 工具调用列表 |
| tool_call_id | string | 工具调用 ID |

### Tool
| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 工具类型，固定为 "function" |
| function | object | 函数定义 |

### ToolFunction
| 字段 | 类型 | 说明 |
|------|------|------|
| name | string | 函数名称 |
| description | string | 函数描述 |
| parameters | object | 函数参数（JSON Schema） |

### ToolCall
| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 工具调用 ID |
| type | string | 工具调用类型，固定为 "function" |
| function | object | 函数调用信息 |

### ChatCompletionRequest
| 字段 | 类型 | 说明 |
|------|------|------|
| model | string | 记忆体 ID |
| messages | array | 消息列表 |
| temperature | number | 温度参数 |
| max_tokens | integer | 最大 token 数 |
| stream | boolean | 是否流式输出 |
| tools | array | 工具列表 |
| tool_choice | any | 工具选择策略 |
| memory_config | object | 记忆配置 |

### ChatCompletionResponse
| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 响应 ID |
| object | string | 对象类型 |
| created | integer | 创建时间戳 |
| model | string | 模型名称 |
| choices | array | 选择项列表 |
| usage | object | 使用情况 |

---

## 错误响应

所有错误响应格式：

```json
{
  "detail": "错误描述"
}
```

常见 HTTP 状态码：
- `401 Unauthorized` - Authorization token 无效
- `404 Not Found` - 资源不存在
- `500 Internal Server Error` - 服务器内部错误

---

## 注意事项

1. **API Key**: 如果配置了 `API_KEY`，所有请求（除根路径和健康检查外）都需要携带，格式为 `Authorization: Bearer <token>`
2. **记忆注入**: Chat Completions 会自动检索并注入相关记忆，可通过 `memory_config.enabled=false` 禁用
3. **流式传输**: 设置 `stream=true` 可启用流式输出，使用 SSE 格式
4. **工具调用**: 支持 OpenAI 风格的工具调用，需要在请求中提供 `tools` 和 `tool_choice`
5. **删除级联**: 删除记忆体会同时删除相关的记忆和向量数据
