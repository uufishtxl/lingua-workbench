<template>
  <div class="w-full max-w-sm p-8 bg-white rounded-lg shadow-md">
    <h2 class="text-2xl font-bold text-center mb-6 text-gray-800">LOGIN</h2>
    
    <form @submit.prevent="handleLogin">
      <div class="mb-4">
        <input
          v-model="email"
          type="email"
          id="email"
          placeholder="Email"
          required
          class="w-full px-4 py-3 bg-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 text-gray-700"
        />
      </div>
      
      <div class="mb-6">
        <input
          v-model="password"
          type="password"
          id="password"
          placeholder="Password"
          required
          class="w-full px-4 py-3 bg-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 text-gray-700"
        />
      </div>
      
      <div v-if="errorMessage" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
        <span class="block sm:inline">{{ errorMessage }}</span>
      </div>
      
      <button
        type="submit"
        class="w-full bg-green-500 text-white font-semibold py-3 rounded-lg hover:bg-green-600 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-opacity-50 transition ease-in-out duration-150"
        :disabled="isLoading"
      >
        {{ isLoading ? 'LOGGING IN...' : 'LOGIN' }}
      </button>
    </form>
    
    <div class="mt-6 text-center text-sm text-gray-600">
      Not registered? 
      <RouterLink to="/register" class="text-green-500 hover:text-green-600 font-medium">Create an account</RouterLink>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'

const email = ref('')
const password = ref('')
const isLoading = ref(false)
const errorMessage = ref<string | null>(null)

const router = useRouter()
const authStore = useAuthStore()

const handleLogin = async () => {
  isLoading.value = true
  errorMessage.value = null
  
  const success = await authStore.login(email.value, password.value)
  
  isLoading.value = false
  
  if (success) {
    router.push({ name: 'home' }) 
  } else {
    errorMessage.value = 'Login failed. Please check your email or password.'
  }
}
</script>

<style scoped>
/* 使用 Tailwind 后，这里的 scoped style 通常会非常少，甚至为空 */
/* 仅用于那些 Tailwind 无法直接表达或非常特殊的组件内部样式 */
</style>