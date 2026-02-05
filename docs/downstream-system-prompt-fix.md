# 下游系统提示词保留修复

## 问题描述

之前的实现中，当下游程序提供系统提示词时，会被Persona的system_prompt完全覆盖，导致下游程序的自定义指令丢失。

### 示例场景

下游程序发送以下消息：
```python
[
    ChatMessage(role='system', content='这部分是我在下游程序里写的系统提示词。'),
    ChatMessage(role='user', content='你是谁？')
]
```

**修复前的行为**：
- 下游的system提示词会被Persona的system_prompt完全替换
- 结果：下游的指令丢失

**修复后的行为**：
- 下游的system提示词会被保留
- Persona的system_prompt会追加到后面
- 结果：两者都生效

## 修改内容

### 1. 修改系统提示词注入逻辑 (`backend/api/chat.py`)

**修复前**（第127行）：
```python
msg["content"] = system_prompt  # 直接覆盖
```

**修复后**：
```python
msg["content"] = f"{msg['content']}\n\n{system_prompt}"  # 追加而不是覆盖
```

### 2. 增加LLM响应日志 (`backend/api/chat.py`)

添加了对LLM原始响应和适配后响应的日志记录，方便调试和监控。

## 处理流程

对于包含下游系统提示词的请求，处理流程如下：

1. **记忆注入**（如果启用）：
   - 检索相关记忆
   - 将记忆追加到system消息中

2. **Persona系统提示词注入**（如果有）：
   - 查找是否已有system消息
   - 如果有：将Persona的system_prompt追加到现有system消息后面
   - 如果没有：创建新的system消息

3. **最终system消息结构**：
   ```
   [下游系统提示词]
   
   [记忆内容]
   
   [Persona系统提示词]
   ```

## 测试

运行测试脚本验证修复：

```bash
./tests/05-test-downstream-system-prompt.sh
```

### 测试内容

1. 创建一个带有system_prompt的Persona
2. 发送包含下游系统提示词的聊天请求
3. 验证下游系统提示词是否被保留
4. 查看日志确认Persona系统提示词是否被正确追加

## 日志输出示例

```
INFO: Injected 2 memories for persona=test-prompt-preserve:
INFO:   1. 用户之前询问过关于AI助手的问题
INFO:   2. 用户对记忆系统感兴趣

INFO: Memory context injected into system prompt:
INFO: [相关知识]
INFO: 1. 用户之前询问过关于AI助手的问题
INFO: 2. 用户对记忆系统感兴趣

INFO: Injected system prompt for persona=test-prompt-preserve: 这是Persona的系统提示词。

INFO: Sending messages to LLM (persona=test-prompt-preserve):
INFO:   1. [system] (full content):
这是下游程序提供的系统提示词。

[相关知识]
1. 用户之前询问过关于AI助手的问题
2. 用户对记忆系统感兴趣

这是Persona的系统提示词。

INFO:   2. [user] 请告诉我你的系统提示词是什么？

INFO: LLM raw response (persona=test-prompt-preserve):
INFO:   {...}

INFO: Adapted response (persona=test-prompt-preserve):
INFO:   {...}
```

## 兼容性说明

- ✅ 完全向后兼容
- ✅ 不影响没有下游系统提示词的请求
- ✅ 记忆注入机制保持不变
- ✅ 流式响应保持不变
