<template>
  <div class="task-sidebar">
    <div class="sidebar-header">
      <span class="sidebar-title">历史任务</span>
      <el-button text @click="$emit('close')">
        <el-icon><Fold /></el-icon>
      </el-button>
    </div>
    
    <div class="task-list" v-loading="loading">
      <!-- 置顶项 -->
      <template v-if="pinnedTasks.length > 0">
        <div
          v-for="task in pinnedTasks"
          :key="task.id"
          :class="['task-item', { active: task.id === activeTaskId }]"
          @click="$emit('select-task', task)"
        >
          <div class="task-status">
            <el-icon v-if="task.status === 'completed'" class="status-icon success"><CircleCheckFilled /></el-icon>
            <el-icon v-else-if="task.status === 'failed'" class="status-icon error"><CircleCloseFilled /></el-icon>
            <el-icon v-else-if="task.status === 'processing'" class="status-icon processing"><Loading /></el-icon>
            <el-icon v-else class="status-icon queued"><Clock /></el-icon>
          </div>
          
          <div class="task-info">
            <div class="task-title">{{ task.video_title || task.filename }}</div>
            <div class="task-time">{{ formatTime(task.created_at) }}</div>
          </div>

          <el-dropdown trigger="click" @command="(cmd: string) => handleCommand(cmd, task)" @click.stop>
            <el-icon class="more-btn"><More /></el-icon>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="unpin">
                  <el-icon><Star /></el-icon>
                  取消置顶
                </el-dropdown-item>
                <el-dropdown-item command="delete" divided>
                  <el-icon><Delete /></el-icon>
                  删除
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
        
        <div class="divider-line"></div>
      </template>

      <!-- 普通项 -->
      <div
        v-for="task in normalTasks"
        :key="task.id"
        :class="['task-item', { active: task.id === activeTaskId }]"
        @click="$emit('select-task', task)"
      >
        <div class="task-status">
          <el-icon v-if="task.status === 'completed'" class="status-icon success"><CircleCheckFilled /></el-icon>
          <el-icon v-else-if="task.status === 'failed'" class="status-icon error"><CircleCloseFilled /></el-icon>
          <el-icon v-else-if="task.status === 'processing'" class="status-icon processing"><Loading /></el-icon>
          <el-icon v-else class="status-icon queued"><Clock /></el-icon>
        </div>
        
        <div class="task-info">
          <div class="task-title">{{ task.video_title || task.filename }}</div>
          <div class="task-time">{{ formatTime(task.created_at) }}</div>
        </div>

        <el-dropdown trigger="click" @command="(cmd: string) => handleCommand(cmd, task)" @click.stop>
          <el-icon class="more-btn"><MoreFilled /></el-icon>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="pin">
                <el-icon><StarFilled /></el-icon>
                置顶
              </el-dropdown-item>
              <el-dropdown-item v-if="task.status === 'failed'" command="retry">
                <el-icon><RefreshRight /></el-icon>
                重试
              </el-dropdown-item>
              <el-dropdown-item command="delete" :divided="task.status === 'failed'">
                <el-icon><Delete /></el-icon>
                删除
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
      
      <div v-if="tasks.length === 0 && !loading" class="empty-state">
        暂无任务
      </div>
    </div>
    
    <!-- <div class="sidebar-footer">
      <el-button type="primary" class="new-task-btn" @click="$emit('new-task')">
        <el-icon><Plus /></el-icon>
        <span style="marginLeft: 10px">新任务</span>
      </el-button>
    </div> -->
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { CircleCheckFilled, CircleCloseFilled, Loading, Clock, Fold, Plus, MoreFilled, StarFilled, Star, RefreshRight, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { pinTask, unpinTask, deleteTask, retryTask } from '@/api/whisperApi'

interface Task {
  id: number
  filename: string
  status: string
  result: string | null
  created_at: string
  video_title?: string
  source_url?: string
  thumbnail_url?: string
  pinned?: boolean
}

const props = defineProps<{
  tasks: Task[]
  activeTaskId?: number
  loading?: boolean
}>()

const emit = defineEmits<{
  'select-task': [task: Task]
  'new-task': []
  'close': []
  'refresh': []
}>()

// 置顶任务
const pinnedTasks = computed(() => props.tasks.filter(t => t.pinned))

// 普通任务
const normalTasks = computed(() => props.tasks.filter(t => !t.pinned))

const handleCommand = async (command: string, task: Task) => {
  try {
    switch (command) {
      case 'pin':
        await pinTask(task.id)
        ElMessage.success('已置顶')
        emit('refresh')
        break
      case 'unpin':
        await unpinTask(task.id)
        ElMessage.success('已取消置顶')
        emit('refresh')
        break
      case 'delete':
        await ElMessageBox.confirm('确定删除该任务？', '提示', { type: 'warning' })
        await deleteTask(task.id)
        ElMessage.success('已删除')
        emit('refresh')
        break
      case 'retry':
        await retryTask(task.id)
        ElMessage.success('已重新提交')
        emit('refresh')
        break
    }
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e?.message || '操作失败')
    }
  }
}

const formatTime = (dateStr: string) => {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)
  
  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins} 分钟前`
  if (diffHours < 24) return `${diffHours} 小时前`
  if (diffDays < 7) return `${diffDays} 天前`
  
  return date.toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.task-sidebar {
  width: 280px;
  height: 100%;
  border-right: 1px solid #e4e7ed;
  background: #f0f2f5;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  overflow: hidden;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 1px solid #e4e7ed;
  background: #e8eaed;
  white-space: nowrap;
}

.sidebar-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  white-space: nowrap;
}

.task-list {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 8px;
}

.task-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
  min-width: 0;
}

.task-item:hover {
  background: #f5f7fa;
}

.task-item.active {
  background: #2563EB;
}

.task-item.active .task-title {
  color: #fff;
}

.task-item.active .task-time {
  color: rgba(255, 255, 255, 0.8);
}

.task-item.active .status-icon {
  color: #fff;
}

.task-item.active .more-btn {
  color: rgba(255, 255, 255, 0.8);
}

.task-item.active .more-btn:hover {
  background: #346EF6;
  color: #fff;
}

.task-status {
  flex-shrink: 0;
  margin-top: 2px;
}

.status-icon {
  font-size: 18px;
}

.status-icon.success {
  color: #67c23a;
}

.status-icon.error {
  color: #f56c6c;
}

.status-icon.processing {
  color: #409eff;
  animation: spin 1s linear infinite;
}

.status-icon.queued {
  color: #909399;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.task-info {
  flex: 1;
  min-width: 0;
}

.task-title {
  font-size: 14px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}

.task-time {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.more-btn {
  flex-shrink: 0;
  font-size: 28px;
  color: #909399;
  padding: 6px;
  border-radius: 50%;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.2s, background-color 0.2s;
}

.task-item.active .more-btn,
.task-item:hover .more-btn {
  opacity: 1;
}

.more-btn:hover {
  background: #e0e2e5;
  color: #606266;
}

.divider-line {
  height: 1px;
  background: #dcdfe6;
  margin: 8px 12px;
}

.empty-state {
  text-align: center;
  color: #909399;
  padding: 40px 0;
}

.sidebar-footer {
  padding: 12px;
  border-top: 1px solid #e4e7ed;
  flex-shrink: 0;
}

.new-task-btn {
  width: 100%;
  background: #2563EB;
  border-color: #2563EB;
}

.new-task-btn:hover {
  background: #1d4ed8;
  border-color: #1d4ed8;
}
</style>
