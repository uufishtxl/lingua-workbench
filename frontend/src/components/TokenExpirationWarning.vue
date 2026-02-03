<template>
  <Transition name="slide-down">
    <div v-if="authStore.expirationWarningActive" class="token-warning-bar">
      <div class="warning-content">
        <el-icon class="warning-icon"><WarningFilled /></el-icon>
        <span class="warning-text">
          登录即将过期 <span class="countdown">{{ formattedTime }}</span>
        </span>
        <div class="warning-actions">
          <el-button v-if="$route.name === 'audio-workbench'" type="warning" size="small" @click="handleSaveNow" :loading="isSaving">
            <i-tabler-device-floppy class="mr-1" />
            立即保存
          </el-button>
          <el-button type="primary" size="small" @click="handleRefreshSession" :loading="isRefreshing">
            <i-tabler-refresh class="mr-1" />
            刷新登录
          </el-button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useAuthStore } from '@/stores/authStore';
import { WarningFilled } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';

// Use native CustomEvent for global save-before-expiration event
// Components can listen with: window.addEventListener('save-before-expiration', handler)
function emitSaveBeforeExpiration() {
  window.dispatchEvent(new CustomEvent('save-before-expiration'));
}

const authStore = useAuthStore();
const isSaving = ref(false);
const isRefreshing = ref(false);

// Format seconds as MM:SS
const formattedTime = computed(() => {
  const seconds = authStore.secondsUntilExpiration;
  if (seconds === null || seconds < 0) return '00:00';
  
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
});

const handleSaveNow = async () => {
  isSaving.value = true;
  try {
    // Emit global event for AudioSlicer to catch
    emitSaveBeforeExpiration();
    ElMessage.info('正在保存...');
    
    // Give components time to respond
    await new Promise(resolve => setTimeout(resolve, 500));
  } finally {
    isSaving.value = false;
  }
};

const handleRefreshSession = async () => {
  isRefreshing.value = true;
  try {
    const success = await authStore.refreshAccessToken();
    if (success) {
      ElMessage.success('登录已刷新');
    } else {
      ElMessage.error('刷新失败，请重新登录');
    }
  } finally {
    isRefreshing.value = false;
  }
};
</script>

<style scoped>
.token-warning-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 9999;
  background: linear-gradient(135deg, #ff9500 0%, #ff6b00 100%);
  color: white;
  padding: 12px 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
}

.warning-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  max-width: 1200px;
  margin: 0 auto;
}

.warning-icon {
  font-size: 20px;
  animation: pulse 1s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.warning-text {
  font-weight: 500;
  font-size: 14px;
}

.countdown {
  font-family: 'Consolas', 'Monaco', monospace;
  font-weight: 700;
  background: rgba(255, 255, 255, 0.2);
  padding: 2px 8px;
  border-radius: 4px;
  margin-left: 4px;
}

.warning-actions {
  display: flex;
  gap: 8px;
}

/* Transition animations */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.slide-down-enter-from {
  transform: translateY(-100%);
  opacity: 0;
}

.slide-down-leave-to {
  transform: translateY(-100%);
  opacity: 0;
}
</style>
