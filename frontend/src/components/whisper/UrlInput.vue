<template>
  <div class="url-input">
    <el-input
      v-model="url"
      placeholder="粘贴 YouTube URL（支持 YouTube、Bilibili 等 1000+ 网站）"
      size="large"
      clearable
      @input="handleInput"
      @clear="handleClear"
      :disabled="isLoading"
    >
      <template #prefix>
        <el-icon><Link /></el-icon>
      </template>
      <template #append>
        <el-button
          type="primary"
          @click="handleFetchInfo"
          :loading="isLoading"
          :disabled="!isValidUrl"
        >
          获取预览
        </el-button>
      </template>
    </el-input>

    <!-- URL 格式提示 -->
    <div class="url-hint" v-if="url && !isValidUrl">
      <el-icon><Warning /></el-icon>
      <span>请输入有效的 URL 格式</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Link, Warning } from '@element-plus/icons-vue'
import { getVideoInfo } from '@/api/whisperApi'

// 视频信息接口
interface VideoInfo {
  title: string
  thumbnail_url: string
  duration: number
  author: string
  platform: string
}

// 事件
const emit = defineEmits<{
  preview: [info: VideoInfo]
  error: [message: string]
}>()

// 状态
const url = ref('')
const isLoading = ref(false)
let debounceTimer: ReturnType<typeof setTimeout> | null = null

// URL 验证正则
const URL_REGEX = /^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_+.~#?&//=]*)$/

// 计算属性：URL 是否有效
const isValidUrl = computed(() => {
  if (!url.value) return false
  return URL_REGEX.test(url.value)
})

// 处理输入（防抖）
const handleInput = () => {
  // 清除之前的定时器
  if (debounceTimer) {
    clearTimeout(debounceTimer)
  }

  // 如果 URL 无效，不触发预览
  if (!isValidUrl.value) {
    return
  }

  // 设置新的定时器（500ms 防抖）
  debounceTimer = setTimeout(() => {
    handleFetchInfo()
  }, 500)
}

// 处理清除
const handleClear = () => {
  url.value = ''
  if (debounceTimer) {
    clearTimeout(debounceTimer)
  }
}

// 获取视频信息
const handleFetchInfo = async () => {
  if (!isValidUrl.value || isLoading.value) {
    return
  }

  isLoading.value = true

  try {
    const info = await getVideoInfo(url.value)
    emit('preview', info)
  } catch (error: any) {
    // 处理错误
    let errorMessage = '获取视频信息失败'
    
    if (error.response) {
      // 服务器返回错误
      const status = error.response.status
      const detail = error.response.data?.detail || ''
      
      switch (status) {
        case 400:
          errorMessage = `无效的 URL: ${detail}`
          break
        case 404:
          errorMessage = `视频不存在: ${detail}`
          break
        case 403:
          errorMessage = `私有视频，无法访问: ${detail}`
          break
        case 503:
          errorMessage = `网络错误: ${detail}`
          break
        default:
          errorMessage = `获取失败 (${status}): ${detail}`
      }
    } else if (error.message) {
      errorMessage = error.message
    }
    
    emit('error', errorMessage)
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.url-input {
  width: 100%;
}

.url-hint {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
  color: #E6A23C;
  font-size: 12px;
}

/* 输入框样式增强 */
:deep(.el-input-group__append) {
  background-color: #409EFF;
  border-color: #409EFF;
  color: white;
}

:deep(.el-input-group__append:hover) {
  background-color: #66B1FF;
  border-color: #66B1FF;
}

:deep(.el-input-group__append:active) {
  background-color: #3A8EE6;
  border-color: #3A8EE6;
}

:deep(.el-input-group__append .el-button) {
  color: white;
  border: none;
}

:deep(.el-input-group__append .el-button:hover) {
  color: white;
  background-color: transparent;
}
</style>
