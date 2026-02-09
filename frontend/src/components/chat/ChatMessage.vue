<template>
  <div :class="['chat-message', message.role]">
    <div class="message-avatar">
      <el-icon v-if="message.role === 'user'" :size="24"><User /></el-icon>
      <el-icon v-else :size="24"><ChatDotRound /></el-icon>
    </div>
    <div class="message-content">
      <div class="message-role">{{ roleLabel }}</div>
      <div v-if="message.role === 'assistant' && injectedMemories && injectedMemories.length > 0" class="injected-memories">
        <el-tag size="small" type="info">
          <el-icon><Reading /></el-icon>
          已注入 {{ injectedMemories.length }} 条记忆
        </el-tag>
      </div>
      <MarkdownRenderer v-if="message.content" :content="message.content" />
      <div v-if="message.tool_calls && message.tool_calls.length > 0" class="tool-calls">
        <el-tag v-for="tool in message.tool_calls" :key="tool.id" size="small" type="warning">
          调用工具: {{ tool.function.name }}
        </el-tag>
      </div>
      <div v-if="message.timestamp" class="message-time">
        {{ formatDateTime(message.timestamp) }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ChatMessage } from '../../types/chat'
import MarkdownRenderer from '../common/MarkdownRenderer.vue'
import { formatDateTime } from '../../utils/helpers'
import { User, ChatDotRound, Reading } from '@element-plus/icons-vue'

const props = defineProps<{
  message: ChatMessage
  injectedMemories?: string[]
}>()

const roleLabel = computed(() => {
  switch (props.message.role) {
    case 'user':
      return '用户'
    case 'assistant':
      return '助手'
    case 'system':
      return '系统'
    case 'tool':
      return '工具'
    default:
      return '未知'
  }
})
</script>

<style scoped>
.chat-message {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  padding: 12px;
  border-radius: 8px;
  background-color: #fff;
}

.chat-message.user {
  flex-direction: row-reverse;
}

.chat-message.user .message-content {
  align-items: flex-end;
}

.message-avatar {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background-color: #f0f0f0;
}

.chat-message.user .message-avatar {
  background-color: #409eff;
  color: #fff;
}

.chat-message.assistant .message-avatar {
  background-color: #67c23a;
  color: #fff;
}

.message-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-width: 70%;
}

.message-role {
  font-size: 12px;
  color: #909399;
  font-weight: 500;
}

.injected-memories {
  margin-top: 4px;
}

.tool-calls {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.message-time {
  font-size: 12px;
  color: #c0c4cc;
  margin-top: 4px;
}
</style>
