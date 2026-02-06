import request from '../utils/request'
import type {
  PersonaCreate,
  PersonaUpdate,
  PersonaResponse,
  PersonaListItem
} from '../types/persona'

export const personaAPI = {
  // 获取记忆体列表
  list() {
    return request.get<PersonaListItem[]>('/v1/personas')
  },

  // 创建记忆体
  create(data: PersonaCreate) {
    return request.post<PersonaResponse>('/v1/personas', data)
  },

  // 获取记忆体详情
  get(id: string) {
    return request.get<PersonaResponse>(`/v1/personas/${id}`)
  },

  // 更新记忆体
  update(id: string, data: PersonaUpdate) {
    return request.put<PersonaResponse>(`/v1/personas/${id}`, data)
  },

  // 删除记忆体
  delete(id: string) {
    return request.delete(`/v1/personas/${id}`)
  }
}
