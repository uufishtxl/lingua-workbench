<script setup lang="ts">
// 1. 我们导入 Vue Router 的两个核心组件
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { computed, ref, onMounted, onUnmounted, nextTick } from 'vue'
// (我们顺便导入我们的“保安室”)
import { useAuthStore } from '@/stores/authStore'
import { useChatStore } from '@/stores/chatStore'
import { layouts, type LayoutKey } from '@/utils/layouts'
// Documentation Assistant ChatBot
import ChatWidget from '@/components/ChatWidget.vue'
// Pomodoro Timer Widget
import PomodoroWidget from '@/components/PomodoroWidget.vue'

const authStore = useAuthStore()

const route = useRoute()

const layoutComponent = computed(() => {
  const layoutName = route.meta.layout as LayoutKey | undefined
  if (layoutName && layouts[layoutName]) {
    return layouts[layoutName]
  }
  return layouts['AppLayout']
})

// (我们创建一个登出方法)
const handleLogout = () => {
  authStore.logout()
  // 登出后，你可能想跳转回登录页
  // (我们稍后在 router/index.ts 里实现这个)
  // router.push({ name: 'login' }) 
  // router.push({ name: 'login' }) 
}

// Global Hotkey for Chat Interaction
const chatWidgetRef = ref()
const chatStore = useChatStore()

const handleGlobalKeydown = (e: KeyboardEvent) => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    if (chatStore.activeSelection) {
      e.preventDefault()
      const { lineId, text } = chatStore.activeSelection
      
      const prompt = `#${lineId} 的 "${text}" 部分：\n`
      
      chatStore.open()
      
      // Wait for v-if to render if needed
      nextTick(() => {
        chatWidgetRef.value?.insertTextAtCursor(prompt)
      })
      
      // Clear selection UI
      window.getSelection()?.removeAllRanges()
    }
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleGlobalKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalKeydown)
})

const handleAskAI = () => {
    if (chatStore.activeSelection) {
      const { lineId, text } = chatStore.activeSelection
      const prompt = `我要操作台词 #${lineId} 的 "${text}" 部分：\n`
      
      chatStore.open()
      nextTick(() => {
        chatWidgetRef.value?.insertTextAtCursor(prompt)
      })
      
      window.getSelection()?.removeAllRanges()
      chatStore.clearActiveSelection()
    }
}
</script>

<template>
  <component :is="layoutComponent">
    <RouterView />
  </component>
  <!-- Documentation Assistant ChatBot (global) -->
  <ChatWidget v-if="authStore.isAuthenticated" ref="chatWidgetRef" />

  <!-- Pomodoro Widget (global) -->
  <PomodoroWidget v-if="authStore.isAuthenticated" />

  <!-- Ask AI Floating Button -->
  <button
    v-if="chatStore.activeSelection && chatStore.selectionCoordinates"
    class="ask-ai-btn"
    :style="{
      top: `${chatStore.selectionCoordinates.y - 40}px`,
      left: `${chatStore.selectionCoordinates.x}px`
    }"
    @mousedown.prevent="handleAskAI"
  >
    Ask AI ✨
  </button>
</template>

<style scoped>
header {
  line-height: 1.5;
  max-height: 100vh;
  background-color: #f9f9f9;
  border-bottom: 1px solid #e0e0e0;
  padding: 1rem 2rem;
}

.wrapper {
  display: flex;
  justify-content: space-between; /* 导航在左，用户信息在右 */
  align-items: center;
  max-width: 1280px;
  margin: 0 auto;
}

nav {
  width: 100%;
  font-size: 1rem;
  text-align: left;
}

nav a {
  display: inline-block;
  padding: 0 1rem;
  border-left: 1px solid #ccc;
  cursor: pointer;
}
nav a:first-of-type {
  border: 0;
  padding-left: 0;
}

/* 这是 Vue Router 自动给“当前激活”的链接加的 class */
nav a.router-link-exact-active {
  color: #007bff;
  font-weight: bold;
}

.user-info {
    font-size: 0.9rem;
    color: #333;
}

.ask-ai-btn {
  position: fixed;
  transform: translateX(-50%);
  z-index: 10000;
  background: white;
  border: 1px solid #e5e7eb;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  color: #667eea; /* Widget gradient start color */
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  cursor: pointer;
  transition: all 0.2s;
  animation: popIn 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  display: flex;
  align-items: center;
  gap: 4px;
}

.ask-ai-btn:hover {
  background: #fdfdfd;
  transform: translateX(-50%) scale(1.05);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.25);
}

@keyframes popIn {
  from { opacity: 0; transform: translateX(-50%) scale(0.8); }
  to { opacity: 1; transform: translateX(-50%) scale(1); }
}
</style>