import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { memoryAPI } from '../api/memory'
import type { MemoryCreate, MemoryUpdate, MemoryResponse, MemoryListItem, MemoryListParams, MemorySearchRequest } from '../types/memory'
import { ElMessage } from 'element-plus'

export const useMemoryStore = defineStore('memory', () => {
  // 状态
  const memories = ref<MemoryListItem[]>([])
  const currentMemory = ref<MemoryResponse | null>(null)
  const loading = ref(false)
  const searchResults = ref<MemoryListItem[]>([])
  const total = ref(0)

  // 计算属性
  const hasMemories = computed(() => memories.value.length > 0)

  // 方法
  async function fetchMemories(params?: MemoryListParams) {
    try {
      loading.value = true
      const response = await memoryAPI.list(params)
      memories.value = response.data
      total.value = memories.value.length
    } catch (error) {
      ElMessage.error('获取记忆列表失败')
      console.error(error)
    } finally {
      loading.value = false
    }
  }

  async function fetchMemory(id: string) {
    try {
      loading.value = true
      const response = await memoryAPI.get(id)
      currentMemory.value = response.data
      return currentMemory.value
    } catch (error) {
      ElMessage.error('获取记忆详情失败')
      console.error(error)
      return null
    } finally {
      loading.value = false
    }
  }

  async function createMemory(data: MemoryCreate) {
    try {
      loading.value = true
      const response = await memoryAPI.create(data)
      memories.value.unshift(response.data)
      ElMessage.success('记忆创建成功')
      return response.data
    } catch (error) {
      ElMessage.error('创建记忆失败')
      console.error(error)
      return null
    } finally {
      loading.value = false
    }
  }

  async function updateMemory(id: string, data: MemoryUpdate) {
    try {
      loading.value = true
      const response = await memoryAPI.update(id, data)
      const memory = response.data
      const index = memories.value.findIndex(m => m.id === id)
      if (index !== -1) {
        memories.value[index] = memory
      }
      if (currentMemory.value?.id === id) {
        currentMemory.value = memory
      }
      ElMessage.success('记忆更新成功')
      return memory
    } catch (error) {
      ElMessage.error('更新记忆失败')
      console.error(error)
      return null
    } finally {
      loading.value = false
    }
  }

  async function deleteMemory(id: string) {
    try {
      loading.value = true
      await memoryAPI.delete(id)
      memories.value = memories.value.filter(m => m.id !== id)
      if (currentMemory.value?.id === id) {
        currentMemory.value = null
      }
      ElMessage.success('记忆删除成功')
      return true
    } catch (error) {
      ElMessage.error('删除记忆失败')
      console.error(error)
      return false
    } finally {
      loading.value = false
    }
  }

  async function searchMemories(data: MemorySearchRequest) {
    try {
      loading.value = true
      const response = await memoryAPI.search(data)
      searchResults.value = response.data.map((r: any) => ({
        id: r.memory_id,
        persona_id: '',
        type: 'long_term',
        content: r.content,
        created_at: '',
        score: r.similarity,
        access_count: 0
      }))
      return searchResults.value
    } catch (error) {
      ElMessage.error('搜索记忆失败')
      console.error(error)
      return []
    } finally {
      loading.value = false
    }
  }

  function setCurrentMemory(memory: MemoryResponse | null) {
    currentMemory.value = memory
  }

  function clearSearchResults() {
    searchResults.value = []
  }

  return {
    // 状态
    memories,
    currentMemory,
    loading,
    searchResults,
    total,
    // 计算属性
    hasMemories,
    // 方法
    fetchMemories,
    fetchMemory,
    createMemory,
    updateMemory,
    deleteMemory,
    searchMemories,
    setCurrentMemory,
    clearSearchResults
  }
})
