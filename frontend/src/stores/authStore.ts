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
    // refresh: string; // Refresh token is now in cookie
    user: UserDetails
}

interface RefreshResponse {
    access: string;
}

// dj-rest-auth 注册/登录 失败时返回的Shape
export interface AuthErrorResponse {
    [key: string]: string[]
}

export const useAuthStore = defineStore('auth', () => {
  // --- 1. State (状态) ---
  const accessToken: Ref<string | null> = ref(null)
  // const refreshToken: Ref<string | null> = ref(null) // Refresh token is now in cookie
  const userEmail: Ref<string | null> = ref(null)
  const isRefreshing: Ref<boolean> = ref(false) // To prevent race conditions

  // --- 2. Getters (计算属性) ---
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

      accessToken.value = response.data.access
      // refreshToken.value = response.data.refresh // Refresh token is now in cookie
      userEmail.value = response.data.user.email

      apiClient.defaults.headers.common['Authorization'] = `Bearer ${accessToken.value}`
      
      return true

    } catch (e) {
      const error = e as AxiosError<AuthErrorResponse>
      console.error('Login failed:', error.response?.data)
      return false
    }
  }

  /**
   * 动作：登出
   */
  function logout():void {
    accessToken.value = null
    // refreshToken.value = null // Refresh token is now in cookie
    userEmail.value = null

    delete apiClient.defaults.headers.common['Authorization']
  }

  /**
   * 动作：刷新令牌
   */
  async function refreshAccessToken(): Promise<boolean> {
    // If refresh token is in cookie, we don't need to send it in body
    try {
      const response = await apiClient.post<RefreshResponse>('/api/token/refresh/') // Correct endpoint
      accessToken.value = response.data.access
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${accessToken.value}`
      return true
    } catch (error) {
      console.error('Token refresh failed:', error)
      logout() // If refresh fails, log the user out
      return false
    }
  }

  // --- 4. Return (暴露) ---
  return {
    accessToken,
    // refreshToken, // Refresh token is now in cookie
    userEmail,
    isRefreshing,
    isAuthenticated,
    login,
    logout,
    refreshAccessToken
  }
}, {
  persist: true, 
})