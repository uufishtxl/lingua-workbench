<template>
  <div class="transcript-viewer">
    <!-- 视频播放器 -->
    <div class="video-section">
      <div class="video-wrapper">
        <!-- YouTube 嵌入 -->
        <iframe
          v-if="youtubeId"
          ref="iframeRef"
          :src="`https://www.youtube.com/embed/${youtubeId}?enablejsapi=1`"
          frameborder="0"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowfullscreen
        />
        <!-- 无视频时显示音频信息 -->
        <div v-else class="audio-placeholder">
          <el-icon :size="48"><Headset /></el-icon>
          <span>音频文件</span>
        </div>
      </div>
    </div>

    <!-- 转录文本 -->
    <div class="transcript-section">
      <div class="transcript-header">
        <h3><span class="segment-count">合计 {{ segments.length }} 条</span></h3>
        <div class="header-right">
          <ExportButton :segments="segments" :title="title" />
        </div>
      </div>
      <div class="transcript-content" ref="transcriptContentRef">
        <div
          v-for="(segment, index) in segments"
          :key="index"
          :class="['segment-item', { active: isActiveSegment(index) }]"
          @click="handleSegmentClick(index)"
        >
          <span class="segment-time">{{ formatTime(segment.start) }}</span>
          <span class="segment-text">{{ segment.text }}</span>
          <span v-if="isActiveSegment(index) && isPlaying" class="playing-dot"></span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { Headset } from '@element-plus/icons-vue'
import ExportButton from './ExportButton.vue'

interface Segment {
  text: string
  start: number
  end: number
}

const props = defineProps<{
  videoUrl: string
  segments: Segment[]
  title?: string
}>()

const iframeRef = ref<HTMLIFrameElement | null>(null)
const transcriptContentRef = ref<HTMLDivElement | null>(null)
const currentTime = ref(0)
const isPlaying = ref(false)
let player: any = null
let timeUpdateInterval: ReturnType<typeof setInterval> | null = null

// 提取 YouTube ID
const youtubeId = computed(() => {
  if (!props.videoUrl) return null
  const match = props.videoUrl.match(/(?:embed\/|v=|youtu\.be\/)([a-zA-Z0-9_-]{11})/)
  return match ? match[1] : null
})

// 计算当前活跃的 segment
const activeSegmentIndex = computed(() => {
  return props.segments.findIndex(
    (seg) => currentTime.value >= seg.start && currentTime.value <= seg.end
  )
})

const isActiveSegment = (index: number) => {
  return index === activeSegmentIndex.value
}

// 点击 segment 跳转
const handleSegmentClick = (index: number) => {
  const segment = props.segments[index]
  if (youtubeId.value && player) {
    player.seekTo(segment.start, true)
    player.playVideo()
  }
}

// 自动滚动到活跃 segment
watch(activeSegmentIndex, (newIndex) => {
  if (newIndex >= 0 && transcriptContentRef.value) {
    const activeElement = transcriptContentRef.value.children[newIndex] as HTMLElement
    if (activeElement) {
      activeElement.scrollIntoView({
        behavior: 'smooth',
        block: 'center'
      })
    }
  }
})

// 加载 YouTube IFrame API
onMounted(() => {
  if (youtubeId.value) {
    loadYouTubeAPI()
  }
})

onUnmounted(() => {
  if (timeUpdateInterval) {
    clearInterval(timeUpdateInterval)
  }
})

const loadYouTubeAPI = () => {
  // 如果已加载
  if ((window as any).YT && (window as any).YT.Player) {
    initPlayer()
    return
  }

  // 加载 API
  const tag = document.createElement('script')
  tag.src = 'https://www.youtube.com/iframe_api'
  const firstScriptTag = document.getElementsByTagName('script')[0]
  firstScriptTag.parentNode?.insertBefore(tag, firstScriptTag)

  // API 就绪回调
  ;(window as any).onYouTubeIframeAPIReady = () => {
    initPlayer()
  }
}

const initPlayer = () => {
  if (!iframeRef.value) return

  player = new (window as any).YT.Player(iframeRef.value, {
    events: {
      onReady: () => {
        // 定时获取当前时间
        timeUpdateInterval = setInterval(() => {
          if (player && player.getCurrentTime) {
            currentTime.value = player.getCurrentTime()
            // 检测播放状态
            const state = player.getPlayerState?.()
            isPlaying.value = state === 1 // 1 = playing
          }
        }, 200)
      }
    }
  })
}

const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}
</script>

<style scoped>
.transcript-viewer {
  display: flex;
  gap: 16px;
  min-height: 400px;
  flex: 1;
}

.video-section {
  flex: 2;
}

.video-wrapper {
  width: 100%;
  height: 100%;
  border-radius: 8px;
  overflow: hidden;
  background: #000;
}

.video-wrapper iframe {
  width: 100%;
  height: 100%;
}

.audio-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #909399;
}

.transcript-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  background: #fafafa;
}

.transcript-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: #f0f2f5;
  border-bottom: 1px solid #e4e7ed;
}

.transcript-header h3 {
  margin: 0;
  font-size: 14px;
  color: #303133;
}

.transcript-header .header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.segment-count {
  font-size: 12px;
  color: #909399;
}

.transcript-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.segment-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  transform-origin: center center;
}

.segment-item:hover {
  background: rgba(37, 99, 235, 0.05);
}

.segment-item.active {
  background: #2563EB;
  color: white;
  padding: 14px 16px;
  transform: scale(1.02);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}

.segment-time {
  flex-shrink: 0;
  font-size: 12px;
  color: #68788F;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  min-width: 45px;
}

.segment-text {
  font-size: 13px;
  color: #68788F;
  line-height: 1.4;
  transition: font-size 0.35s ease, line-height 0.35s ease, color 0.35s ease;
}

.segment-item.active .segment-time {
  color: rgba(255, 255, 255, 0.9);
  font-size: 14px;
  font-weight: 600;
}

.segment-item.active .segment-text {
  color: #fff;
  font-size: 16px;
  font-weight: 500;
  line-height: 1.5;
}

.playing-dot {
  width: 8px;
  height: 8px;
  background: #fff;
  border-radius: 50%;
  margin-left: auto;
  flex-shrink: 0;
  animation: breathe 1.5s ease-in-out infinite;
}

@keyframes breathe {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(0.8);
  }
}
</style>
