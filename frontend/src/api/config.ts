import request from '../utils/request'
import type {
  SystemConfig,
  SystemConfigUpdate,
  ConfigItem
} from '../types/config'

export const configAPI = {
  // 获取系统配置
  get() {
    return request.get<SystemConfig>('/v1/config')
  },

  // 更新系统配置
  update(data: SystemConfigUpdate) {
    return request.put<SystemConfig>('/v1/config', data)
  },

  // 获取指定配置
  getByKey(config_key: string) {
    return request.get<Record<string, any>>(`/v1/config/${config_key}`)
  },

  // 更新指定配置
  updateByKey(config_key: string, data: any) {
    return request.put<Record<string, any>>(`/v1/config/${config_key}`, data)
  },

  // 列出所有配置
  list(user_id?: string) {
    return request.get<ConfigItem[]>('/v1/config/list', {
      params: { user_id }
    })
  },

  // 创建新配置
  create(data: {
    user_id: string
    config_key: string
    config_value: Record<string, any>
    description?: string
  }) {
    return request.post<ConfigItem>('/v1/config', data)
  },

  // 删除配置
  delete(config_id: string) {
    return request.delete(`/v1/config/${config_id}`)
  },

  // 重新初始化配置
  reinitialize() {
    return request.post<{ message: string }>('/v1/config/reinitialize')
  }
}
