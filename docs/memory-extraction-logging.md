# 记忆提取机制说明

## 触发条件

记忆提取（自动保存记忆）**只在非流式响应时触发**。

### 非流式响应（stream=false）

✅ **会触发记忆提取**

```json
{
  "model": "persona-1",
  "messages": [...],
  "stream": false
}
```

**处理流程**：
1. 检索相关记忆
2. 注入记忆和系统提示词
3. 调用LLM获取响应
4. 适配响应格式
5. **在后台提取并保存记忆** ← 触发点
6. 返回响应

### 流式响应（stream=true）

❌ **不会触发记忆提取**

```json
{
  "model": "persona-1",
  "messages": [...],
  "stream": true
}
```

**处理流程**：
1. 检索相关记忆
2. 注入记忆和系统提示词
3. 返回流式响应（直接返回，不等待响应完成）
4. **无法添加后台任务** ← 不触发记忆提取

**原因**：流式响应是实时返回的，无法在响应完成前添加后台任务。

## 日志输出

### 非流式响应的完整日志

```
INFO: Injected 2 memories for persona=和暮:
INFO:   1. 用户之前询问过关于AI助手的问题
INFO:   2. 用户对记忆系统感兴趣

INFO: Injected system prompt for persona=和暮: 你是和暮

INFO: Sending messages to LLM (persona=和暮):
INFO:   1. [system] (full content):
这部分是我在下游程序里写的系统提示词。

[相关知识]
1. 用户之前询问过关于AI助手的问题
2. 用户对记忆系统感兴趣

你是和暮

INFO:   2. [user] 你是谁？

INFO: LLM raw response (persona=和暮):
INFO:   {
INFO:     "choices": [...]
INFO:   }

INFO: Adapted response (persona=和暮):
INFO:   {
INFO:     "id": "...",
INFO:     "choices": [...]
INFO:   }

INFO: Scheduling auto memory extraction task (persona=和暮)
INFO: Auto memory extraction task scheduled (persona=和暮)

INFO: Chat completion successful: persona=和暮

--- 后台任务日志（异步执行）---

INFO: Starting auto memory extraction for persona=和暮

INFO: Memory extraction prompt (persona=和暮):
请分析以下对话，提取值得长期记住的重要信息。

对话内容：
用户: 你是谁？

请只提取以下类型的信息：
1. 用户的重要偏好（如喜欢/不喜欢的东西）
2. 用户的重要事实（如生日、联系方式、工作信息）
3. 用户明确要求记住的信息
4. 对未来对话有帮助的关键信息

请以JSON数组格式返回，每个元素包含一个content字段。

INFO: LLM extraction response (persona=和暮):
INFO:   {"choices": [{"message": {"content": "[{\"content\": \"用户询问了AI助手的身份\"}]"}}]}

INFO: Extracted 1 memories from conversation:
INFO:   1. 用户询问了AI助手的身份

INFO: Auto-saved memory: id=mem_xxx, persona_id=和暮

INFO: Auto-saved 1 memories from conversation
```

### 流式响应的日志

```
INFO: Injected 2 memories for persona=和暮:
INFO:   1. 用户之前询问过关于AI助手的问题
INFO:   2. 用户对记忆系统感兴趣

INFO: Injected system prompt for persona=和暮: 你是和暮

INFO: Sending messages to LLM (persona=和暮):
INFO:   1. [system] (full content):
这部分是我在下游程序里写的系统提示词。

[相关知识]
1. 用户之前询问过关于AI助手的问题
2. 用户对记忆系统感兴趣

你是和暮

INFO:   2. [user] 你是谁？

INFO: Using streaming mode (persona=和暮)

--- 流式数据开始返回 ---
data: {...}
data: {...}
data: [DONE]
--- 流式数据结束 ---

⚠️ 注意：没有记忆提取的日志，因为流式响应不触发记忆提取
```

## 配置选项

### 禁用记忆检索

```json
{
  "memory_config": {
    "enabled": false
  }
}
```

### 禁用自动记忆保存

```json
{
  "memory_config": {
    "auto_save": false
  }
}
```

**日志输出**：
```
INFO: Auto memory extraction disabled (persona=和暮)
```

## 如何在流式响应中提取记忆

如果你需要在流式响应中也提取记忆，有以下几种方案：

### 方案1：使用非流式模式

将 `stream` 设置为 `false`，这样会自动触发记忆提取。

### 方案2：客户端手动调用记忆API

在流式响应完成后，客户端手动调用记忆API保存重要信息：

```bash
curl -X POST "http://localhost:8000/api/memories" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-api-key" \
  -d '{
    "persona_id": "和暮",
    "content": "用户询问了AI助手的身份"
  }'
```

### 方案3：实现流式响应的记忆提取（需要修改代码）

修改 `_stream_chat_completion` 函数，在流式结束时添加记忆提取逻辑。这需要：
1. 收集完整的流式响应
2. 在流式结束时触发记忆提取
3. 使用其他机制（如消息队列）来处理后台任务

## 总结

| 模式 | 记忆检索 | 记忆提取（保存） | 日志 |
|------|---------|----------------|------|
| 非流式（stream=false） | ✅ | ✅ | 完整日志 |
| 流式（stream=true） | ✅ | ❌ | 无记忆提取日志 |

**推荐**：如果需要自动记忆提取，使用非流式模式。
