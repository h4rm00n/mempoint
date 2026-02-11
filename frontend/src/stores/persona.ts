import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { personaAPI } from '../api/persona'
import type { PersonaCreate, PersonaUpdate, PersonaResponse, PersonaListItem } from '../types/persona'
import { ElMessage } from 'element-plus'

export const usePersonaStore = defineStore('persona', () => {
  // 状态
  const personas = ref<PersonaListItem[]>([])
  const currentPersona = ref<PersonaResponse | null>(null)
  const loading = ref(false)

  // 计算属性
  const personaOptions = computed(() =>
    personas.value.map(p => ({
      label: p.name || p.id,
      value: p.id
    }))
  )

  const hasPersonas = computed(() => personas.value.length > 0)

  // 方法
  async function fetchPersonas() {
    try {
      loading.value = true
      const response = await personaAPI.list()
      personas.value = response.data
    } catch (error) {
      ElMessage.error('获取记忆体列表失败')
      console.error(error)
    } finally {
      loading.value = false
    }
  }

  async function fetchPersona(id: string) {
    try {
      loading.value = true
      const response = await personaAPI.get(id)
      currentPersona.value = response.data
      return currentPersona.value
    } catch (error) {
      ElMessage.error('获取记忆体详情失败')
      console.error(error)
      return null
    } finally {
      loading.value = false
    }
  }

  async function createPersona(data: PersonaCreate) {
    try {
      loading.value = true
      const response = await personaAPI.create(data)
      personas.value.push(response.data)
      ElMessage.success('记忆体创建成功')
      return response.data
    } catch (error) {
      ElMessage.error('创建记忆体失败')
      console.error(error)
      return null
    } finally {
      loading.value = false
    }
  }

  async function updatePersona(id: string, data: PersonaUpdate) {
    try {
      loading.value = true
      const response = await personaAPI.update(id, data)
      const persona = response.data
      const index = personas.value.findIndex(p => p.id === id)
      if (index !== -1) {
        personas.value[index] = persona
      }
      if (currentPersona.value?.id === id) {
        currentPersona.value = persona
      }
      ElMessage.success('记忆体更新成功')
      return persona
    } catch (error) {
      ElMessage.error('更新记忆体失败')
      console.error(error)
      return null
    } finally {
      loading.value = false
    }
  }

  async function deletePersona(id: string) {
    try {
      loading.value = true
      await personaAPI.delete(id)
      personas.value = personas.value.filter(p => p.id !== id)
      if (currentPersona.value?.id === id) {
        currentPersona.value = null
      }
      ElMessage.success('记忆体删除成功')
      return true
    } catch (error) {
      ElMessage.error('删除记忆体失败')
      console.error(error)
      return false
    } finally {
      loading.value = false
    }
  }

  function setCurrentPersona(persona: PersonaResponse | null) {
    currentPersona.value = persona
  }

  return {
    // 状态
    personas,
    currentPersona,
    loading,
    // 计算属性
    personaOptions,
    hasPersonas,
    // 方法
    fetchPersonas,
    fetchPersona,
    createPersona,
    updatePersona,
    deletePersona,
    setCurrentPersona
  }
})
