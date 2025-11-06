import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import Login from '@/views/Login.vue'
import Register from '@/views/Register.vue'
import VerifyEmail from '@/views/VerifyEmail.vue'
import PhraseSeeker from '@/views/PhraseSeeker.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      name: "phrase-seeker",
      component: PhraseSeeker,
      meta: {
        layout: 'AppLayout',
        requiresAuth: true
      }
    },
    {
      path: '/login',
      name: 'login',
      component: Login,
      meta: {
        layout: 'AuthLayout',
      },
    },
    {
      path: '/register',
      name: 'register',
      component: Register,
      meta: {
        layout: 'AuthLayout'
      },
    },
     {
      path: '/verify-email',
      name: 'verify-email',
      component: VerifyEmail,
      meta: {
        layout: 'AuthLayout'
      },
    }
  ],
})

// 2. 【新增】设置“全局前置守卫”
router.beforeEach((to, from, next) => {
  // (在“守卫”内部，我们才能安全地“激活” store)
  const authStore = useAuthStore()
  const isAuthenticated = authStore.isAuthenticated // (检查用户是否登录)

  const requiresAuth = to.meta.requiresAuth as boolean
  const isAuthPage = to.name === 'login' || to.name === 'register'

  console.log("to.name", to.name, "isAuthenticated", isAuthenticated)

  // --- 逻辑 1 (你问的)：如果“已登录”，还想去“登录/注册页” ---
  if (isAuthPage && isAuthenticated) {
    // 阻止他，并把他“踢”回主页
    next({ name: 'phrase-seeker' })
  } 

  // --- 逻辑 2 (保护)：如果“未登录”，还想去“受保护的页面” ---
  else if (requiresAuth && !isAuthenticated) {
    // 阻止他，并把他“踢”回登录页
    next({ name: 'login' })
  } 

  // --- 逻辑 3 (放行)：所有其他情况 (e.g., 登录了去主页, 没登录去登录页) ---
  else {
    // 正常放行
    next() 
  }
})

export default router
