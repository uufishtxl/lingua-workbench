import axios from 'axios';
import { useAuthStore } from '@/stores/authStore';
import { ElMessageBox } from 'element-plus';
import router from '@/router';

// 告诉 Axios：去浏览器的 Cookie 里找叫 'csrftoken' 的东西
axios.defaults.xsrfCookieName = 'csrftoken';
// 告诉 Axios：发请求的时候，把它塞进一个叫 'X-CSRFToken' 的请求头里发给后端
axios.defaults.xsrfHeaderName = 'X-CSRFToken';


const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 60000, // 60 seconds for AI requests
  withCredentials: true, // Crucial for sending cookies (refresh token)
});

// Create request interceptor
apiClient.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore();
    if (authStore.isAuthenticated && authStore.accessToken) {
      config.headers.Authorization = `Bearer ${authStore.accessToken}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Create response interceptor
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error: any) => {
    const originalRequest = error.config;
    const authStore = useAuthStore();

    // Check if the error is 401 and it's not a retry request
    // Note: error.response may be undefined for network errors
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      // Prevent multiple refresh calls
      if (!authStore.isRefreshing) {
        authStore.isRefreshing = true;
        try {
          const refreshed = await authStore.refreshAccessToken();
          if (refreshed) {
            // Update the header for the original request
            originalRequest.headers.Authorization = `Bearer ${authStore.accessToken}`;
            // Retry the original request
            return apiClient(originalRequest);
          } else {
            // Refresh failed (or was rejected by server)
            throw new Error("Refresh failed");
          }
        } catch (refreshError) {
          // Handle refresh failure: Session expired
          authStore.logout(); // Clear local state

          // Show blocking alert
          try {
            await ElMessageBox.alert('登录已失效，请重新登录', '会话过期', {
              confirmButtonText: '确定',
              type: 'warning',
              showClose: false, // Force user to click OK
              closeOnClickModal: false,
              closeOnPressEscape: false,
            });
          } catch {
            // Ignore cancel errors if any, though we disabled ways to cancel
          }

          // Redirect to login
          router.push({ name: 'login' });
          return Promise.reject(error);
        } finally {
          authStore.isRefreshing = false;
        }
      } else {
        // Wait for the token to be refreshed
        return new Promise((resolve, reject) => {
          const interval = setInterval(() => {
            if (!authStore.isRefreshing) {
              clearInterval(interval);
              if (authStore.isAuthenticated) {
                originalRequest.headers.Authorization = `Bearer ${authStore.accessToken}`;
                resolve(apiClient(originalRequest));
              } else {
                reject(error);
              }
            }
          }, 100);
        });
      }
    }

    // For other errors, just reject them
    return Promise.reject(error);
  }
);

export default apiClient;