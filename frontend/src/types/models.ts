// 模型相关类型定义

export interface Model {
  id: string
  object: 'model'
  created: number
  owned_by: string
}

export interface ModelsResponse {
  object: 'list'
  data: Model[]
}

export interface MemoryTool {
  type: 'function'
  function: {
    name: string
    description: string
    parameters: {
      type: string
      properties: Record<string, any>
      required: string[]
    }
  }
}

export interface MemoryToolsResponse {
  object: 'list'
  data: MemoryTool[]
}
