<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import { useRouter, RouterLink } from 'vue-router' // 保留 RouterLink 用于 Header
import logoUrl from '@/assets/logo.svg'

// 1. 引入 ElementPlus 图标
import {
  Document,
  Menu as IconMenu,
  HomeFilled,
  SwitchButton,
  UserFilled,
  Setting,
  QuestionFilled,
  // Clock,
  // Scissor
} from '@element-plus/icons-vue'

const isCollapse = ref(false)
const authStore = useAuthStore()
const router = useRouter()

const handleLogout = () => {
  authStore.logout()
  router.push({ name: 'login' })
}

// 2. 额外：处理 el-dropdown 的命令
const handleCommand = (command: string | number | object) => {
  if (command === 'logout') {
    handleLogout()
  }
}
</script>

<template>
  <el-container class="h-screen">
    <el-header class="shadow py-4 px-8 border-b-1 border-b-gray-300 flex justify-between items-center"
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

    <el-container>
      <el-aside width="auto" class="bg-slate-100 border-r-gray-300 border-r-1 flex flex-col">
        <el-menu :default-active="$route.path" router class="el-menu-vertical-demo"
          style="background-color: transparent; border-right: none;" :collapse="isCollapse">
          <el-sub-menu index="1">
            <template #title>
              <el-icon><icon-menu /></el-icon>
              <span>PhraseSeeker</span>
            </template>
            <el-menu-item index="/">
              <el-icon><Document /></el-icon>
              <span>Lookup</span>
            </el-menu-item>
            <el-menu-item index="/quiz">
              <el-icon><QuestionFilled /></el-icon>
              <span>Quiz</span>
            </el-menu-item>
          </el-sub-menu>
          <el-menu-item index="/history">
            <el-icon><setting /></el-icon>
            <span>History</span>
          </el-menu-item>
        </el-menu>

        <div class="mt-auto p-4 flex justify-center">
            <el-switch v-model="isCollapse" />
        </div>
      </el-aside>

      <el-main class="bg-slate-100">
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
</style>