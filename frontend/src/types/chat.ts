// 聊天相关类型定义

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system' | 'tool'
  content: string
  tool_calls?: ToolCall[]
  tool_call_id?: string
  timestamp?: Date
}

export interface ToolCall {
  id: string
  type: 'function'
  function: {
    name: string
    arguments: string
  }
}

export interface Tool {
  type: 'function'
  function: ToolFunction
}

export interface ToolFunction {
  name: string
  description: string
  parameters: Record<string, any>
}

export interface MemoryConfig {
  enabled: boolean
  max_long_term?: number
  auto_save?: boolean
}

export interface ChatCompletionRequest {
  model: string
  messages: ChatMessage[]
  temperature?: number
  max_tokens?: number
  stream?: boolean
  tools?: Tool[]
  tool_choice?: 'auto' | 'none' | string
  memory_config?: MemoryConfig
}

export interface ChatCompletionChoice {
  index: number
  message: ChatMessage
  finish_reason: 'stop' | 'length' | 'tool_calls' | 'content_filter'
}

export interface ChatCompletionUsage {
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
}

export interface ChatCompletionResponse {
  id: string
  object: 'chat.completion'
  created: number
  model: string
  choices: ChatCompletionChoice[]
  usage: ChatCompletionUsage
}

export interface ChatStreamChunk {
  id: string
  object: 'chat.completion.chunk'
  created: number
  model: string
  choices: Array<{
    index: number
    delta: {
      role?: string
      content?: string
      tool_calls?: ToolCall[]
    }
    finish_reason: string | null
  }>
}
