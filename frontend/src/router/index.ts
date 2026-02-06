import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { title: '登录', requiresAuth: false }
  },
  {
    path: '/',
    redirect: '/chat'
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('../views/ChatView.vue'),
    meta: { title: '聊天', requiresAuth: true }
  },
  {
    path: '/personas',
    name: 'Personas',
    component: () => import('../views/PersonasView.vue'),
    meta: { title: '记忆体管理', requiresAuth: true }
  },
  {
    path: '/personas/:id',
    name: 'PersonaDetail',
    component: () => import('../views/PersonaDetailView.vue'),
    meta: { title: '记忆体详情', requiresAuth: true }
  },
  {
    path: '/memories',
    name: 'Memories',
    component: () => import('../views/MemoriesView.vue'),
    meta: { title: '记忆管理', requiresAuth: true }
  },
  {
    path: '/graph',
    name: 'Graph',
    component: () => import('../views/GraphView.vue'),
    meta: { title: '知识图谱', requiresAuth: true }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/SettingsView.vue'),
    meta: { title: '配置管理', requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  document.title = `${to.meta.title || 'MemPoint'} - MemPoint`
  
  // 检查路由是否需要认证
  const requiresAuth = to.meta.requiresAuth !== false
  
  if (requiresAuth) {
    const authStore = useAuthStore()
    
    // 如果需要认证但没有 API Key，重定向到登录页
    if (!authStore.hasApiKey()) {
      next('/login')
      return
    }
  } else {
    // 如果是登录页且已有 API Key，重定向到首页
    if (to.path === '/login') {
      const authStore = useAuthStore()
      if (authStore.hasApiKey()) {
        next('/chat')
        return
      }
    }
  }
  
  next()
})

export default router
