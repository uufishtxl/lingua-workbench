<template>
  <div class="w-full max-w-sm p-8 bg-white rounded-lg shadow-md">
    <h2 class="text-2xl font-bold text-center mb-6 text-gray-600">Create Account</h2>
    
    <form @submit.prevent="handleRegister">
      
      <div class="mb-4">
        <input
          v-model="email"
          type="email"
          id="email"
          placeholder="Email"
          required
          class="w-full px-4 py-3 bg-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-600 text-gray-600"
        />
      </div>
      
      <div class="mb-4">
        <input
          v-model="password"
          type="password"
          id="password"
          placeholder="Password"
          required
          class="w-full px-4 py-3 bg-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-600 text-gray-600"
        />
      </div>
      
      <div class="mb-6">
        <input
          v-model="password2"
          type="password"
          id="password2"
          placeholder="Confirm Password"
          required
          class="w-full px-4 py-3 bg-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-600 text-gray-600"
        />
      </div>
      
      <div v-if="errorMessage" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
        <span class="block sm:inline">{{ errorMessage }}</span>
      </div>
      
      <button
        type="submit"
        class="w-full bg-sky-600 text-white font-semibold py-3 rounded-lg hover:bg-sky-700 focus:outline-none focus:ring-2 focus:ring-sky-600 focus:ring-opacity-50 transition ease-in-out duration-150"
        :disabled="isLoading"
      >
        {{ isLoading ? 'REGISTERING...' : 'REGISTER' }}
      </button>
    </form>
    
    <div class="mt-6 text-center text-sm text-gray-600">
      Already have an account? 
      <RouterLink to="/login" class="text-sky-600 hover:text-sky-700 font-medium">Login here</RouterLink>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import axios, { type AxiosError} from 'axios'
import { useAuthStore, type AuthErrorResponse } from '@/stores/authStore'
import apiClient from '@/api/axios'

const email = ref('')
const password = ref('')
const password2 = ref('') // 6. 【新增】v-model 状态
const isLoading = ref(false)
const errorMessage = ref<string | null>(null)

const router = useRouter()
const authStore = useAuthStore()

// 7. 【核心】修改逻辑
const handleRegister = async () => {
  isLoading.value = true
  errorMessage.value = null
  
  // 8. 【新增】客户端验证
  if (password.value !== password2.value) {
    errorMessage.value = 'Passwords do not match.'
    isLoading.value = false
    return // 停止执行
  }

  if (password.value.length < 8) {
    errorMessage.value = 'Password must be at least 8 characters long.'
    isLoading.value = false
    return
  }

// 3. 检查是否包含字母 (用正则表达式)
  if (!/[a-zA-Z]/.test(password.value)) {
    errorMessage.value = 'Password must contain at least one letter.'
    isLoading.value = false
    return // 停止执行
  }

  // 4. 检查是否包含数字 (用正则表达式)
  if (!/\d/.test(password.value)) {
    errorMessage.value = 'Password must contain at least one number.'
    isLoading.value = false
    return // 停止执行
  }
  
  try {
    // 【【【【【【 核心修改在这里 】】】】】】
    await apiClient.post(
        'auth/registration/', 
        {
          // 1. 后端想要 'username'，我们就把 email 给它
          username: email.value, 
          
          // 2. Email 
          email: email.value,
          
          // 3. 后端想要 'password1', 而不是 'password'
          password1: password.value, 
          
          // 4. 'password2' 保持不变
          password2: password2.value
        }
    )

    isLoading.value = false
    
    router.push({name: 'verify-email', 'query': { 'from': 'register' }}) // 用 query 参数导航，这样 router.push会带上一个“凭证”，证明是从注册页合法过来的

  } catch (e) {
    // (我们之前写的“智能”错误处理 catch 块... 100% 不变)
    isLoading.value = false
    const error = e as AxiosError<AuthErrorResponse>
    // ...
  }
}
</script>

<style scoped>
/* 样式复用，无需修改 */
</style>