<template>
  <div class="task-status">
    <el-card class="status-card" :class="statusClass">
      <div class="status-content">
        <!-- 状态图标 -->
        <div class="status-icon">
          <el-icon v-if="status === 'queued'" class="rotating"><Loading /></el-icon>
          <el-icon v-else-if="status === 'processing'" class="rotating"><Loading /></el-icon>
          <el-icon v-else-if="status === 'completed'"><SuccessFilled /></el-icon>
          <el-icon v-else-if="status === 'failed'"><CircleCloseFilled /></el-icon>
        </div>

        <!-- 状态信息 -->
        <div class="status-info">
          <h3 class="status-title">{{ statusTitle }}</h3>
          <p class="status-message">{{ statusMessage }}</p>
          
          <!-- 进度条（处理中时显示） -->
          <el-progress
            v-if="status === 'processing'"
            :percentage="100"
            :indeterminate="true"
            :duration="2"
            class="progress-bar"
          />
        </div>

        <!-- 任务信息 -->
        <div class="task-info">
          <span class="task-id">任务 #{{ taskId }}</span>
          <span class="task-time">{{ formatTime(createdAt) }}</span>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Loading, SuccessFilled, CircleCloseFilled } from '@element-plus/icons-vue'

// Props
const props = defineProps<{
  taskId: number
  status: 'queued' | 'processing' | 'completed' | 'failed'
  createdAt?: string
  videoTitle?: string
}>()

// 状态标题
const statusTitle = computed(() => {
  switch (props.status) {
    case 'queued':
      return '排队中'
    case 'processing':
      return '处理中'
    case 'completed':
      return '已完成'
    case 'failed':
      return '失败'
    default:
      return '未知状态'
  }
})

// 状态消息
const statusMessage = computed(() => {
  switch (props.status) {
    case 'queued':
      return '任务正在排队等待处理...'
    case 'processing':
      return '正在下载音频并进行转录，请稍候...'
    case 'completed':
      return '转录完成！'
    case 'failed':
      return '转录失败，请重试'
    default:
      return ''
  }
})

// 状态样式类
const statusClass = computed(() => {
  return `status-${props.status}`
})

// 格式化时间
const formatTime = (time?: string): string => {
  if (!time) return ''
  const date = new Date(time)
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.task-status {
  margin: 20px 0;
}

.status-card {
  border-radius: 12px;
  transition: all 0.3s ease;
}

.status-card.status-queued {
  border-left: 4px solid #E6A23C;
}

.status-card.status-processing {
  border-left: 4px solid #409EFF;
}

.status-card.status-completed {
  border-left: 4px solid #67C23A;
}

.status-card.status-failed {
  border-left: 4px solid #F56C6C;
}

.status-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.status-icon {
  flex-shrink: 0;
  font-size: 32px;
}

.status-queued .status-icon {
  color: #E6A23C;
}

.status-processing .status-icon {
  color: #409EFF;
}

.status-completed .status-icon {
  color: #67C23A;
}

.status-failed .status-icon {
  color: #F56C6C;
}

.rotating {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.status-info {
  flex: 1;
}

.status-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 4px 0;
}

.status-message {
  font-size: 14px;
  color: #606266;
  margin: 0;
}

.progress-bar {
  margin-top: 8px;
}

.task-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.task-id {
  font-size: 12px;
  color: #909399;
}

.task-time {
  font-size: 12px;
  color: #C0C4CC;
}
</style>
