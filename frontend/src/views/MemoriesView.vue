<template>
  <div class="memories-view">
    <div class="view-header">
      <h2>记忆管理</h2>
      <el-button type="primary" :icon="Plus" @click="showCreateDialog">新建记忆</el-button>
    </div>

    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="搜索">
          <el-input
            v-model="searchQuery"
            placeholder="搜索记忆内容..."
            clearable
            @clear="handleSearch"
            @keyup.enter="handleSearch"
          >
            <template #append>
              <el-button :icon="Search" @click="handleSearch" />
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="记忆体">
          <el-select
            v-model="filterForm.persona_id"
            placeholder="选择记忆体"
            clearable
            @change="loadMemories"
          >
            <el-option
              v-for="persona in personaStore.personas"
              :key="persona.id"
              :label="persona.name || persona.id"
              :value="persona.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="类型">
          <el-select
            v-model="filterForm.type"
            placeholder="选择类型"
            clearable
            @change="loadMemories"
          >
            <el-option label="长期记忆" value="long_term" />
            <el-option label="短期记忆" value="short_term" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button :icon="Refresh" @click="loadMemories">刷新</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div v-loading="memoryStore.loading" class="memories-list">
      <el-empty v-if="!memoryStore.hasMemories && !memoryStore.loading" description="暂无记忆" />
      <el-card
        v-for="memory in displayMemories"
        :key="memory.id"
        class="memory-card"
        shadow="hover"
      >
        <div class="memory-content">
          <div class="memory-header">
            <el-tag :type="memory.type === 'long_term' ? 'primary' : 'success'" size="small">
              {{ memory.type === 'long_term' ? '长期' : '短期' }}
            </el-tag>
          </div>
          <p class="memory-text">{{ memory.content }}</p>
          <div class="memory-meta">
            <span>访问次数: {{ memory.access_count }}</span>
            <span>创建时间: {{ formatDateTime(memory.created_at) }}</span>
          </div>
        </div>
        <div class="memory-actions">
          <el-button link type="primary" size="small" @click="viewMemory(memory.id)">
            查看
          </el-button>
          <el-button link type="primary" size="small" @click="showEditDialog(memory.id)">
            编辑
          </el-button>
          <el-button link type="danger" size="small" @click="handleDelete(memory.id)">
            删除
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑记忆' : '新建记忆'"
      width="500px"
    >
      <el-form :model="form" label-width="80px">
        <el-form-item label="记忆体" required>
          <el-select v-model="form.persona_id" placeholder="选择记忆体">
            <el-option
              v-for="persona in personaStore.personas"
              :key="persona.id"
              :label="persona.name || persona.id"
              :value="persona.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="类型" required>
          <el-select v-model="form.type" placeholder="选择类型">
            <el-option label="长期记忆" value="long_term" />
            <el-option label="短期记忆" value="short_term" />
          </el-select>
        </el-form-item>
        <el-form-item label="内容" required>
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="5"
            placeholder="请输入记忆内容"
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
      <p>确定要删除这条记忆吗？删除后将无法恢复。</p>
      <template #footer>
        <el-button @click="deleteDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="confirmDelete">删除</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useMemoryStore } from '../stores/memory'
import { usePersonaStore } from '../stores/persona'
import type { MemoryCreate } from '../types/memory'
import { Plus, Search, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { formatDateTime } from '../utils/helpers'

const memoryStore = useMemoryStore()
const personaStore = usePersonaStore()

const dialogVisible = ref(false)
const deleteDialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref('')
const searchQuery = ref('')
const filterForm = ref({
  persona_id: '',
  type: ''
})
const form = ref<MemoryCreate>({
  persona_id: '',
  type: 'long_term',
  content: ''
})

const displayMemories = computed(() => {
  if (searchQuery.value) {
    return memoryStore.searchResults.length > 0 ? memoryStore.searchResults : []
  }
  return memoryStore.memories
})

onMounted(async () => {
  await personaStore.fetchPersonas()
  await loadMemories()
})

async function loadMemories() {
  await memoryStore.fetchMemories(filterForm.value)
}

async function handleSearch() {
  if (searchQuery.value.trim()) {
    await memoryStore.searchMemories({ query: searchQuery.value })
  } else {
    memoryStore.clearSearchResults()
    await loadMemories()
  }
}

function showCreateDialog() {
  isEdit.value = false
  form.value = {
    persona_id: '',
    type: 'long_term',
    content: ''
  }
  dialogVisible.value = true
}

function showEditDialog(memoryId: string) {
  isEdit.value = true
  editingId.value = memoryId
  const memory = memoryStore.memories.find(m => m.id === memoryId)
  if (memory) {
    form.value = {
      persona_id: memory.persona_id,
      type: memory.type,
      content: memory.content
    }
  }
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.value.persona_id) {
    ElMessage.warning('请选择记忆体')
    return
  }
  if (!form.value.content.trim()) {
    ElMessage.warning('请输入记忆内容')
    return
  }

  if (isEdit.value) {
    await memoryStore.updateMemory(editingId.value, { content: form.value.content })
  } else {
    await memoryStore.createMemory(form.value)
  }
  dialogVisible.value = false
}

function handleDelete(memoryId: string) {
  editingId.value = memoryId
  deleteDialogVisible.value = true
}

async function confirmDelete() {
  const success = await memoryStore.deleteMemory(editingId.value)
  if (success) {
    deleteDialogVisible.value = false
  }
}

function viewMemory(id: string) {
  // 可以跳转到详情页或显示详情对话框
  console.log('查看记忆:', id)
}
</script>

<style scoped>
.memories-view {
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

.filter-card {
  margin-bottom: 0;
}

.memories-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.memory-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0;
}

.memory-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.memory-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.memory-text {
  margin: 0;
  color: #303133;
  line-height: 1.6;
}

.memory-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #909399;
}

.memory-actions {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-left: 16px;
}
</style>
