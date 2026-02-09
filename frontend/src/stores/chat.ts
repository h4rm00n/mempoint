import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ChatMessage, MemoryConfig } from '../types/chat'
import { storage } from '../utils/storage'

export const useChatStore = defineStore('chat', () => {
  // 状态
  const currentPersonaId = ref<string>(storage.get<string>('currentPersonaId') || '')
  const currentModel = ref<string>(storage.get<string>('currentModel') || '')
  const messages = ref<ChatMessage[]>([])
  const isStreaming = ref(false)
  const memoryConfig = ref<MemoryConfig>({
    enabled: true,
    max_long_term: 10,
    auto_save: true
  })

  // 计算属性
  const hasMessages = computed(() => messages.value.length > 0)
  const lastMessage = computed(() => messages.value[messages.value.length - 1])

  // 方法
  function setCurrentPersonaId(id: string) {
    currentPersonaId.value = id
    storage.set('currentPersonaId', id)
  }

  function setCurrentModel(model: string) {
    currentModel.value = model
    storage.set('currentModel', model)
  }

  function addMessage(message: ChatMessage) {
    messages.value.push({
      ...message,
      timestamp: new Date()
    })
  }

  function updateLastMessage(content: string) {
    if (messages.value.length > 0) {
      const lastMsg = messages.value[messages.value.length - 1]
      if (lastMsg && lastMsg.role === 'assistant') {
        lastMsg.content = content
      }
    }
  }

  function clearMessages() {
    messages.value = []
  }

  function setStreaming(streaming: boolean) {
    isStreaming.value = streaming
  }

  function setMemoryConfig(config: Partial<MemoryConfig>) {
    memoryConfig.value = { ...memoryConfig.value, ...config }
  }

  return {
    // 状态
    currentPersonaId,
    currentModel,
    messages,
    isStreaming,
    memoryConfig,
    // 计算属性
    hasMessages,
    lastMessage,
    // 方法
    setCurrentPersonaId,
    setCurrentModel,
    addMessage,
    updateLastMessage,
    clearMessages,
    setStreaming,
    setMemoryConfig
  }
})
