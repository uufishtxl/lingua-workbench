import axios from 'axios';
import { useAuthStore } from '@/stores/authStore';

const apiClient = axios.create({
  baseURL: '/api',
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
  async (error) => {
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
          }
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