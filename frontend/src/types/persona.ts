// 记忆体相关类型定义

export interface PersonaCreate {
  name: string
  description?: string
  system_prompt?: string
}

export interface PersonaUpdate {
  description?: string
  system_prompt?: string
}

export interface PersonaResponse {
  id: string
  name: string
  description: string
  system_prompt: string
  created_at: string
  updated_at: string
}

export interface PersonaListItem {
  id: string
  name?: string
  description: string
  created_at: string
  updated_at: string
  memory_count?: number
}
