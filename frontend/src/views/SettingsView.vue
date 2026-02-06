<template>
  <div class="settings-view">
    <h2>配置管理</h2>

    <el-card class="settings-card">
      <el-tabs v-model="activeTab" type="border-card">
        <!-- LLM 配置 -->
        <el-tab-pane label="LLM 配置" name="llm">
          <el-form v-if="configStore.config" :model="llmForm" label-width="120px">
            <el-form-item label="Base URL">
              <el-input v-model="llmForm.base_url" placeholder="https://api.siliconflow.com/v1" />
            </el-form-item>
            <el-form-item label="API Key">
              <el-input
                v-model="llmForm.api_key"
                type="password"
                placeholder="请输入 API Key"
                show-password
              />
            </el-form-item>
            <el-form-item label="Model">
              <el-input v-model="llmForm.model" placeholder="deepseek-ai/DeepSeek-V3.2" />
            </el-form-item>
            <el-form-item label="Timeout">
              <el-input-number v-model="llmForm.timeout" :min="1" :max="300" />
              <span class="unit">秒</span>
            </el-form-item>
            <el-form-item label="Temperature">
              <el-input-number v-model="llmForm.temperature" :min="0" :max="2" :step="0.1" :precision="1" />
            </el-form-item>
            <el-form-item label="Max Tokens">
              <el-input-number v-model="llmForm.max_tokens" :min="1" :max="100000" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveLLMConfig">保存</el-button>
              <el-button @click="resetLLMConfig">重置为默认</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- Embedding 配置 -->
        <el-tab-pane label="Embedding 配置" name="embedding">
          <el-form v-if="configStore.config" :model="embeddingForm" label-width="120px">
            <el-form-item label="Base URL">
              <el-input v-model="embeddingForm.base_url" placeholder="https://api.siliconflow.com/v1" />
            </el-form-item>
            <el-form-item label="API Key">
              <el-input
                v-model="embeddingForm.api_key"
                type="password"
                placeholder="请输入 API Key"
                show-password
              />
            </el-form-item>
            <el-form-item label="Model">
              <el-input v-model="embeddingForm.model" placeholder="BAAI/bge-m3" />
            </el-form-item>
            <el-form-item label="Dimension">
              <el-input-number v-model="embeddingForm.dimension" :min="1" />
            </el-form-item>
            <el-form-item label="Timeout">
              <el-input-number v-model="embeddingForm.timeout" :min="1" :max="300" />
              <span class="unit">秒</span>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveEmbeddingConfig">保存</el-button>
              <el-button @click="resetEmbeddingConfig">重置为默认</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 记忆系统配置 -->
        <el-tab-pane label="记忆系统" name="memory_system">
          <el-form v-if="configStore.config" :model="memorySystemForm" label-width="180px">
            <el-form-item label="启用记忆系统">
              <el-switch v-model="memorySystemForm.enabled" />
            </el-form-item>
            <el-form-item label="检索Top K">
              <el-input-number v-model="memorySystemForm.retrieval_top_k" :min="1" :max="100" />
            </el-form-item>
            <el-form-item label="检索阈值">
              <el-input-number v-model="memorySystemForm.retrieval_threshold" :min="0" :max="1" :step="0.01" :precision="2" />
            </el-form-item>
            <el-form-item label="最大长期记忆数">
              <el-input-number v-model="memorySystemForm.max_long_term_memories" :min="1" :max="1000" />
            </el-form-item>
            <el-form-item label="自动保存记忆">
              <el-switch v-model="memorySystemForm.auto_save" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveMemorySystemConfig">保存</el-button>
              <el-button @click="resetMemorySystemConfig">重置为默认</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 记忆评分配置 -->
        <el-tab-pane label="记忆评分" name="memory_scoring">
          <el-form v-if="configStore.config" :model="memoryScoringForm" label-width="180px">
            <el-form-item label="近期性权重">
              <el-input-number v-model="memoryScoringForm.recency_weight" :min="0" :max="1" :step="0.01" :precision="2" />
            </el-form-item>
            <el-form-item label="访问次数权重">
              <el-input-number v-model="memoryScoringForm.access_count_weight" :min="0" :max="1" :step="0.01" :precision="2" />
            </el-form-item>
            <el-form-item label="重要性权重">
              <el-input-number v-model="memoryScoringForm.importance_weight" :min="0" :max="1" :step="0.01" :precision="2" />
            </el-form-item>
            <el-form-item label="相似度权重">
              <el-input-number v-model="memoryScoringForm.similarity_weight" :min="0" :max="1" :step="0.01" :precision="2" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveMemoryScoringConfig">保存</el-button>
              <el-button @click="resetMemoryScoringConfig">重置为默认</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 数据库配置 -->
        <el-tab-pane label="数据库" name="database">
          <el-form v-if="configStore.config" :model="databaseForm" label-width="120px">
            <el-divider content-position="left">Milvus 配置</el-divider>
            <el-form-item label="Host">
              <el-input v-model="databaseForm.milvus.host" placeholder="localhost" />
            </el-form-item>
            <el-form-item label="Port">
              <el-input-number v-model="databaseForm.milvus.port" :min="1" :max="65535" />
            </el-form-item>
            <el-form-item label="Collection Name">
              <el-input v-model="databaseForm.milvus.collection_name" placeholder="memories" />
            </el-form-item>
            <el-form-item label="Dimension">
              <el-input-number v-model="databaseForm.milvus.dimension" :min="1" />
            </el-form-item>
            <el-divider content-position="left">KùzuDB 配置</el-divider>
            <el-form-item label="Path">
              <el-input v-model="databaseForm.kuzu.path" placeholder="./data/kuzu" />
            </el-form-item>
            <el-form-item label="Read Only">
              <el-switch v-model="databaseForm.kuzu.read_only" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveDatabaseConfig">保存</el-button>
              <el-button @click="resetDatabaseConfig">重置为默认</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-card class="actions-card">
      <template #header>
        <h3>全局操作</h3>
      </template>
      <div class="actions">
        <el-button type="danger" @click="handleReinitialize">
          重新初始化配置
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useConfigStore } from '../stores/config'
import { ElMessage, ElMessageBox } from 'element-plus'

const configStore = useConfigStore()

const activeTab = ref('llm')
const llmForm = ref<any>({})
const embeddingForm = ref<any>({})
const memorySystemForm = ref<any>({})
const memoryScoringForm = ref<any>({})
const databaseForm = ref<any>({})

onMounted(async () => {
  await configStore.fetchConfig()
  initForms()
})

watch(() => configStore.config, () => {
  initForms()
}, { deep: true })

function initForms() {
  if (!configStore.config) return

  llmForm.value = { ...configStore.config.llm }
  embeddingForm.value = { ...configStore.config.embedding }
  memorySystemForm.value = { ...configStore.config.memory_system }
  memoryScoringForm.value = { ...configStore.config.memory_scoring }
  databaseForm.value = {
    milvus: { ...configStore.config.milvus },
    kuzu: { ...configStore.config.kuzu }
  }
}

async function saveLLMConfig() {
  await configStore.updateConfig({ llm: llmForm.value })
  ElMessage.success('LLM 配置已保存')
}

async function resetLLMConfig() {
  await configStore.updateConfigByKey('llm', {})
  await configStore.fetchConfig()
  initForms()
  ElMessage.success('LLM 配置已重置')
}

async function saveEmbeddingConfig() {
  await configStore.updateConfig({ embedding: embeddingForm.value })
  ElMessage.success('Embedding 配置已保存')
}

async function resetEmbeddingConfig() {
  await configStore.updateConfigByKey('embedding', {})
  await configStore.fetchConfig()
  initForms()
  ElMessage.success('Embedding 配置已重置')
}

async function saveMemorySystemConfig() {
  await configStore.updateConfig({ memory_system: memorySystemForm.value })
  ElMessage.success('记忆系统配置已保存')
}

async function resetMemorySystemConfig() {
  await configStore.updateConfigByKey('memory_system', {})
  await configStore.fetchConfig()
  initForms()
  ElMessage.success('记忆系统配置已重置')
}

async function saveMemoryScoringConfig() {
  await configStore.updateConfig({ memory_scoring: memoryScoringForm.value })
  ElMessage.success('记忆评分配置已保存')
}

async function resetMemoryScoringConfig() {
  await configStore.updateConfigByKey('memory_scoring', {})
  await configStore.fetchConfig()
  initForms()
  ElMessage.success('记忆评分配置已重置')
}

async function saveDatabaseConfig() {
  await configStore.updateConfig({
    milvus: databaseForm.value.milvus,
    kuzu: databaseForm.value.kuzu
  })
  ElMessage.success('数据库配置已保存')
}

async function resetDatabaseConfig() {
  await Promise.all([
    configStore.updateConfigByKey('milvus', {}),
    configStore.updateConfigByKey('kuzu', {})
  ])
  await configStore.fetchConfig()
  initForms()
  ElMessage.success('数据库配置已重置')
}

async function handleReinitialize() {
  try {
    await ElMessageBox.confirm(
      '确定要重新初始化配置吗？这将把所有配置重置为默认值。',
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const success = await configStore.reinitializeConfig()
    if (success) {
      await configStore.fetchConfig()
      initForms()
    }
  } catch {
    // 用户取消
  }
}
</script>

<style scoped>
.settings-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.settings-view h2 {
  margin: 0;
}

.settings-card,
.actions-card {
  margin-bottom: 0;
}

.actions-card h3 {
  margin: 0;
}

.actions {
  display: flex;
  gap: 12px;
}

.unit {
  margin-left: 8px;
  color: #909399;
}
</style>
