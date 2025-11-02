// 在 src/main.ts
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import axios from 'axios' // <--- 导入 axios
import './styles/styles.css'
import router from './router'
import { useAuthStore } from './stores/authStore' // <--- 导入 authStore

import App from './App.vue'
// ...

const app = createApp(App)

const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)
app.use(pinia)

// --- 这是新增的关键逻辑 ---
// 必须在 app.use(pinia) 之后调用，这样 store 才能被正确初始化
const authStore = useAuthStore()

// 在应用加载时，检查 localStorage 中恢复的 token
// 如果 token 存在，必须手动重新设置 axios 的全局 Header
if (authStore.accessToken) {
  axios.defaults.headers.common['Authorization'] = `Bearer ${authStore.accessToken}`
}
// --- 关键逻辑结束 ---

app.use(router)
app.mount('#app')