import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import Login from '@/views/Login.vue'
import Register from '@/views/Register.vue'
import VerifyEmail from '@/views/VerifyEmail.vue'
import PhraseSeeker from '@/views/PhraseSeeker.vue'
import AudioLab from '@/views/AudioLab.vue'
import EpisodeSelector from '@/views/EpisodeSelector.vue'
import LoadSource from '@/views/LoadSource.vue'
import AudioWorkbench from '@/views/AudioWorkbench.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/phrase-seeker",
      name: "phrase-seeker",
      component: PhraseSeeker,
      meta: {
        layout: 'AppLayout',
        requiresAuth: true
      }
    },
    {
      path: '/slicer/load-source',
      name: 'load-source',
      component: LoadSource,
      meta: {
        layout: 'AppLayout',
        requiresAuth: true
      }
    },
    {
      path: '/slicer/workbench/:id',
      name: 'audio-workbench',
      component: AudioWorkbench,
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
    },
    {
      path: '/episode-selector',
      name: 'episode-selector',
      component: EpisodeSelector,
      meta: {
        layout: 'AppLayout',
        requiresAuth: true
      }
    },
    {
      path: '/audio-lab',
      name: 'audio-lab',
      component: AudioLab,
      meta: {
        layout: 'AppLayout',
        requiresAuth: true
      }
    },
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/ReviewBoard.vue'),
      meta: {
        layout: 'AppLayout',
        requiresAuth: true
      }
    },
    {
      path: '/translations',
      name: 'translations',
      component: () => import('@/views/TranslationManager.vue'),
      meta: {
        layout: 'AppLayout',
        requiresAuth: true
      }
    },
    // Dev routes (开发专用)
    {
      path: '/dev/highlight-editor',
      name: 'dev-highlight-editor',
      component: () => import('@/views/dev/HighlightEditorDev.vue'),
      meta: {
        requiresAuth: false
      }
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
    next({ name: 'home' })
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
