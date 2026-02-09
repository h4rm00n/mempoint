<template>
  <div class="persona-detail-view">
    <div class="detail-header">
      <el-button :icon="ArrowLeft" @click="goBack">返回列表</el-button>
    </div>

    <div v-loading="loading" class="detail-content">
      <el-card v-if="persona" class="info-card">
        <template #header>
          <h3>基本信息</h3>
        </template>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="名称">{{ persona.name || persona.id }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatDateTime(persona.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="更新时间">
            {{ formatDateTime(persona.updated_at) }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-card v-if="persona" class="edit-card">
        <template #header>
          <h3>编辑信息</h3>
        </template>
        <el-form :model="form" label-width="80px">
          <el-form-item label="描述">
            <el-input
              v-model="form.description"
              type="textarea"
              :rows="3"
              placeholder="请输入描述"
            />
          </el-form-item>
          <el-form-item label="System Prompt">
            <el-input
              v-model="form.system_prompt"
              type="textarea"
              :rows="10"
              placeholder="请输入 System Prompt"
            />
          </el-form-item>
        </el-form>
      </el-card>

      <el-card class="memories-card">
        <template #header>
          <div class="card-header">
            <h3>关联记忆</h3>
            <el-button size="small" :icon="Refresh" @click="loadMemories">刷新</el-button>
          </div>
        </template>
        <div v-loading="memoryStore.loading">
          <el-empty v-if="!memoryStore.hasMemories && !memoryStore.loading" description="暂无记忆" />
          <el-table v-else :data="memoryStore.memories" style="width: 100%">
            <el-table-column prop="content" label="内容" show-overflow-tooltip />
            <el-table-column prop="type" label="类型" width="100">
              <template #default="{ row }">
                <el-tag :type="row.type === 'long_term' ? 'primary' : 'success'" size="small">
                  {{ row.type === 'long_term' ? '长期' : '短期' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="access_count" label="访问次数" width="100" />
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="viewMemory(row.id)">
                  查看
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-card>

      <div class="save-button-container">
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePersonaStore } from '../stores/persona'
import { useMemoryStore } from '../stores/memory'
import type { PersonaUpdate } from '../types/persona'
import { ArrowLeft, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { formatDateTime } from '../utils/helpers'

const route = useRoute()
const router = useRouter()
const personaStore = usePersonaStore()
const memoryStore = useMemoryStore()

const loading = ref(false)
const saving = ref(false)
const persona = ref<any>(null)
const form = ref<PersonaUpdate>({
  description: '',
  system_prompt: ''
})

onMounted(async () => {
  const id = route.params.id as string
  await loadPersona(id)
  await loadMemories()
})

async function loadPersona(id: string) {
  loading.value = true
  persona.value = await personaStore.fetchPersona(id)
  if (persona.value) {
    form.value = {
      description: persona.value.description || '',
      system_prompt: persona.value.system_prompt || ''
    }
  }
  loading.value = false
}

async function loadMemories() {
  if (persona.value) {
    await memoryStore.fetchMemories({ persona_id: persona.value.id })
  }
}

function goBack() {
  router.push('/personas')
}

async function handleSave() {
  if (persona.value) {
    saving.value = true
    try {
      await personaStore.updatePersona(persona.value.id, form.value)
      persona.value = { ...persona.value, ...form.value }
      ElMessage.success('保存成功')
    } catch (error) {
      ElMessage.error('保存失败')
    } finally {
      saving.value = false
    }
  }
}

function viewMemory(_id: string) {
  router.push(`/memories`)
}
</script>

<style scoped>
.persona-detail-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.info-card,
.edit-card,
.prompt-card,
.memories-card {
  margin-bottom: 0;
}

.info-card h3,
.edit-card h3,
.prompt-card h3,
.memories-card h3 {
  margin: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
}

.save-button-container {
  display: flex;
  justify-content: flex-end;
  padding: 10px 0;
}
</style>
