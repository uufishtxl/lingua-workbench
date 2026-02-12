<template>
  <div class="chunk-complete-bar">
    <!-- Normal State: Show button or completion message -->
    <div v-if="!showSuccessAnimation" class="bar-content">
      <template v-if="isLastChunk">
        <!-- Last chunk: show completion message -->
        <div class="completion-message">
          <i-tabler-trophy class="text-2xl text-yellow-500" />
          <span class="text-gray-600 font-medium">🎉 恭喜！您已完成本集的学习旅程</span>
        </div>
      </template>
      <template v-else>
        <!-- Normal: show complete button -->
        <button 
          class="complete-btn"
          :disabled="isLoading"
          @click="handleComplete"
        >
          <i-tabler-circle-check class="text-xl" />
          <span>Mark Complete & Continue</span>
          <i-tabler-chevron-right class="text-lg" />
        </button>
      </template>
    </div>

    <!-- Success Animation Overlay -->
    <Transition name="slide-up">
      <div v-if="showSuccessAnimation" class="success-overlay">
        <div class="success-content">
          <div class="success-icon">
            <i-tabler-check class="text-3xl text-green-600" />
          </div>
          <div class="success-text">
            <span class="success-title">Amazing!</span>
            <span class="success-subtitle">Chunk {{ (currentIndex ?? 0) + 1 }} / {{ totalChunks ?? '?' }} completed</span>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { completeChunk } from '@/api/slicerApi'

const props = defineProps<{
  chunkId: number
  nextChunkId?: number | null
  isLastChunk?: boolean
  currentIndex?: number
  totalChunks?: number
}>()

const emit = defineEmits<{
  completed: [nextChunkId: number | null]
}>()

const router = useRouter()
const isLoading = ref(false)
const showSuccessAnimation = ref(false)

// Success sound (optional - you can add a sound file later)
const playSuccessSound = () => {
  try {
    // Create a simple beep using Web Audio API
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
    const oscillator = audioContext.createOscillator()
    const gainNode = audioContext.createGain()
    
    oscillator.connect(gainNode)
    gainNode.connect(audioContext.destination)
    
    oscillator.frequency.value = 800
    oscillator.type = 'sine'
    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime)
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3)
    
    oscillator.start(audioContext.currentTime)
    oscillator.stop(audioContext.currentTime + 0.3)
  } catch (e) {
    console.log('Audio not supported')
  }
}

const handleComplete = async () => {
  if (isLoading.value) return
  
  isLoading.value = true
  
  try {
    const result = await completeChunk(props.chunkId)
    
    // Show success animation
    showSuccessAnimation.value = true
    playSuccessSound()
    
    // Wait 1.5 seconds then navigate
    setTimeout(() => {
      emit('completed', result.next_chunk_id)
      
      if (result.next_chunk_id) {
        // Navigate to next chunk
        router.push({
          name: 'audio-workbench',
          params: { id: result.next_chunk_id },
          query: { mode: 'review' }
        })
      }
    }, 1500)
    
  } catch (error) {
    console.error('Failed to complete chunk:', error)
    isLoading.value = false
  }
}
</script>

<style scoped>
.chunk-complete-bar {
  position: sticky;
  bottom: 0;
  left: 0;
  right: 0;
  background: white;
  border-top: 1px solid #e5e7eb;
  padding: 1rem 1.5rem;
  z-index: 50;
}

.bar-content {
  display: flex;
  justify-content: center;
  align-items: center;
}

.complete-btn {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.875rem 2rem;
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  color: white;
  font-weight: 600;
  font-size: 1rem;
  border-radius: 9999px;
  border: none;
  cursor: pointer;
  box-sizing: border-box;
  box-shadow: 0 4px 14px rgba(34, 197, 94, 0.4);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.complete-btn:hover:not(:disabled) {
  box-shadow: 0 6px 20px rgba(34, 197, 94, 0.5);
}

.complete-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.completion-message {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border-radius: 0.75rem;
}

/* Success Animation Overlay */
.success-overlay {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
  padding: 1.5rem 2rem;
  z-index: 100;
}

.success-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  max-width: 600px;
  margin: 0 auto;
}

.success-icon {
  width: 3.5rem;
  height: 3.5rem;
  background: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.success-text {
  display: flex;
  flex-direction: column;
}

.success-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #15803d;
}

.success-subtitle {
  font-size: 0.875rem;
  color: #166534;
}

/* Slide Up Animation */
.slide-up-enter-active {
  transition: all 0.3s ease-out;
}

.slide-up-leave-active {
  transition: all 0.2s ease-in;
}

.slide-up-enter-from {
  transform: translateY(100%);
  opacity: 0;
}

.slide-up-leave-to {
  transform: translateY(100%);
  opacity: 0;
}
</style>
