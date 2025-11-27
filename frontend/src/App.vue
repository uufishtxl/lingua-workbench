<script setup lang="ts">
// 1. 我们导入 Vue Router 的两个核心组件
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { computed } from 'vue'
// (我们顺便导入我们的“保安室”)
import { useAuthStore } from '@/stores/authStore'
import { layouts, type LayoutKey } from '@/utils/layouts'

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
}
</script>

<template>
  <component :is="layoutComponent">
    <RouterView />
  </component>
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

</style>