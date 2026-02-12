<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { getResumeData, uploadEpisodeCover, type ResumeData } from '@/api/dashboardApi'
import { ElMessage } from 'element-plus'
import { useDashboardStore } from '@/stores/dashboardStore'
import StatsDisplay from '@/components/dashboard/StatsDisplay.vue'

const router = useRouter()
const dashboardStore = useDashboardStore()
const { stats, isLoading: isStatsLoading } = storeToRefs(dashboardStore)
const isLoading = ref(true)
const resumeData = ref<ResumeData | null>(null)

// ... existing code ...

// Load data on mount
onMounted(async () => {
  try {
    const [resume] = await Promise.all([
      getResumeData(),
      dashboardStore.fetchStats()
    ])
    resumeData.value = resume
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
    ElMessage.error('Failed to load dashboard')
  } finally {
    isLoading.value = false
  }
})


// Cover upload state
const fileInputRef = ref<HTMLInputElement | null>(null)
const selectedCoverFile = ref<File | null>(null)
const coverPreviewUrl = ref<string | null>(null)
const isUploadingCover = ref(false)

// Format time ago
const timeAgo = computed(() => {
  if (!resumeData.value?.last_studied_at) return null
  const date = new Date(resumeData.value.last_studied_at)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)
  
  if (diffDays > 0) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`
  if (diffHours > 0) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
  if (diffMins > 0) return `${diffMins} min${diffMins > 1 ? 's' : ''} ago`
  return 'Just now'
})

// Episode display string
const episodeDisplay = computed(() => {
  if (!resumeData.value?.source_audio) return ''
  const { drama_name, season, episode } = resumeData.value.source_audio
  return `${drama_name} S${season.toString().padStart(2, '0')}E${episode.toString().padStart(2, '0')}`
})

// Current cover URL (preview or actual)
const currentCoverUrl = computed(() => {
  if (coverPreviewUrl.value) return coverPreviewUrl.value
  return resumeData.value?.source_audio?.cover_url
})

// Source Audio ID for cover upload
const sourceAudioId = computed(() => {
  return resumeData.value?.source_audio?.id
})

// Navigate to workbench in review mode
const handleResume = () => {
  if (!resumeData.value?.chunk_id) return
  router.push({
    name: 'audio-workbench',
    params: { id: resumeData.value.chunk_id },
    query: { mode: 'review' }
  })
}

// Trigger file input
const triggerFileInput = () => {
  fileInputRef.value?.click()
}

// Handle file selection
const handleFileSelect = (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  
  // Validate file type
  if (!file.type.startsWith('image/')) {
    ElMessage.error('Please select an image file')
    return
  }
  
  // Create preview URL
  selectedCoverFile.value = file
  coverPreviewUrl.value = URL.createObjectURL(file)
}

// Cancel cover selection
const cancelCoverSelection = () => {
  if (coverPreviewUrl.value) {
    URL.revokeObjectURL(coverPreviewUrl.value)
  }
  selectedCoverFile.value = null
  coverPreviewUrl.value = null
  // Reset file input
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

// Upload cover to server
const uploadCover = async () => {
  if (!selectedCoverFile.value || !sourceAudioId.value) return
  
  isUploadingCover.value = true
  try {
    const result = await uploadEpisodeCover(sourceAudioId.value, selectedCoverFile.value)
    
    // Update resumeData with new cover URL
    if (resumeData.value?.source_audio && result.cover_url) {
      resumeData.value.source_audio.cover_url = result.cover_url
    }
    
    // Clear preview state
    cancelCoverSelection()
    
    ElMessage.success('Cover image uploaded!')
  } catch (error) {
    console.error('Failed to upload cover:', error)
    ElMessage.error('Failed to upload cover image')
  } finally {
    isUploadingCover.value = false
  }
}

// Load data on mount
onMounted(async () => {
  try {
    const [resume] = await Promise.all([
      getResumeData(),
      dashboardStore.fetchStats()
    ])
    resumeData.value = resume
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
    ElMessage.error('Failed to load dashboard')
  } finally {
    isLoading.value = false
  }
})
</script>

<template>
  <div class="dashboard" v-loading="isLoading">
    <!-- Header -->
    <!-- <div class="dashboard-header">
      <h1 class="dashboard-title">
        <i-tabler-microphone class="text-2xl text-blue-500" />
        Audio Slicer
      </h1>
    </div> -->

    <!-- No Content State -->
    <div v-if="!isLoading && !resumeData?.has_content" class="empty-state">
      <i-tabler-file-music class="text-6xl text-gray-300 mb-4" />
      <h2 class="text-xl font-semibold text-gray-600 mb-2">No Learning Content Yet</h2>
      <p class="text-gray-500 mb-6">Upload some audio to get started with your learning journey!</p>
      <el-button type="primary" size="large" @click="router.push({ name: 'load-source' })">
        <i-tabler-upload class="mr-2" />
        Upload Audio
      </el-button>
    </div>

    <!-- Main Dashboard Content -->
    <div v-else-if="!isLoading && resumeData?.has_content" class="dashboard-content">
      
      <!-- Hero Card Container -->
      <div class="hero-container">
        <!-- Hero Card: Continue Learning -->
        <div 
          class="hero-card"
          :class="{ 'hero-blur': !!coverPreviewUrl }"
          :style="currentCoverUrl ? { backgroundImage: `url(${currentCoverUrl})` } : {}"
        >
          <div class="hero-overlay"></div>
          <div class="hero-content">
            <h2 class="hero-title">{{ episodeDisplay }}</h2>
            <p class="hero-subtitle">
              Last stop: Chunk #{{ (resumeData.chunk_index ?? 0) + 1 }} / {{ resumeData.total_chunks }}
              <span v-if="timeAgo"> • {{ timeAgo }}</span>
            </p>
            <button class="resume-btn" @click="handleResume">
              <i-tabler-player-play-filled class="text-lg" />
              <span>Resume Learning</span>
            </button>
          </div>

          <!-- Cover Image Upload Button (bottom-right) -->
          <button 
            v-if="!coverPreviewUrl"
            class="cover-upload-btn"
            @click="triggerFileInput"
            title="Upload cover image"
          >
            <i-tabler-photo-plus class="text-xl" />
          </button>

          <!-- Hidden file input -->
          <input
            ref="fileInputRef"
            type="file"
            accept="image/*"
            class="hidden"
            @change="handleFileSelect"
          />
        </div>

        <!-- Save Cover Overlay (outside hero-card to avoid blur) -->
        <Transition name="fade">
          <div v-if="coverPreviewUrl" class="cover-save-overlay">
            <div class="cover-save-content">
              <button 
                class="cover-save-btn"
                :disabled="isUploadingCover"
                @click="uploadCover"
              >
                <i-tabler-device-floppy v-if="!isUploadingCover" class="text-5xl" />
                <i-tabler-loader-2 v-else class="text-5xl animate-spin" />
              </button>
              <span class="cover-save-text">Save Cover</span>
              <button class="cover-cancel-btn" @click="cancelCoverSelection">
                <i-tabler-x class="text-lg" />
                Cancel
              </button>
            </div>
          </div>
        </Transition>
      </div>


      <!-- Stats Row -->
      <div class="stats-row">
        <!-- Weak Points Card -->
        <div class="stats-card weak-points-card">
          <div class="stats-header">
            <i-tabler-chart-bar class="text-xl" />
            <span>难点突击 (Weak Points)</span>
          </div>
          <div class="stats-body">
            <StatsDisplay 
              variant="dashboard"
              :hardCount="stats?.hard_sentences ?? 0"
              :reviewCount="stats?.review_sentences ?? 0"
            />
          </div>
          <button 
            class="stats-action-btn" 
            :disabled="(stats?.hard_sentences ?? 0) + (stats?.review_sentences ?? 0) === 0"
            @click="router.push({ name: 'blitz-camp' })"
          >
            <i-tabler-bolt class="text-lg" />
            <span>开始突击复习</span>
          </button>
        </div>

        <!-- Progress Card -->
        <div class="stats-card progress-card">
          <div class="stats-header">
            <i-tabler-trophy class="text-xl text-yellow-500" />
            <span>学习进度 (Progress)</span>
          </div>
          <div class="progress-body">
            <div class="progress-number">{{ stats?.total_chunks_studied ?? 0 }}</div>
            <div class="progress-label">Chunks Completed</div>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
.dashboard {
  min-height: 100%;
  padding: 2rem;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.dashboard-header {
  margin-bottom: 2rem;
}

.dashboard-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.75rem;
  font-weight: 700;
  color: #1e293b;
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  text-align: center;
}

/* Dashboard Content */
.dashboard-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  max-width: 900px;
  width: 100%;
  margin: 0 auto;
}

/* Hero Container */
.hero-container {
  position: relative;
  border-radius: 1rem;
  overflow: hidden;
}

/* Hero Card */
.hero-card {
  position: relative;
  border-radius: 1rem;
  overflow: hidden;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  background-size: cover;
  background-position: center;
  aspect-ratio: 16 / 9;
  box-shadow: 0 10px 40px rgba(99, 102, 241, 0.3);
  transition: filter 0.3s ease;
}

.hero-blur {
  filter: blur(4px);
}

.hero-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(0,0,0,0.6) 0%, rgba(0,0,0,0.4) 100%);
}

.hero-content {
  position: relative;
  z-index: 1;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  height: 100%;
}

.hero-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: white;
  margin-bottom: 0.5rem;
  text-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

.hero-subtitle {
  font-size: 1rem;
  color: rgba(255,255,255,0.85);
  margin-bottom: 1.5rem;
}

.resume-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 2rem;
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  color: white;
  font-weight: 600;
  font-size: 1.125rem;
  border-radius: 9999px;
  border: none;
  cursor: pointer;
  box-shadow: 0 4px 14px rgba(34, 197, 94, 0.4);
  transition: box-shadow 0.2s ease;
  width: fit-content;
}

.resume-btn:hover {
  box-shadow: 0 6px 20px rgba(34, 197, 94, 0.5);
}

/* Cover Upload Button */
.cover-upload-btn {
  position: absolute;
  bottom: 1rem;
  right: 1rem;
  z-index: 10;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(8px);
  border: 2px solid rgba(255, 255, 255, 0.4);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.cover-upload-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.1);
}

/* Cover Save Overlay */
.cover-save-overlay {
  position: absolute;
  inset: 0;
  z-index: 20;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
}

.cover-save-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}

.cover-save-btn {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  border: none;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 30px rgba(34, 197, 94, 0.5);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.cover-save-btn:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 12px 40px rgba(34, 197, 94, 0.6);
}

.cover-save-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.cover-save-text {
  color: white;
  font-weight: 600;
  font-size: 1.125rem;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.cover-cancel-btn {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 1rem;
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.4);
  border-radius: 0.5rem;
  color: white;
  font-size: 0.875rem;
  cursor: pointer;
  transition: background 0.2s ease;
}

.cover-cancel-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

/* Fade Transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Stats Row */
.stats-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

@media (max-width: 640px) {
  .stats-row {
    grid-template-columns: 1fr;
  }
}

.stats-card {
  background: white;
  border-radius: 1rem;
  padding: 1.5rem;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
}

.stats-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 1rem;
}

.stats-body {
  display: flex;
  gap: 2rem;
  margin-bottom: 1rem;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.stat-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.stat-dot-red {
  background: #ef4444;
}

.stat-dot-yellow {
  background: #eab308;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1e293b;
}

.stat-label {
  font-size: 0.875rem;
  color: #6b7280;
}

.stats-action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.75rem 1rem;
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  color: white;
  font-weight: 600;
  border-radius: 0.5rem;
  border: none;
  cursor: pointer;
  transition: opacity 0.2s ease;
}

.stats-action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.progress-card .progress-body {
  text-align: center;
  padding: 1rem 0;
}

.progress-number {
  font-size: 3rem;
  font-weight: 700;
  color: #6366f1;
}

.progress-label {
  font-size: 0.875rem;
  color: #6b7280;
}

/* Utilities */
.hidden {
  display: none;
}

.animate-spin {
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
</style>
