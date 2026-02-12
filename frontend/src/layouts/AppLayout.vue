<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import { useRouter, RouterLink } from 'vue-router' // 保留 RouterLink 用于 Header
import logoUrl from '@/assets/logo.svg'
import TokenExpirationWarning from '@/components/TokenExpirationWarning.vue'
import RiArchive2Fill from '~icons/ri/archive-2-fill';
// 1. 引入 ElementPlus 图标
import {
  Document,
  Menu as IconMenu,
  HomeFilled,
  SwitchButton,
  UserFilled,
  Setting,
  QuestionFilled,
  VideoPlay,
  GoldMedal,
  // Clock,
  Scissor,
} from '@element-plus/icons-vue'

const isCollapse = ref(false)
const authStore = useAuthStore()
const router = useRouter()

const handleLogout = () => {
  authStore.logout()
  router.push({ name: 'login' })
}

// Start token expiration monitor on mount (for page refresh scenarios)
onMounted(() => {
  if (authStore.isAuthenticated) {
    authStore.startExpirationMonitor()
  }
})

// 2. 额外：处理 el-dropdown 的命令
const handleCommand = (command: string | number | object) => {
  if (command === 'logout') {
    handleLogout()
  }
}

// Menu Items Configuration
const menuItems = [
  {
    index: '/',
    icon: HomeFilled,
    title: 'Home',
  },
  {
    index: '/dashboard',
    icon: GoldMedal,
    title: 'Dashboard',
  },
  {
    index: '1',
    icon: IconMenu,
    title: 'Phrase Seeker',
    children: [
      {
        index: '/phrase-seeker',
        icon: Document,
        title: 'Lookup',
      },
      {
        index: '/quiz',
        icon: QuestionFilled,
        title: 'Quiz',
      },
    ],
  },
  {
    index: '2',
    icon: IconMenu,
    title: 'Audio Slicer',
    children: [
      {
        index: '/slicer/load-source',
        icon: RiArchive2Fill,
        title: 'Load Source',
      },
      {
        index: '/audio-lab',
        icon: Scissor,
        title: 'Audio Clip',
      },
    ],
  },
  {
    index: '/history',
    icon: Setting,
    title: 'Setting',
  },
]
</script>

<template>
  <!-- Token Expiration Warning Bar -->
  <TokenExpirationWarning />
  
  <el-container class="h-screen overflow-hidden">
    <el-header class="shadow py-2 px-8 border-b-1 border-b-gray-300 flex justify-between items-center"
      style="background-color: #f1f5f9;">
      <div class="flex items-center">
        <img :src="logoUrl" alt="Logo" class="w-8 h-8 mr-3" />
        <h2 class="text-md font-bold">Lingua Workbench</h2>
      </div>

      <div v-if="authStore.isAuthenticated" class="flex items-center">
        <el-dropdown @command="handleCommand">
          <span class="el-dropdown-link" style="cursor: pointer; display: flex; align-items: center;">
            <el-avatar :size="32" :icon="UserFilled" />
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout">
                <el-icon>
                  <SwitchButton />
                </el-icon>
                Logout
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>

      <div class="flex items-center gap-4" v-else>
        <RouterLink to="/login">
          <el-link type="primary" :underline="false">Log in</el-link>
        </RouterLink>
        <RouterLink to="/register"> <el-button type="primary" size="small">Get Lingua Workbench for free!</el-button>
        </RouterLink>
      </div>
    </el-header>

    <el-container class="overflow-hidden">
      <el-aside width="auto" class="bg-slate-100 border-r-gray-300 border-r-1 flex flex-col">
        <el-menu :default-active="$route.path" router class="el-menu-vertical-demo"
          style="background-color: transparent; border-right: none;" :collapse="isCollapse">
          
          <template v-for="item in menuItems" :key="item.index">
            <!-- If item has children, render SubMenu -->
            <el-sub-menu v-if="item.children" :index="item.index">
              <template #title>
                <el-icon><component :is="item.icon" /></el-icon>
                <span>{{ item.title }}</span>
              </template>
              <el-menu-item v-for="child in item.children" :key="child.index" :index="child.index">
                <el-icon><component :is="child.icon" /></el-icon>
                <span>{{ child.title }}</span>
              </el-menu-item>
            </el-sub-menu>

            <!-- Else render MenuItem -->
            <el-menu-item v-else :index="item.index">
              <el-icon><component :is="item.icon" /></el-icon>
              <span>{{ item.title }}</span>
            </el-menu-item>
          </template>

        </el-menu>

        <div class="mt-auto p-4 flex justify-end">
          <el-switch v-model="isCollapse" />
        </div>
      </el-aside>

      <el-main class="bg-slate-100 overflow-hidden">
        <slot />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.el-menu-vertical-demo:not(.el-menu--collapse) {
  width: 250px;
}

.el-menu-vertical-demo {
  --el-menu-hover-bg-color: oklch(97.7% 0.013 236.62);
  --el-menu-bg-color: transparent;
}

/* 4. 为底部的登出按钮添加样式
  让它看起来像一个 el-menu-item
*/
.logout-button {
  display: flex;
  align-items: center;
  gap: 8px;
  /* 模拟 el-menu-item 的图标和文字间距 */
  padding: 12px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.logout-button:hover {
  background-color: var(--el-menu-hover-bg-color);
}

:deep(.el-main) {
  padding: 4px 8px;
}
</style>