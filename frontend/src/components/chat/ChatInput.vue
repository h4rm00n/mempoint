<template>
  <div class="chat-input">
    <el-input
      v-model="inputMessage"
      type="textarea"
      :rows="3"
      placeholder="输入消息..."
      @keydown.ctrl.enter="sendMessage"
      :disabled="disabled"
    />
    <div class="input-actions">
      <div class="input-left">
        <el-tooltip content="记忆配置" placement="top">
          <el-button
            :icon="Setting"
            circle
            size="small"
            @click="showMemoryConfig"
          />
        </el-tooltip>
      </div>
      <div class="input-right">
        <el-button
          type="primary"
          :loading="loading"
          :disabled="!inputMessage.trim() || disabled"
          @click="sendMessage"
        >
          发送
          <el-icon class="el-icon--right"><Promotion /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 记忆配置对话框 -->
    <el-dialog v-model="memoryConfigVisible" title="记忆配置" width="500px">
      <el-form :model="memoryConfig" label-width="120px">
        <el-form-item label="启用记忆">
          <el-switch v-model="memoryConfig.enabled" />
        </el-form-item>
        <el-form-item label="最大长期记忆数">
          <el-input-number
            v-model="memoryConfig.max_long_term"
            :min="1"
            :max="50"
          />
        </el-form-item>
        <el-form-item label="自动保存记忆">
          <el-switch v-model="memoryConfig.auto_save" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="memoryConfigVisible = false">取消</el-button>
        <el-button type="primary" @click="saveMemoryConfig">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { Setting, Promotion } from '@element-plus/icons-vue'
import type { MemoryConfig } from '../../types/chat'

const props = defineProps<{
  disabled?: boolean
  loading?: boolean
  memoryConfig?: MemoryConfig
}>()

const emit = defineEmits<{
  send: [message: string]
  updateMemoryConfig: [config: MemoryConfig]
}>()

const inputMessage = ref('')
const memoryConfigVisible = ref(false)
const memoryConfig = ref<MemoryConfig>({
  enabled: true,
  max_long_term: 10,
  auto_save: true
})

watch(() => props.memoryConfig, (newConfig) => {
  if (newConfig) {
    memoryConfig.value = { ...newConfig }
  }
}, { immediate: true })

function sendMessage() {
  if (inputMessage.value.trim()) {
    emit('send', inputMessage.value.trim())
    inputMessage.value = ''
  }
}

function showMemoryConfig() {
  memoryConfigVisible.value = true
}

function saveMemoryConfig() {
  emit('updateMemoryConfig', memoryConfig.value)
  memoryConfigVisible.value = false
}
</script>

<style scoped>
.chat-input {
  background-color: #fff;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
}

.input-left {
  display: flex;
  gap: 8px;
}

.input-right {
  display: flex;
  gap: 8px;
}
</style>
