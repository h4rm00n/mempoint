// 记忆相关类型定义

export interface MemoryCreate {
  persona_id: string
  content: string
  type: 'long_term' | 'short_term'
  entity_id?: string
  metadata?: Record<string, any>
}

export interface MemoryUpdate {
  content?: string
  metadata?: Record<string, any>
}

export interface MemoryResponse {
  id: string
  persona_id: string
  vector_id: string
  entity_id: string | null
  type: 'long_term' | 'short_term'
  content: string
  created_at: string
  last_accessed_at: string
  access_count: number
  metadata: Record<string, any>
}

export interface MemoryListItem {
  id: string
  persona_id: string
  type: 'long_term' | 'short_term'
  content: string
  created_at: string
  access_count: number
  persona_name?: string
}

export interface MemorySearchRequest {
  query: string
  top_k?: number
  metadata?: Record<string, any>
}

export interface MemorySearchResult {
  memory_id: string
  content: string
  similarity: number
  metadata?: Record<string, any>
}

export interface MemoryListParams {
  persona_id?: string
  type?: string
  limit?: number
}
