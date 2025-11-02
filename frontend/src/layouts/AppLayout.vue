<template>
  <div class="flex flex-col h-screen">
    <header class="bg-slate-100 shadow py-4 px-8 flex justify-between items-center border-b-1 border-b-gray-300">
      <div class="flex items-center">
        <img :src="logoUrl" alt="Logo" class="w-8 h-8 mr-3" />
        <h2 class="text-md font-bold">Lingua Workbench</h2>
      </div>
      <div v-if="authStore.isAuthenticated" class="user-info text-slate-700">
        Logged in as: <strong>{{ authStore.userEmail }}</strong>
        <a @click="handleLogout" href="#" class="ml-4 text-md text-blue-500 font-medium hover:underline">Logout</a>
      </div>
      <div class="flex items-center gap-4" v-else>
        <RouterLink to="/login" class="text-slate-700 text-sm font-bold hover:underline">Log in</RouterLink>
        <RouterLink class="bg-sky-600 p-2 text-xs rounded text-gray-100">Get Lingua Workbench for free!</RouterLink>
      </div>
    </header>

    <div class="flex flex-grow">
      <aside class="w-64 bg-slate-100 text-sm text-slate-700 py-4 px-2 border-r-gray-300 border-r-1">
      <nav class="mt-2 flex flex-col gap-2">
        <RouterLink to="/" class="block py-2 px-2 rounded hover:bg-slate-200">PhraseSeeker</RouterLink>
        <!-- <RouterLink to="/history" class="block py-2 px-2 rounded hover:bg-slate-200">History</RouterLink> -->
        <!-- <RouterLink to="/slicer" class="block py-2 px-2 rounded hover:bg-slate-200">TrackSlicer</RouterLink> -->
      </nav>
    </aside>
    <main class="flex-1 p-8 bg-slate-100 overflow-y-auto">
      <slot />
    </main>
    </div>

  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '@/stores/authStore'
import { useRouter, RouterLink } from 'vue-router'
import logoUrl from '@/assets/logo.svg'

const authStore = useAuthStore()
const router = useRouter()

const handleLogout = () => {
  authStore.logout()
  router.push({ name: 'login' })
}
</script>

<style scoped>
/* (你可以加一些 scoped 样式来微调) */
nav a.router-link-exact-active {
  background-color:oklch(92.9% 0.013 255.508);
  /* e.g., bg-indigo-600 */
}
</style>