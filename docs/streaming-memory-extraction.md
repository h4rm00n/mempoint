# 流式响应记忆提取功能

## 更新说明

现在流式响应（stream=true）也会触发自动记忆提取！

## 实现原理

在流式响应结束时，使用 `asyncio.create_task` 异步触发记忆提取，不会阻塞流式响应的返回。

## 工作流程

### 流式响应（stream=true）

1. 检索相关记忆并注入
2. 注入系统提示词
3. 开始流式响应
4. 发送数据块到客户端
5. 发送结束标记 `[DONE]`
6. **触发记忆提取**（异步执行，不阻塞响应）
7. 返回流式响应

### 非流式响应（stream=false）

1. 检索相关记忆并注入
2. 注入系统提示词
3. 调用LLM获取完整响应
4. 适配响应格式
5. **触发记忆提取**（使用BackgroundTasks）
6. 返回响应

## 日志输出

### 流式响应的完整日志

```
INFO: Injected system prompt for persona=和暮: 你是和暮
INFO: Sending messages to LLM (persona=和暮):
INFO:   1. [system] (full content):
这部分是我在下游程序里写的系统提示词。

你是和暮
INFO:   2. [user] 你是谁？

INFO: Using streaming mode (persona=和暮)

--- 流式数据开始返回 ---
data: {...}
data: {...}
data: [DONE]
--- 流式数据结束 ---

INFO: Stream completed, triggering auto memory extraction (persona=和暮)

--- 记忆提取（异步执行）---

INFO: Starting auto memory extraction for persona=和暮
INFO: Memory extraction prompt (persona=和暮):
[提取提示词完整内容]
INFO: LLM extraction response (persona=和暮):
[LLM响应完整内容]
INFO: Extracted 1 memories from conversation
INFO: Auto-saved memory: id=mem_xxx, persona_id=和暮
INFO: Auto-saved 1 memories from conversation
```

### 非流式响应的完整日志

```
INFO: Injected system prompt for persona=和暮: 你是和暮
INFO: Sending messages to LLM (persona=和暮)
INFO: LLM raw response (persona=和暮)
INFO: Adapted response (persona=和暮)
INFO: Scheduling auto memory extraction task (persona=和暮)
INFO: Auto memory extraction task scheduled (persona=和暮)
INFO: Chat completion successful: persona=和暮

--- 记忆提取（后台任务，异步执行）---

INFO: Starting auto memory extraction for persona=和暮
INFO: Memory extraction prompt (persona=和暮)
[提取提示词完整内容]
INFO: LLM extraction response (persona=和暮)
[LLM响应完整内容]
INFO: Extracted 1 memories from conversation
INFO: Auto-saved memory: id=mem_xxx, persona_id=和暮
INFO: Auto-saved 1 memories from conversation
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

流式响应日志：
```
INFO: Using streaming mode (persona=和暮)
--- 流式数据 ---
data: [DONE]
--- 不会触发记忆提取 ---
```

## 技术细节

### 流式响应的记忆提取

```python
async def _stream_chat_completion(...):
    try:
        # 流式发送数据
        async for chunk in llm_client.chat_completion_stream(...):
            yield f"data: {json.dumps(chunk)}\n\n"

        # 发送结束标记
        yield "data: [DONE]\n\n"

        # 流式响应结束后，触发记忆提取
        if original_messages and persona_id:
            auto_save_enabled = memory_config.get("auto_save", True)
            if auto_save_enabled:
                logger.info(f"Stream completed, triggering auto memory extraction")
                # 使用asyncio.create_task异步执行，不阻塞响应
                asyncio.create_task(
                    _extract_memory_after_stream(...)
                )
    except Exception as e:
        logger.error(f"Error in streaming chat completion: {e}")
        raise
```

### 非流式响应的记忆提取

```python
async def chat_completions(...):
    # ... 调用LLM ...

    # 使用BackgroundTasks添加后台任务
    if auto_save_enabled:
        logger.info(f"Scheduling auto memory extraction task")
        background_tasks.add_task(
            auto_memory_service.extract_and_save_memories,
            ...
        )
```

## 性能考虑

### 流式响应
- ✅ 不阻塞响应返回
- ✅ 记忆提取在后台异步执行
- ✅ 客户端可以立即开始接收流式数据
- ⚠️ 记忆提取可能在响应完成后才执行

### 非流式响应
- ✅ 记忆提取在后台任务中执行
- ✅ 不阻塞响应返回
- ✅ 使用FastAPI的BackgroundTasks机制

## 总结

| 模式 | 记忆检索 | 记忆提取（保存） | 触发方式 | 日志 |
|------|---------|----------------|---------|------|
| 流式（stream=true） | ✅ | ✅ | asyncio.create_task | `Stream completed, triggering auto memory extraction` |
| 非流式（stream=false） | ✅ | ✅ | BackgroundTasks | `Scheduling auto memory extraction task` |

**现在两种模式都支持自动记忆提取！**
