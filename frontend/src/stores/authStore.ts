// frontend/src/stores/authStore.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Ref, ComputedRef } from 'vue'
import axios, { type AxiosError } from 'axios'
import apiClient from '@/api/axios'

// 定义 API 响应的数据的 Shape
interface UserDetails {
    pk: number;
    usernmae: string;
    email: string;
    first_name: string;
    last_name: string;
}

// dj-rest-auth /login/ 接口返回的数据的 Shape
interface LoginResponse {
    access: string;
    refresh_token: string;
    user: UserDetails
}

// dj-rest-auth 注册/登录 失败时返回的Shape
export interface AuthErrorResponse {
    [key: string]: string[]
}

// const  API_BASE_URL = '/api'
// const AUTH_API_URL = `${API_BASE_URL}/auth/` 

// “保安室”
export const useAuthStore = defineStore('auth', () => {
  // --- 1. State (状态) ---
  // ref() 用于创建“响应式”变量
  const accessToken: Ref<string | null> = ref(null)  // 存放 JWT 令牌
  const userEmail: Ref<string | null> = ref(null)     // (可选) 存放登录用户的邮箱

  // --- 2. Getters (计算属性) ---
  // computed() 用于根据 state 派生新值
  const isAuthenticated: ComputedRef<boolean> = computed(() => accessToken.value != null)

  // --- 3. Actions (动作) ---

  /**
   * 动作：登录
   */
  async function login(email:string, password: string): Promise<boolean> {
    try {
      const response = await apiClient.post<LoginResponse>('auth/login/', {
        username: email,
        email: email,
        password: password
      })

      // 登录成功！
      accessToken.value = response.data.access // 从 `dj-rest-auth` 获取 token
      userEmail.value = response.data.user.email  // (dj-rest-auth 会返回 user 信息)

      // (重要) 把 Token 加到 axios 的全局请求头中
      // 这样，*之后*所有的 API 请求都会自动带上这个“通行证”
      axios.defaults.headers.common['Authorization'] = `Bearer ${accessToken.value}`
      console.log(response.data)
      return true // 返回成功

    } catch (e) {
      const error = e as AxiosError<AuthErrorResponse>
      console.error('Login failed:', error.response?.data)
      return false // 返回失败
    }
  }

  /**
   * 动作：登出
   */
  function logout():void {
    accessToken.value = null
    userEmail.value = null

    // (重要) 从全局请求头中移除“通行证”
    delete axios.defaults.headers.common['Authorization']
  }

  // --- 4. Return (暴露) ---
  // 把你需要“暴露”给组件的状态和动作 return 出去
  return {
    accessToken,
    userEmail,
    isAuthenticated,
    login,
    logout
  }
}, {
  // 【魔法】开启 Pinia 的持久化插件
  // 这会自动把上面 return 的所有 state (accessToken, userEmail)
  // 存入浏览器的 localStorage，实现“刷新也不掉线”
  persist: true, 
})