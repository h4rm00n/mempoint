import request from '../utils/request'
import type {
  MemoryCreate,
  MemoryUpdate,
  MemoryResponse,
  MemoryListItem,
  MemorySearchRequest,
  MemorySearchResult,
  MemoryListParams
} from '../types/memory'

export const memoryAPI = {
  // 获取记忆列表
  list(params?: MemoryListParams) {
    return request.get<MemoryListItem[]>('/v1/memories', { params })
  },

  // 获取记忆详情
  get(id: string) {
    return request.get<MemoryResponse>(`/v1/memories/${id}`)
  },

  // 创建记忆
  create(data: MemoryCreate) {
    return request.post<MemoryResponse>('/v1/memories', data)
  },

  // 更新记忆
  update(id: string, data: MemoryUpdate) {
    return request.put<MemoryResponse>(`/v1/memories/${id}`, data)
  },

  // 删除记忆
  delete(id: string) {
    return request.delete(`/v1/memories/${id}`)
  },

  // 语义搜索记忆
  search(data: MemorySearchRequest) {
    return request.post<MemorySearchResult[]>('/v1/memories/search', data)
  }
}
