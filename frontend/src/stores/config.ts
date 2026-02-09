import { defineStore } from 'pinia'
import { ref } from 'vue'
import { configAPI } from '../api/config'
import type { SystemConfig, SystemConfigUpdate } from '../types/config'
import { ElMessage } from 'element-plus'

export const useConfigStore = defineStore('config', () => {
  // 状态
  const config = ref<SystemConfig | null>(null)
  const loading = ref(false)

  // 方法
  async function fetchConfig() {
    try {
      loading.value = true
      const response = await configAPI.get()
      config.value = response.data
      return config.value
    } catch (error) {
      ElMessage.error('获取配置失败')
      console.error(error)
      return null
    } finally {
      loading.value = false
    }
  }

  async function updateConfig(data: SystemConfigUpdate) {
    try {
      loading.value = true
      const response = await configAPI.update(data)
      config.value = response.data
      ElMessage.success('配置更新成功')
      return response.data
    } catch (error) {
      ElMessage.error('更新配置失败')
      console.error(error)
      return null
    } finally {
      loading.value = false
    }
  }

  async function fetchConfigByKey(config_key: string) {
    try {
      loading.value = true
      return await configAPI.getByKey(config_key)
    } catch (error) {
      ElMessage.error('获取配置失败')
      console.error(error)
      return null
    } finally {
      loading.value = false
    }
  }

  async function updateConfigByKey(config_key: string, data: any) {
    try {
      loading.value = true
      const updated = await configAPI.updateByKey(config_key, data)
      if (config.value) {
        config.value = { ...config.value, [config_key]: updated }
      }
      ElMessage.success('配置更新成功')
      return updated
    } catch (error) {
      ElMessage.error('更新配置失败')
      console.error(error)
      return null
    } finally {
      loading.value = false
    }
  }

  async function reinitializeConfig() {
    try {
      loading.value = true
      await configAPI.reinitialize()
      ElMessage.success('配置重新初始化成功')
      return true
    } catch (error) {
      ElMessage.error('重新初始化配置失败')
      console.error(error)
      return false
    } finally {
      loading.value = false
    }
  }

  return {
    // 状态
    config,
    loading,
    // 方法
    fetchConfig,
    updateConfig,
    fetchConfigByKey,
    updateConfigByKey,
    reinitializeConfig
  }
})
