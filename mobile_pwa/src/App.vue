<script setup lang="ts">
import { useAuthStore } from '@/stores/authStore'
import PomodoroWidget from './components/PomodoroWidget.vue'
import { ref } from 'vue'

const authStore = useAuthStore()

const email = ref('')
const password = ref('')
const isLoggingIn = ref(false)

async function handleLogin() {
  if (!email.value || !password.value) return
  isLoggingIn.value = true
  const success = await authStore.login(email.value, password.value)
  if (!success) {
    alert("登录失败，请检查账号密码")
  }
  isLoggingIn.value = false
}

</script>

<template>
  <div class="app-root">
    <template v-if="authStore.isAuthenticated">
      <PomodoroWidget />
    </template>
    <template v-else>
      <div class="login-container neumorphic-panel">
        <h1 class="title">LINGUA POMO</h1>
        <p class="subtitle">Please log in to your Django Backend</p>
        
        <input class="neu-input" type="email" v-model="email" placeholder="Email" />
        <input class="neu-input" type="password" v-model="password" placeholder="Password" @keyup.enter="handleLogin" />
        
        <button class="neumorphic-btn-accent login-btn" :disabled="isLoggingIn" @click="handleLogin">
          {{ isLoggingIn ? 'Logging in...' : 'Enter Focus Zone' }}
        </button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.app-root {
  width: 100vw;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--bg-color);
}

.login-container {
  width: 330px;
  padding: 40px 28px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
}

.title {
  font-size: 20px;
  font-weight: 200;
  letter-spacing: 4px;
  color: var(--text-main);
  margin: 0;
}

.subtitle {
  font-size: 11px;
  color: var(--text-secondary);
  letter-spacing: 1px;
  margin: 0 0 16px 0;
  text-align: center;
}

.neu-input {
  width: 100%;
  background: var(--bg-color);
  border: none;
  border-radius: 12px;
  padding: 14px 16px;
  color: var(--text-main);
  font-size: 14px;
  box-shadow: inset 4px 4px 8px var(--shadow-dark), 
              inset -4px -4px 8px var(--shadow-primary);
  outline: none;
  transition: all 0.2s;
  box-sizing: border-box;
}

.neu-input:focus {
  box-shadow: inset 6px 6px 12px var(--shadow-dark), 
              inset -6px -6px 12px var(--shadow-primary);
}

.login-btn {
  width: 100%;
  padding: 16px;
  font-weight: 600;
  letter-spacing: 2px;
  font-size: 13px;
  margin-top: 12px;
  text-transform: uppercase;
}
</style>
