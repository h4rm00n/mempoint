<template>
  <div class="chat-view">
    <div class="chat-header">
      <div class="header-left">
        <el-select
          v-model="selectedModel"
          placeholder="选择模型"
          style="width: 300px"
          @change="handleModelChange"
        >
          <el-option-group
            v-for="group in modelGroups"
            :key="group.personaId"
            :label="group.personaId"
          >
            <el-option
              v-for="model in group.models"
              :key="model.id"
              :label="model.llmModel"
              :value="model.id"
            />
          </el-option-group>
        </el-select>
      </div>
      <div class="header-right">
        <el-button :icon="Plus" @click="newChat">新对话</el-button>
        <el-button :icon="Delete" @click="clearChat">清空对话</el-button>
      </div>
    </div>

    <div class="chat-container" ref="chatContainer">
      <div v-if="!chatStore.hasMessages" class="empty-state">
        <el-empty description="开始新的对话吧" />
      </div>
      <ChatMessageComponent
        v-for="(message, index) in chatStore.messages"
        :key="index"
        :message="message"
        :injected-memories="getInjectedMemories(index)"
      />
    </div>

    <div class="chat-footer">
      <ChatInput
        :disabled="chatStore.isStreaming"
        :loading="chatStore.isStreaming"
        :memory-config="chatStore.memoryConfig"
        @send="handleSend"
        @update-memory-config="handleUpdateMemoryConfig"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch, computed } from 'vue'
import { useChatStore } from '../stores/chat'
import { chatAPI } from '../api/chat'
import { modelsAPI } from '../api/models'
import type { Model } from '../types/models'
import ChatMessageComponent from '../components/chat/ChatMessage.vue'
import ChatInput from '../components/chat/ChatInput.vue'
import { Plus, Delete } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const chatStore = useChatStore()

const chatContainer = ref<HTMLElement>()
const selectedModel = ref<string>('')
const models = ref<Model[]>([])
const injectedMemoriesMap = ref<Map<number, string[]>>(new Map())

// 模型分组：按 persona_id 分组
const modelGroups = computed(() => {
  const groups: Record<string, { personaId: string; models: Array<{ id: string; llmModel: string }> }> = {}

  models.value.forEach(model => {
    // modelId 格式: persona_id/llm_model
    const parts = model.id.split('/')
    if (parts.length >= 2) {
      const personaId = parts[0]
      if (!personaId) return // 跳过空的 personaId
      
      const llmModel = parts.slice(1).join('/') // 处理可能包含多个斜杠的 llm_model

      if (!groups[personaId]) {
        groups[personaId] = {
          personaId,
          models: []
        }
      }

      const group = groups[personaId]!
      group.models.push({
        id: model.id,
        llmModel
      })
    }
  })

  return Object.values(groups)
})

onMounted(async () => {
  await fetchModels()
})

watch(() => chatStore.messages, () => {
  nextTick(() => {
    scrollToBottom()
  })
}, { deep: true })

async function fetchModels() {
  try {
    const response = await modelsAPI.list()
    models.value = response.data.data
    if (models.value.length > 0 && !selectedModel.value) {
      selectedModel.value = models.value[0]?.id || ''
    }
  } catch (error) {
    ElMessage.error('获取模型列表失败')
    console.error('Failed to fetch models:', error)
  }
}

function handleModelChange(_modelId: string) {
  // 可以在这里保存当前选择的模型
  clearChat()
}

function newChat() {
  chatStore.clearMessages()
  injectedMemoriesMap.value.clear()
}

function clearChat() {
  chatStore.clearMessages()
  injectedMemoriesMap.value.clear()
  ElMessage.success('对话已清空')
}

function getInjectedMemories(index: number): string[] {
  return injectedMemoriesMap.value.get(index) || []
}

async function handleSend(message: string) {
  if (!selectedModel.value) {
    ElMessage.warning('请先选择模型')
    return
  }

  // 添加用户消息
  chatStore.addMessage({
    role: 'user',
    content: message
  })

  // 准备请求
  const messages = chatStore.messages.map(m => ({
    role: m.role,
    content: m.content
  }))

  chatStore.setStreaming(true)

  // 添加助手消息占位
  chatStore.addMessage({
    role: 'assistant',
    content: ''
  })

  let assistantMessage = ''

  try {
    await chatAPI.sendMessageStream(
      {
        model: selectedModel.value,
        messages,
        memory_config: chatStore.memoryConfig
      },
      (chunk) => {
        // 处理流式响应
        if (chunk.choices && chunk.choices[0]) {
          const delta = chunk.choices[0].delta
          if (delta.content) {
            assistantMessage += delta.content
            chatStore.updateLastMessage(assistantMessage)
          }
        }
      },
      () => {
        // 完成
        chatStore.setStreaming(false)
      },
      (error) => {
        // 错误
        chatStore.setStreaming(false)
        ElMessage.error(error.message || '发送消息失败')
      }
    )
  } catch (error) {
    chatStore.setStreaming(false)
    ElMessage.error('发送消息失败')
  }
}

function handleUpdateMemoryConfig(config: any) {
  chatStore.setMemoryConfig(config)
  ElMessage.success('记忆配置已更新')
}

function scrollToBottom() {
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}
</script>

<style scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 16px;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.header-left,
.header-right {
  display: flex;
  gap: 8px;
}

.chat-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background-color: #f5f7fa;
  border-radius: 8px;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.chat-footer {
  flex-shrink: 0;
}
</style>
