<template>
  <div class="default-layout">
    <el-container>
      <el-header class="layout-header">
        <div class="header-left">
          <h1 class="logo">MemPoint</h1>
        </div>
        <el-menu
          :default-active="activeMenu"
          mode="horizontal"
          :ellipsis="false"
          router
          class="header-menu"
        >
          <el-menu-item index="/chat">
            <el-icon><ChatDotRound /></el-icon>
            <span>聊天</span>
          </el-menu-item>
          <el-menu-item index="/personas">
            <el-icon><User /></el-icon>
            <span>记忆体</span>
          </el-menu-item>
          <el-menu-item index="/memories">
            <el-icon><Document /></el-icon>
            <span>记忆</span>
          </el-menu-item>
          <el-menu-item index="/graph">
            <el-icon><Share /></el-icon>
            <span>图谱</span>
          </el-menu-item>
          <el-menu-item index="/settings">
            <el-icon><Setting /></el-icon>
            <span>配置</span>
          </el-menu-item>
        </el-menu>
        <div class="header-right">
          <el-button
            v-if="!authStore.hasApiKey()"
            type="primary"
            size="small"
            @click="showApiKeyDialog"
          >
            设置 API Key
          </el-button>
          <el-dropdown v-else>
            <el-button size="small">
              <el-icon><User /></el-icon>
              已登录
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="showApiKeyDialog">修改 API Key</el-dropdown-item>
                <el-dropdown-item @click="logout">退出</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="layout-main">
        <router-view />
      </el-main>
    </el-container>

    <!-- API Key 对话框 -->
    <el-dialog
      v-model="apiKeyDialogVisible"
      title="设置 API Key"
      width="400px"
    >
      <el-form :model="apiKeyForm" label-width="80px">
        <el-form-item label="API Key">
          <el-input
            v-model="apiKeyForm.key"
            type="password"
            placeholder="请输入 API Key"
            show-password
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="apiKeyDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveApiKey">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ChatDotRound,
  User,
  Document,
  Share,
  Setting,
  ArrowDown
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const apiKeyDialogVisible = ref(false)
const apiKeyForm = ref({
  key: authStore.apiKey || ''
})

const activeMenu = computed(() => route.path)

function showApiKeyDialog() {
  apiKeyForm.value.key = authStore.apiKey || ''
  apiKeyDialogVisible.value = true
}

function saveApiKey() {
  if (apiKeyForm.value.key.trim()) {
    authStore.setApiKey(apiKeyForm.value.key.trim())
    apiKeyDialogVisible.value = false
    ElMessage.success('API Key 已保存')
  }
}

async function logout() {
  try {
    await ElMessageBox.confirm(
      '确定要退出登录吗？',
      '确认退出',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    authStore.clearApiKey()
    ElMessage.success('已退出登录')
    router.push('/login')
  } catch {
    // 用户取消
  }
}
</script>

<style scoped>
.default-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.layout-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  background-color: #fff;
  border-bottom: 1px solid #e4e7ed;
}

.header-left {
  display: flex;
  align-items: center;
}

.logo {
  margin: 0;
  font-size: 24px;
  font-weight: bold;
  color: #409eff;
}

.header-menu {
  flex: 1;
  margin: 0 40px;
  border-bottom: none;
}

.header-right {
  display: flex;
  align-items: center;
}

.layout-main {
  background-color: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}
</style>
