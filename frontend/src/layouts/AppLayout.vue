<template>
    <div>
  <aside class="w-64 bg-gray-800 text-white p-4">
        <h2>Lingua Workbench</h2>
        <nav class="mt-8">
          <RouterLink to="/" class="block py-2">PhraseSeeker</RouterLink>
          <RouterLink to="/history" class="block py-2">History</RouterLink>
          <RouterLink to="/slicer" class="block py-2">TrackSlicer</RouterLink>
        </nav>
      </aside>
      
      <div class="flex-1 flex flex-col">
        <header class="bg-white shadow p-4 flex justify-end">
          <div v-if="authStore.isAuthenticated">
            {{ authStore.userEmail }}
            <button @click="handleLogout" class="ml-4 text-blue-500">Logout</button>
          </div>
        </header>
        
        <main class="flex-1 p-8 bg-gray-100 overflow-y-auto">
          <RouterView />
        </main>
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { RouterLink, RouterView, useRouter } from 'vue-router'
  import { useAuthStore } from '@/stores/authStore'

  const authStore = useAuthStore()
  const router = useRouter()

  const handleLogout = () => {
    authStore.logout()
    // 登出后，跳转回登录页
    router.push({ name: 'login' })
  }
  </script>

  <style scoped>
  /* 我们仍然可以用 scoped CSS 来处理一些精细的样式 */
  nav a.router-link-exact-active {
    font-weight: bold;
    color: #42b983; /* Tailwind 的 'green-500' 之一 */
  }
  </style>