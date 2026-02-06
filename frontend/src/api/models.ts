import request from '../utils/request'
import type { ModelsResponse, MemoryToolsResponse } from '../types/models'

export const modelsAPI = {
  // 列出模型
  list() {
    return request.get<ModelsResponse>('/v1/models')
  }
}

export const memoryToolsAPI = {
  // 获取记忆工具定义
  list() {
    return request.get<MemoryToolsResponse>('/v1/memory-tools')
  }
}
