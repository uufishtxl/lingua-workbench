<template>
  <div class="whisper-view">
    <div class="main-layout">
      <!-- 侧边栏 -->
      <Transition name="sidebar">
        <TaskSidebar
          v-if="showSidebar"
          :tasks="taskList"
          :active-task-id="currentTask?.id"
          :loading="isLoadingTasks"
          @select-task="handleSelectTask"
          @new-task="handleNewTask"
          @close="showSidebar = false"
          @refresh="loadTaskList"
        />
      </Transition>
      
      <!-- 内容区 -->
      <div class="content-area">
        <!-- 页面头部 -->
        <div class="page-header">
          <div class="header-left">
            <el-button
              v-if="!showSidebar"
              class="sidebar-toggle"
              :icon="Expand"
              text
              @click="showSidebar = true"
            />
            <div class="title-row">
              <h1>智能转录</h1>
              <span class="powered-badge">
                <el-icon><Cpu /></el-icon>
                POWERED BY WHISPER
              </span>
            </div>
          </div>
          <div v-if="currentTask?.status === 'completed'" class="header-right">
            <el-button type="primary" class="new-transcribe-btn" @click="handleReset">
              <el-icon><Plus /></el-icon>
              <span style="marginLeft: 10px">新任务</span>
            </el-button>
          </div>
        </div>

        <!-- 空状态：新建转录 -->
        <div v-if="!currentTask && !videoInfo" class="welcome-section">
          <!-- 功能介绍 -->
          <div class="intro-section">
            <h2 class="intro-title">开始新的转录项目</h2>
            <p class="intro-desc">利用先进的 Whisper 模型，精准将音频及视频转换为结构化文本。支持超过 90 种语言的自动识别与翻译。</p>
          </div>

          <!-- 主工作区 -->
          <div class="model-selector">
            <el-radio-group v-model="whisperModel" size="default">
              <el-radio-button value="tiny">最快</el-radio-button>
              <el-radio-button value="base">推荐</el-radio-button>
              <el-radio-button value="small">更准</el-radio-button>
              <el-radio-button value="medium">高精度</el-radio-button>
              <el-radio-button value="large">最高精度</el-radio-button>
            </el-radio-group>
          </div>
          <div class="input-workspace">
            <!-- YouTube 链接区域 -->
            <div :class="['input-card', { disabled: isTranscribing }]">
              <div class="card-icon youtube">
                <el-icon :size="32"><VideoCamera /></el-icon>
              </div>
              <h3 class="card-title">输入 YouTube 链接</h3>
              <p class="card-desc">粘贴视频 URL 即可直接提取音频进行转录，无需下载文件。</p>
              <el-input
                v-model="urlInput"
                placeholder="https://www.youtube.com/watch?v=..."
                size="large"
                clearable
                :disabled="isTranscribing"
                @input="handleUrlInput"
              >
                <template #prefix>
                  <el-icon><Link /></el-icon>
                </template>
              </el-input>
              <el-button
                type="primary"
                class="fetch-btn"
                :loading="isLoading"
                :disabled="!isValidUrl || isTranscribing"
                @click="handleFetchPreview"
              >
                获取预览
                <el-icon class="el-icon--right"><ArrowRight /></el-icon>
              </el-button>
            </div>

            <!-- 分割线 -->
            <div class="divider-vertical">
              <span class="divider-text">或</span>
            </div>

            <!-- 上传本地文件区域 -->
            <div :class="['input-card', { disabled: isLoading }]">
              <div class="card-icon upload">
                <el-icon :size="32"><Upload /></el-icon>
              </div>
              <h3 class="card-title">上传本地文件</h3>
              <p class="card-desc">点击或拖拽文件到此开始转录</p>
              <el-upload
                class="upload-area"
                drag
                :auto-upload="false"
                :on-change="handleFileChange"
                accept="audio/*,video/*"
                :limit="1"
                :disabled="isLoading"
              >
                <div class="upload-content">
                  <el-icon :size="40"><UploadFilled /></el-icon>
                </div>
              </el-upload>
              <div class="format-badges">
                <span class="format-badge">MP3</span>
                <span class="format-badge">WAV</span>
                <span class="format-badge">M4A</span>
                <span class="format-badge">MP4</span>
              </div>
              <p class="format-hint">支持 mp3, m4a, wav, flac, mp4 等格式</p>
            </div>
          </div>

          <!-- 底部亮点 -->
          <div class="highlights-divider"></div>
          <div class="highlights">
            <div class="highlight-item">
              <el-icon class="highlight-icon"><Aim /></el-icon>
              <div>
                <h4>高精度识别</h4>
                <p>基于 OpenAI Whisper 模型，准确率高达 95%+</p>
              </div>
            </div>
            <div class="highlight-item">
              <el-icon class="highlight-icon"><Lock /></el-icon>
              <div>
                <h4>隐私保护</h4>
                <p>本地部署处理，数据不上传第三方服务器</p>
              </div>
            </div>
            <div class="highlight-item">
              <el-icon class="highlight-icon"><ChatDotRound /></el-icon>
              <div>
                <h4>多语言支持</h4>
                <p>支持 90+ 种语言自动识别与翻译</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 视频预览区域 -->
        <div v-if="videoInfo && !currentTask" class="preview-section">
          <el-card class="preview-card">
            <template #header>
              <div class="card-header">
                <span>视频预览</span>
                <div class="header-actions">
                  <el-button type="primary" @click="handleStartTranscribe" :loading="isTranscribing">
                    开始转录
                  </el-button>
                </div>
              </div>
            </template>

            <div class="preview-content">
              <div class="thumbnail-wrapper">
                <img
                  :src="videoInfo.thumbnail_url"
                  :alt="videoInfo.title"
                  class="thumbnail"
                  @error="handleThumbnailError"
                />
                <div class="duration-badge">
                  {{ formatDuration(videoInfo.duration) }}
                </div>
              </div>

              <div class="video-info">
                <h3 class="video-title">{{ videoInfo.title }}</h3>
                <div class="video-meta">
                  <span class="author">
                    <el-icon><User /></el-icon>
                    {{ videoInfo.author }}
                  </span>
                  <span class="platform">
                    <el-icon><VideoCamera /></el-icon>
                    {{ videoInfo.platform }}
                  </span>
                </div>
              </div>
            </div>
          </el-card>
        </div>

        <!-- 任务状态 -->
        <TaskStatus
          v-if="currentTask && currentTask.status !== 'completed'"
          :task-id="currentTask.id"
          :status="currentTask.status"
          :created-at="currentTask.created_at"
          :video-title="currentTask.video_title"
        />

        <!-- 转录结果 -->
        <div v-if="currentTask?.status === 'completed' && currentTask.result" class="result-section">
          <el-card class="result-card">
            <!-- <template #header>
              <div class="card-header">
                <span>转录结果</span>
              </div>
            </template> -->
            
            <TranscriptViewer
              v-if="parsedSegments.length > 0"
              :video-url="videoSourceUrl"
              :segments="parsedSegments"
              :title="currentTask.video_title"
            />
            
            <div v-else class="result-content">
              <pre class="result-text">{{ currentTask.result }}</pre>
            </div>
          </el-card>
        </div>

        <!-- 错误提示 -->
        <el-alert
          v-if="errorMessage"
          :title="errorMessage"
          type="error"
          show-icon
          closable
          @close="errorMessage = ''"
          class="error-alert"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { 
  User, VideoCamera, Loading, UploadFilled, Expand, Cpu, 
  Link, ArrowRight, Upload, Aim, Lock, ChatDotRound, Plus
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import TaskSidebar from '@/components/whisper/TaskSidebar.vue'
import TaskStatus from '@/components/whisper/TaskStatus.vue'
import TranscriptViewer from '@/components/whisper/TranscriptViewer.vue'
import ExportButton from '@/components/whisper/ExportButton.vue'
import { getVideoInfo, transcribeUrl, transcribeAudio, getTaskStatus, getTasks } from '@/api/whisperApi'

interface VideoInfo {
  title: string
  thumbnail_url: string
  duration: number
  author: string
  platform: string
  url: string
}

interface Task {
  id: number
  status: 'queued' | 'processing' | 'completed' | 'failed'
  result: string | null
  created_at: string
  video_title?: string
  source_url?: string
  thumbnail_url?: string
}

// URL 相关
const urlInput = ref('')
const URL_REGEX = /^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_+.~#?&//=]*)$/
const isValidUrl = computed(() => urlInput.value && URL_REGEX.test(urlInput.value))

// 状态
const videoInfo = ref<VideoInfo | null>(null)
const isLoading = ref(false)
const isTranscribing = ref(false)
const errorMessage = ref('')
const currentTask = ref<Task | null>(null)
const whisperModel = ref('base')
const taskList = ref<Task[]>([])
const isLoadingTasks = ref(false)
const showSidebar = ref(false)

let debounceTimer: ReturnType<typeof setTimeout> | null = null
let pollTimer: ReturnType<typeof setInterval> | null = null

// URL 输入处理
const handleUrlInput = () => {
  if (debounceTimer) clearTimeout(debounceTimer)
  if (!isValidUrl.value) return
  debounceTimer = setTimeout(() => {
    handleFetchPreview()
  }, 800)
}

// 获取预览
const handleFetchPreview = async () => {
  if (!isValidUrl.value || isLoading.value) return
  isLoading.value = true
  errorMessage.value = ''
  try {
    const info = await getVideoInfo(urlInput.value)
    videoInfo.value = info
  } catch (error: any) {
    errorMessage.value = error.response?.data?.detail || '获取视频信息失败'
  } finally {
    isLoading.value = false
  }
}

// 文件上传
const handleFileChange = async (file: any) => {
  if (!file?.raw) return
  isTranscribing.value = true
  errorMessage.value = ''
  try {
    const response = await transcribeAudio(file.raw, {
      filename: file.name,
      skipLlm: true
    })
    currentTask.value = {
      id: response.task_id,
      status: 'queued',
      result: null,
      created_at: new Date().toISOString(),
      video_title: file.name
    }
    startPolling(response.task_id)
    ElMessage.success('任务已提交')
  } catch (error: any) {
    errorMessage.value = `提交失败: ${error.response?.data?.detail || error.message}`
  } finally {
    isTranscribing.value = false
  }
}

// 开始转录
const handleStartTranscribe = async () => {
  if (!videoInfo.value?.url) return
  isTranscribing.value = true
  errorMessage.value = ''
  try {
    const response = await transcribeUrl(videoInfo.value.url, {
      skipLlm: true,
      whisperModel: whisperModel.value,
      videoTitle: videoInfo.value.title,
      thumbnailUrl: videoInfo.value.thumbnail_url,
      duration: videoInfo.value.duration
    })
    currentTask.value = {
      id: response.task_id,
      status: 'queued',
      result: null,
      created_at: new Date().toISOString(),
      video_title: videoInfo.value.title,
      source_url: videoInfo.value.url,
      thumbnail_url: videoInfo.value.thumbnail_url
    }
    startPolling(response.task_id)
    ElMessage.success('任务已提交')
  } catch (error: any) {
    errorMessage.value = `提交失败: ${error.response?.data?.detail || error.message}`
  } finally {
    isTranscribing.value = false
  }
}

// 轮询任务状态
const startPolling = (taskId: number) => {
  stopPolling()
  pollTimer = setInterval(async () => {
    try {
      const task = await getTaskStatus(taskId)
      if (task && currentTask.value) {
        currentTask.value = { ...currentTask.value, ...task }
      }
      if (task.status === 'completed' || task.status === 'failed') {
        stopPolling()
        if (task.status === 'completed') {
          ElMessage.success('转录完成！')
        } else {
          ElMessage.error('转录失败')
        }
        loadTaskList()
      }
    } catch (error) {
      console.error('轮询失败:', error)
    }
  }, 1000)
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

// 任务列表
const loadTaskList = async () => {
  isLoadingTasks.value = true
  try {
    const tasks = await getTasks()
    taskList.value = Array.isArray(tasks) ? tasks : []
  } catch (error) {
    console.error('加载任务列表失败:', error)
  } finally {
    isLoadingTasks.value = false
  }
}

const handleSelectTask = (task: Task) => {
  currentTask.value = task
  if (task.source_url) {
    videoInfo.value = {
      url: task.source_url,
      title: task.video_title || '',
      thumbnail_url: task.thumbnail_url || '',
      duration: 0,
      author: '',
      platform: ''
    }
  } else {
    videoInfo.value = null
  }
}

const handleNewTask = () => {
  currentTask.value = null
  videoInfo.value = null
  urlInput.value = ''
}

const handleReset = () => {
  handleNewTask()
}

// 计算属性
const parsedSegments = computed(() => {
  if (!currentTask.value?.result) return []
  try {
    const parsed = JSON.parse(currentTask.value.result)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
})

const videoSourceUrl = computed(() => {
  if (videoInfo.value?.url) {
    const videoId = videoInfo.value.url.match(/(?:v=|youtu\.be\/)([a-zA-Z0-9_-]+)/)?.[1]
    if (videoId) return `https://www.youtube.com/embed/${videoId}`
  }
  return ''
})

const formatDuration = (seconds: number): string => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

const handleThumbnailError = (e: Event) => {
  const img = e.target as HTMLImageElement
  img.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIwIiBoZWlnaHQ9IjE4MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMzIwIiBoZWlnaHQ9IjE4MCIgZmlsbD0iI2Y1ZjVmNSIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiM5OTkiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5ObyBUaHVtYm5haWw8L3RleHQ+PC9zdmc+'
}

onMounted(() => {
  loadTaskList()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.whisper-view {
  height: calc(100vh - 68px);
  overflow: hidden;
  background: #f5f7fa;
}

.main-layout {
  display: flex;
  height: 100%;
}

.content-area {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
}

.page-header {
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

.new-transcribe-btn {
  background: #2563EB;
  border-color: #2563EB;
}

.new-transcribe-btn:hover {
  background: #1d4ed8;
  border-color: #1d4ed8;
}

.sidebar-toggle {
  font-size: 18px;
  color: #606266;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.page-header h1 {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.powered-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  background: #2563EB;
  color: white;
  font-size: 11px;
  font-weight: 500;
  border-radius: 4px;
  letter-spacing: 0.5px;
}

.powered-badge .el-icon {
  font-size: 12px;
}

/* 欢迎页面 */
.welcome-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px 0;
}

.intro-section {
  text-align: center;
  margin-bottom: 48px;
}

.intro-title {
  font-size: 28px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0 0 12px 0;
}

.intro-desc {
  font-size: 15px;
  color: #6b7280;
  margin: 0;
  max-width: 560px;
  line-height: 1.6;
}

/* 输入工作区 */
.input-workspace {
  display: flex;
  gap: 24px;
  width: 100%;
  padding: 0 40px;
  margin-bottom: 48px;
  box-sizing: border-box;
}

.input-card {
  flex: 1;
  background: white;
  border-radius: 12px;
  padding: 28px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  border: 1px solid #e5e7eb;
  transition: opacity 0.3s, pointer-events 0.3s;
}

.input-card.disabled {
  opacity: 0.5;
  pointer-events: none;
}

.card-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.card-icon.youtube {
  background: #fee2e2;
  color: #dc2626;
}

.card-icon.upload {
  background: #dbeafe;
  color: #2563eb;
}

.card-title {
  font-size: 17px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 8px 0;
}

.card-desc {
  font-size: 13px;
  color: #9ca3af;
  margin: 0 0 20px 0;
  line-height: 1.5;
}

.input-card .el-input {
  width: 100%;
  margin-bottom: 12px;
}

.fetch-btn {
  width: 100%;
  background: #2563EB;
  border-color: #2563EB;
}

.fetch-btn:hover {
  background: #1d4ed8;
  border-color: #1d4ed8;
}

/* 精度选择器 */
.model-selector {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

.model-label {
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
}

/* 分割线 */
.divider-vertical {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1px;
  background: #e5e7eb;
  position: relative;
}

.divider-text {
  position: absolute;
  background: #f5f7fa;
  padding: 8px 0;
  color: #9ca3af;
  font-size: 13px;
}

/* 上传区域 */
.upload-area {
  width: 100%;
  margin-bottom: 16px;
}

.upload-area :deep(.el-upload-dragger) {
  padding: 24px;
  border-radius: 8px;
  border-color: #d1d5db;
}

.upload-area :deep(.el-upload-dragger:hover) {
  border-color: #2563EB;
}

.upload-content {
  color: #9ca3af;
}

.format-badges {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.format-badge {
  padding: 3px 10px;
  background: #f3f4f6;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  color: #6b7280;
}

.format-hint {
  font-size: 12px;
  color: #9ca3af;
  margin: 0;
}

/* 底部亮点 */
.highlights-divider {
  width: 100%;
  padding: 0 40px;
  box-sizing: border-box;
  margin-bottom: 40px;
}

.highlights-divider::before {
  content: '';
  display: block;
  height: 1px;
  background: #e5e7eb;
}

.highlights {
  display: flex;
  gap: 32px;
  width: 100%;
  padding: 0 40px;
  box-sizing: border-box;
}

.highlight-item {
  flex: 1;
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.highlight-icon {
  flex-shrink: 0;
  font-size: 20px;
  color: #2563EB;
  margin-top: 2px;
}

.highlight-item h4 {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 4px 0;
}

.highlight-item p {
  font-size: 12px;
  color: #9ca3af;
  margin: 0;
  line-height: 1.4;
}

/* 预览区域 */
.preview-section {
  margin-top: 12px;
}

.preview-card {
  border-radius: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.preview-content {
  display: flex;
  gap: 20px;
}

.thumbnail-wrapper {
  position: relative;
  flex-shrink: 0;
  width: 240px;
  height: 135px;
  border-radius: 6px;
  overflow: hidden;
  background-color: #f5f5f5;
}

.thumbnail {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.duration-badge {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.video-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.video-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
  line-height: 1.3;
}

.video-meta {
  display: flex;
  gap: 16px;
  color: #606266;
  font-size: 14px;
}

.video-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 结果区域 */
.result-section {
  margin-top: 12px;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.result-card {
  border-radius: 8px;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.result-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.result-content {
  max-height: 400px;
  overflow-y: auto;
}

.result-text {
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 14px;
  line-height: 1.6;
  color: #303133;
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0;
  padding: 16px;
  background-color: #f5f7fa;
  border-radius: 8px;
}

.error-alert {
  margin-top: 12px;
}

/* 侧边栏动画 */
.sidebar-enter-active,
.sidebar-leave-active {
  transition: width 0.3s ease;
}

.sidebar-enter-from,
.sidebar-leave-to {
  width: 0 !important;
}

.sidebar-enter-from *,
.sidebar-leave-to * {
  visibility: hidden;
}

@media (max-width: 768px) {
  .input-workspace {
    flex-direction: column;
  }
  
  .divider-vertical {
    width: 100%;
    height: 1px;
  }
  
  .divider-text {
    padding: 0 8px;
  }
  
  .highlights {
    flex-direction: column;
    gap: 16px;
  }
  
  .preview-content {
    flex-direction: column;
  }
  
  .thumbnail-wrapper {
    width: 100%;
    height: auto;
    aspect-ratio: 16 / 9;
  }
}
</style>
