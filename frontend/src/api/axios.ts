import axios from 'axios';
import { useAuthStore } from '@/stores/authStore';

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 5000, // 设置请求超时时间为 5 秒
});

// 创建请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 在这里，我们不能在模块顶层调用 useAuthStore()
    // 因为 Pinia 实例此时可能还未挂载到 Vue app 上
    const authStore = useAuthStore();

    if (authStore.isAuthenticated && authStore.accessToken) {
      // 为请求头添加 Authorization 字段
      config.headers.Authorization = `Bearer ${authStore.accessToken}`;
    }
    return config;
  },
  (error) => {
    // 处理请求错误
    return Promise.reject(error);
  }
);

export default apiClient;