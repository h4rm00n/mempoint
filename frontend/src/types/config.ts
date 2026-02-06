// 配置相关类型定义

export interface SystemConfig {
  llm: LLMConfig
  embedding: EmbeddingConfig
  memory_extraction: MemoryExtractionConfig
  memory_system: MemorySystemConfig
  memory_scoring: MemoryScoringConfig
  milvus: MilvusConfig
  kuzu: KuzuConfig
  cache: CacheConfig
}

export interface LLMConfig {
  base_url: string
  api_key: string
  model: string
  timeout: number
  temperature: number
  max_tokens: number
}

export interface EmbeddingConfig {
  base_url: string
  api_key: string
  model: string
  dimension: number
  timeout: number
}

export interface MemoryExtractionConfig {
  enabled: boolean
  model: string
  temperature: number
  max_tokens: number
}

export interface MemorySystemConfig {
  enabled: boolean
  retrieval_top_k: number
  retrieval_threshold: number
  max_long_term_memories: number
  auto_save: boolean
}

export interface MemoryScoringConfig {
  recency_weight: number
  access_count_weight: number
  importance_weight: number
  similarity_weight: number
}

export interface MilvusConfig {
  host: string
  port: number
  collection_name: string
  dimension: number
  index_type: string
  metric_type: string
}

export interface KuzuConfig {
  path: string
  read_only: boolean
}

export interface CacheConfig {
  enabled: boolean
  ttl: number
  max_size: number
}

export interface SystemConfigUpdate {
  llm?: Partial<LLMConfig>
  embedding?: Partial<EmbeddingConfig>
  memory_extraction?: Partial<MemoryExtractionConfig>
  memory_system?: Partial<MemorySystemConfig>
  memory_scoring?: Partial<MemoryScoringConfig>
  milvus?: Partial<MilvusConfig>
  kuzu?: Partial<KuzuConfig>
  cache?: Partial<CacheConfig>
}

export interface ConfigItem {
  id: string
  user_id: string
  config_key: string
  config_value: Record<string, any>
  description?: string
  created_at: string
  updated_at: string
}
