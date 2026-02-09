<template>
  <div class="personas-view">
  <div class="view-header">
    <h2>记忆体管理</h2>
    <div class="header-actions">
      <el-button :icon="Refresh" @click="personaStore.fetchPersonas()">刷新</el-button>
      <el-button type="primary" :icon="Plus" @click="showCreateDialog">新建记忆体</el-button>
    </div>
  </div>

    <div v-loading="personaStore.loading" class="personas-grid">
      <el-empty v-if="!personaStore.hasPersonas && !personaStore.loading" description="暂无记忆体" />
      <el-card
        v-for="persona in personaStore.personas"
        :key="persona.id"
        class="persona-card"
        shadow="hover"
      >
        <template #header>
          <div class="card-header">
            <div class="persona-name">
              <el-icon :size="20"><User /></el-icon>
              {{ persona.name || persona.id }}
            </div>
            <el-dropdown @command="(cmd: string) => handleCommand(cmd, persona.id)">
              <el-button circle :icon="MoreFilled" />
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="view">查看/编辑</el-dropdown-item>
                  <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </template>
        <div class="card-content">
          <p class="persona-description">{{ persona.description || '暂无描述' }}</p>
          <div class="persona-meta">
            <span>创建时间: {{ formatDateTime(persona.created_at) }}</span>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 创建对话框 -->
    <el-dialog
      v-model="dialogVisible"
      title="新建记忆体"
      width="500px"
    >
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="请输入记忆体名称" />
        </el-form-item>
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
            :rows="5"
            placeholder="请输入 System Prompt"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 删除确认对话框 -->
    <el-dialog v-model="deleteDialogVisible" title="确认删除" width="400px">
      <p>确定要删除这个记忆体吗？删除后将无法恢复。</p>
      <template #footer>
        <el-button @click="deleteDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="handleDelete">删除</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePersonaStore } from '../stores/persona'
import type { PersonaCreate } from '../types/persona'
import { Plus, User, MoreFilled, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { formatDateTime } from '../utils/helpers'

const router = useRouter()
const personaStore = usePersonaStore()

const dialogVisible = ref(false)
const deleteDialogVisible = ref(false)
const editingId = ref('')
const form = ref<PersonaCreate>({
  name: '',
  description: '',
  system_prompt: ''
})

onMounted(() => {
  personaStore.fetchPersonas()
})

function showCreateDialog() {
  form.value = {
    name: '',
    description: '',
    system_prompt: ''
  }
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.value.name.trim()) {
    ElMessage.warning('请输入记忆体名称')
    return
  }

  // 将 name 作为 id 发送给后端
  await personaStore.createPersona({
    id: form.value.name,
    description: form.value.description,
    system_prompt: form.value.system_prompt
  } as any)
  dialogVisible.value = false
}

function handleCommand(command: string, personaId: string) {
  switch (command) {
    case 'view':
      router.push(`/personas/${personaId}`)
      break
    case 'delete':
      editingId.value = personaId
      deleteDialogVisible.value = true
      break
  }
}

async function handleDelete() {
  const success = await personaStore.deletePersona(editingId.value)
  if (success) {
    deleteDialogVisible.value = false
  }
}
</script>

<style scoped>
.personas-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.view-header h2 {
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.personas-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.persona-card {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.persona-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.card-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.persona-description {
  margin: 0;
  color: #606266;
  line-height: 1.6;
  min-height: 60px;
}

.persona-meta {
  font-size: 12px;
  color: #909399;
}
</style>
