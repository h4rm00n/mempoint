<template>
  <div class="login-view">
    <el-card class="login-card">
      <template #header>
        <div class="card-header">
          <h2>MemPoint 登录</h2>
          <p class="subtitle">请输入 API Key 以继续</p>
        </div>
      </template>
      
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="0"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="apiKey">
          <el-input
            v-model="form.apiKey"
            type="password"
            placeholder="请输入 API Key"
            show-password
            size="large"
            clearable
          >
            <template #prefix>
              <el-icon><Key /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            @click="handleLogin"
            style="width: 100%"
          >
            登录
          </el-button>
        </el-form-item>
        
        <el-alert
          v-if="errorMessage"
          :title="errorMessage"
          type="error"
          :closable="false"
          show-icon
        />
        
        <div class="tips">
          <el-divider />
          <p class="tip-text">
            <el-icon><InfoFilled /></el-icon>
            提示：默认 API Key 为 <code>test_key</code>
          </p>
          <p class="tip-text">
            如需修改，请在后端 <code>config.exp.py</code> 中配置 <code>API_KEY</code>
          </p>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { ElMessage } from 'element-plus'
import { Key, InfoFilled } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import request from '../utils/request'

const router = useRouter()
const authStore = useAuthStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const errorMessage = ref('')

const form = reactive({
  apiKey: ''
})

const rules: FormRules = {
  apiKey: [
    { required: true, message: '请输入 API Key', trigger: 'blur' },
    { min: 1, message: 'API Key 不能为空', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    
    loading.value = true
    errorMessage.value = ''
    
    // 设置 API Key
    authStore.setApiKey(form.apiKey)
    
    // 验证 API Key 是否有效 - 尝试调用一个简单的 API
    try {
      // 使用 request (axios) 调用 API，自动处理 baseURL 和 Authorization 头
      await request.get('/v1/personas')

      ElMessage.success('登录成功')
      // 跳转到主页
      router.push('/chat')
    } catch (error: any) {
      console.error('API 验证失败:', error)
      
      // 检查是否是 401 错误
      if (error.response?.status === 401) {
        errorMessage.value = 'API Key 无效，请检查后重试'
        authStore.clearApiKey()
      } else {
        // 其他错误也认为登录成功（可能是服务器问题）
        ElMessage.success('登录成功')
        router.push('/chat')
      }
    }
  } catch (error) {
    console.error('表单验证失败', error)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-view {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-card {
  width: 100%;
  max-width: 450px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.card-header {
  text-align: center;
}

.card-header h2 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 28px;
  font-weight: 600;
}

.subtitle {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.tips {
  margin-top: 24px;
}

.tip-text {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 8px 0;
  color: #606266;
  font-size: 13px;
  line-height: 1.6;
}

.tip-text code {
  padding: 2px 6px;
  background: #f5f7fa;
  border: 1px solid #dcdfe6;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: #e6a23c;
}

.tip-text .el-icon {
  color: #409eff;
}

:deep(.el-form-item) {
  margin-bottom: 24px;
}

:deep(.el-input__wrapper) {
  padding: 12px 15px;
}

:deep(.el-alert) {
  margin-top: 16px;
}
</style>
