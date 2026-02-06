import { defineStore } from 'pinia'
import { ref } from 'vue'
import { storage } from '../utils/storage'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const apiKey = ref<string>(storage.get<string>('api_key') || '')

  // 方法
  function setApiKey(key: string) {
    apiKey.value = key
    storage.set('api_key', key)
  }

  function clearApiKey() {
    apiKey.value = ''
    storage.remove('api_key')
  }

  function hasApiKey(): boolean {
    return !!apiKey.value
  }

  return {
    // 状态
    apiKey,
    // 方法
    setApiKey,
    clearApiKey,
    hasApiKey
  }
})
