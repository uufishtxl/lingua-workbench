// frontend/src/stores/authStore.ts
import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import type { Ref, ComputedRef } from 'vue'
import axios, { type AxiosError } from 'axios'
import apiClient from '@/api/axios'
import { getTokenExpiration, getTimeUntilExpiration, willExpireWithin } from '@/utils/tokenUtils'

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

// Warning threshold in minutes
const EXPIRATION_WARNING_MINUTES = 30 // in minutes

export const useAuthStore = defineStore('auth', () => {
  // --- 1. State (状态) ---
  const accessToken: Ref<string | null> = ref(null)
  // const refreshToken: Ref<string | null> = ref(null) // Refresh token is now in cookie
  const userEmail: Ref<string | null> = ref(null)
  const isRefreshing: Ref<boolean> = ref(false) // To prevent race conditions

  // Expiration monitoring state
  const expirationWarningActive: Ref<boolean> = ref(false)
  const secondsUntilExpiration: Ref<number | null> = ref(null)
  const silentRefreshAttempted: Ref<boolean> = ref(false) // Track if silent refresh was tried
  let expirationMonitorInterval: ReturnType<typeof setInterval> | null = null

  // --- 2. Getters (计算属性) ---
  const isAuthenticated: ComputedRef<boolean> = computed(() => accessToken.value != null)

  // Get token expiration time
  const tokenExpiresAt: ComputedRef<Date | null> = computed(() => {
    if (!accessToken.value) return null
    return getTokenExpiration(accessToken.value)
  })

  // --- 3. Actions (动作) ---

  /**
   * 检查 token 过期状态（内部函数）
   */
  function checkTokenExpiration(): void {
    console.log('检查 token 过期状态')
    if (!accessToken.value) {
      expirationWarningActive.value = false
      secondsUntilExpiration.value = null
      return
    }

    const remaining = getTimeUntilExpiration(accessToken.value)
    if (remaining === null) {
      expirationWarningActive.value = false
      secondsUntilExpiration.value = null
      return
    }

    secondsUntilExpiration.value = Math.floor(remaining / 1000)
    // console.log('Token 过期时间:', secondsUntilExpiration.value)

    // Check if we're within the warning threshold
    if (willExpireWithin(accessToken.value, EXPIRATION_WARNING_MINUTES)) {
      // First, try silent refresh (only once, not repeatedly)
      console.log("发现即将过期，isRefreshing.value, silentRefreshAttempted.value", isRefreshing.value, silentRefreshAttempted.value)
      if (!isRefreshing.value && !silentRefreshAttempted.value) {
        console.log('Token 即将过期，尝试静默刷新...')
        silentRefreshAttempted.value = true
        isRefreshing.value = true

        refreshAccessToken().then((success) => {
          if (success) {
            console.log('静默刷新成功')
            expirationWarningActive.value = false
            silentRefreshAttempted.value = false // Reset for next cycle
          } else {
            console.log('静默刷新失败，显示警告条')
            expirationWarningActive.value = true
          }
        }).finally(() => {
          isRefreshing.value = false
        })
      }

      // Show warning only if refresh is in progress or has failed
      if (isRefreshing.value || (silentRefreshAttempted.value && expirationWarningActive.value)) {
        // Keep warning active if we're still trying or failed
      }
    } else {
      expirationWarningActive.value = false
      silentRefreshAttempted.value = false
    }
  }

  /**
   * 启动过期监控定时器
   */
  function startExpirationMonitor(): void {
    console.log('启动过期监控定时器')
    // Clear any existing interval
    stopExpirationMonitor()

    // Check immediately
    checkTokenExpiration()

    // Then check every 30 seconds
    expirationMonitorInterval = setInterval(() => {
      checkTokenExpiration()
    }, 30000)
  }

  /**
   * 停止过期监控定时器
   */
  function stopExpirationMonitor(): void {
    if (expirationMonitorInterval) {
      clearInterval(expirationMonitorInterval)
      expirationMonitorInterval = null
    }
    expirationWarningActive.value = false
    secondsUntilExpiration.value = null
  }

  /**
   * 动作：登录
   */
  async function login(email: string, password: string): Promise<boolean> {
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

      // Start monitoring after login
      startExpirationMonitor()

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
  function logout(): void {
    accessToken.value = null
    // refreshToken.value = null // Refresh token is now in cookie
    userEmail.value = null

    delete apiClient.defaults.headers.common['Authorization']

    // Stop monitoring on logout
    stopExpirationMonitor()
  }

  /**
   * 动作：刷新令牌
   */
  async function refreshAccessToken(): Promise<boolean> {
    // If refresh token is in cookie, we don't need to send it in body
    // Note: apiClient.baseURL is '/api', so we use 'token/refresh/' not '/api/token/refresh/'
    // return false // 测试提示框 
    try {
      const response = await apiClient.post<RefreshResponse>('token/refresh/')
      accessToken.value = response.data.access
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${accessToken.value}`

      // Reset warning after successful refresh
      expirationWarningActive.value = false
      checkTokenExpiration()

      return true
    } catch (error) {
      console.error('Token refresh failed:', error)
      logout() // If refresh fails, log the user out
      return false
    }
  }

  // Watch for accessToken changes to restart monitoring
  watch(accessToken, (newToken) => {
    if (newToken) {
      startExpirationMonitor()
    } else {
      stopExpirationMonitor()
    }
  })

  // --- 4. Return (暴露) ---
  return {
    accessToken,
    // refreshToken, // Refresh token is now in cookie
    userEmail,
    isRefreshing,
    isAuthenticated,
    tokenExpiresAt,
    expirationWarningActive,
    secondsUntilExpiration,
    login,
    logout,
    refreshAccessToken,
    startExpirationMonitor,
    stopExpirationMonitor
  }
}, {
  persist: {
    pick: ['accessToken', 'userEmail']
  }
})