<template>
  <!-- Main Container -->
  <div class="h-full w-full flex flex-col p-4 bg-slate-50">

    <!-- Empty State -->
    <div v-if="!loading && dueCards.length === 0" class="flex-1 flex flex-col items-center justify-center text-center bg-white rounded-3xl shadow-lg p-8">
      <div class="text-5xl mb-6">🎉</div>
      <h2 class="text-xl font-bold text-zinc-800 mb-2">All caught up!</h2>
      <p class="text-zinc-500 mb-8 max-w-xs text-sm">Great job keeping up with your daily reviews.</p>
      <!-- @pending 这里跳转的链接需要确认 -->
      <button 
        @click="$router.push('/phrase-seeker')"
        class="px-6 py-2.5 bg-blue-500 text-white font-semibold rounded-full hover:bg-blue-600 transition-colors shadow-lg"
      >
        Go to Library
      </button>
    </div>

    <!-- Carousel Container -->
    <div v-else-if="currentCard" class="flex-1 flex items-center justify-center gap-6 min-h-0 px-4">
      
      <!-- Left Arrow + Preview Card -->
      <div class="hidden lg:flex items-center gap-3 flex-1 max-w-[200px]">
        <!-- Previous Card Preview (3D Skew) -->
        <div 
          v-if="prevCard"
          class="flex-1 h-[60vh] max-h-[500px] min-h-[350px] bg-white/60 rounded-2xl shadow-md flex items-center justify-center p-4 cursor-pointer hover:bg-white/80 transition-all"
          style="transform: perspective(800px) rotateY(-15deg);"
          @click="goToPrev"
        >
          <p class="text-zinc-400 text-sm text-center line-clamp-3">{{ prevCard.slice_translation || '...' }}</p>
        </div>
        
        <!-- Left Arrow -->
        <button 
          v-if="currentIndex > 0"
          @click="goToPrev"
          class="arrow-btn w-12 h-12 rounded-full bg-white shadow-md flex items-center justify-center text-blue-500 hover:scale-125 hover:shadow-lg transition-all shrink-0 cursor-pointer"
        >
          <i-tabler-chevron-left class="text-2xl" />
        </button>
      </div>

      <!-- Current Card (Main) -->
      <div class="flex-[2] max-w-3xl h-[70vh] max-h-[500px] min-h-[350px] flex flex-col">
        <Transition :name="slideDirection" mode="out-in">
        <div :key="currentIndex" class="flex-1 bg-white rounded-3xl shadow-xl flex flex-col items-center p-6 gap-4 overflow-hidden">
          
          <!-- Tag -->
          <span class="px-3 py-1 rounded-full text-[10px] font-bold tracking-wider uppercase bg-blue-500 text-white shrink-0">
            LISTEN TO THE AUDIO
          </span>

          <!-- Audio Controls Row -->
          <div class="flex items-center gap-6">
            <!-- Recording Button (Left) -->
            <button 
              @click="toggleRecording"
              class="w-10 h-10 rounded-full flex items-center justify-center transition-all hover:scale-110 active:scale-95"
              :class="isRecording ? 'bg-red-500 text-white animate-pulse' : 'bg-transparent text-red-400 hover:text-red-500'"
              :title="isRecording ? 'Stop Recording' : 'Start Recording'"
            >
              <i-tabler-microphone v-if="!isRecording" class="text-xl" />
              <i-tabler-player-stop-filled v-else class="text-lg" />
            </button>

            <!-- Play Audio Button (Center) -->
            <button 
              @click="playAudio"
              :disabled="isAudioLoading"
              class="w-14 h-14 rounded-full bg-blue-500 hover:bg-blue-600 text-white flex items-center justify-center shadow-lg transition-all hover:scale-110 active:scale-95 shrink-0 disabled:opacity-50 disabled:cursor-wait"
            >
              <i-tabler-loader-2 v-if="isAudioLoading" class="text-xl animate-spin" />
              
              <i-tabler-player-pause-filled v-else-if="isPlaying" class="text-xl" />
              <i-tabler-player-play-filled v-else class="text-xl" />
            </button>

            <!-- Play Recording Button (Right) -->
            <button 
              @click="playRecording"
              :disabled="!recordedAudioUrl"
              class="w-10 h-10 rounded-full flex items-center justify-center transition-all hover:scale-110 active:scale-95"
              :class="recordedAudioUrl ? (isPlayingRecordedAudio ? 'text-green-600' : 'text-green-500 hover:text-green-600') : 'text-zinc-300 cursor-not-allowed'"
              title="Play Recording"
            >
              <!-- IconoirEmojiSingLeftNote i-tabler-headphones --> 
              <IconoirEmojiSingLeftNote v-if="!isPlayingRecordedAudio" class="text-xl" :class="recordedAudioUrl ? 'text-green-500' : 'text-zinc-300'" />
              <i-tabler-loader-2 v-else class="text-xl animate-spin" />
            </button>
          </div>

          <!-- Translation Text (Fixed Height, Editable) -->
          <div class="h-28 flex items-center justify-center w-full px-4 overflow-hidden">
            <EditableText
              :modelValue="currentCard.slice_translation"
              placeholder="点击添加翻译..."
              displayClass="text-xl md:text-2xl font-serif text-[#1F2937] text-center leading-relaxed line-clamp-3"
              @save="(text) => saveField('translation', text)"
            />
          </div>

          <!-- Divider -->
          <div class="w-full border-t border-zinc-200 shrink-0"></div>

          <!-- Reveal / Answer Section (Fixed Height) -->
          <div class="h-20 flex items-center justify-center w-full">
            <!-- Show Answer Button -->
            <button 
              v-if="!showResult"
              @click="revealAnswer"
              class="flex items-center gap-2 text-zinc-400 hover:text-zinc-600 transition-colors"
            >
              <i-tabler-eye-off class="text-lg" />
              <span class="text-sm">Show Answer</span>
            </button>

            <!-- Revealed Answer (Editable) -->
            <EditableText
              v-else
              :modelValue="currentCard.slice_text"
              placeholder="点击添加原文..."
              displayClass="text-lg font-serif text-zinc-500 text-center leading-relaxed line-clamp-2 px-4"
              @save="(text) => saveField('original_text', text)"
            />
          </div>

          <!-- Action Buttons (Fixed Height) -->
          <div class="h-12 flex items-center justify-center gap-6 shrink-0">
            <button 
              @click="submitResult(false)"
              class="flex items-center gap-1 px-4 py-2 rounded-full border border-red-200 text-red-400 hover:bg-red-50 hover:border-red-300 transition-all"
            >
              <i-tabler-x class="text-sm" />
              <span class="text-sm font-medium">Forgot</span>
            </button>
            <button 
              @click="submitResult(true)"
              class="flex items-center gap-1 px-4 py-2 rounded-full border border-green-200 text-green-500 hover:bg-green-50 hover:border-green-300 transition-all"
            >
              <i-tabler-thumb-up class="text-sm" />
              <span class="text-sm font-medium">Good</span>
            </button>
          </div>

          <div class="text-zinc-300 text-xs font-light mt-auto">{{ currentIndex + 1 }} / {{ totalCards }}</div>

        </div>
        </Transition>
      </div>

      <!-- Right Arrow + Preview Card -->
      <div class="hidden lg:flex items-center gap-3 flex-1 max-w-[200px]">
        <!-- Right Arrow -->
        <button 
          v-if="currentIndex < dueCards.length - 1"
          @click="goToNext"
          class="arrow-btn w-12 h-12 rounded-full bg-white shadow-md flex items-center justify-center text-blue-500 hover:scale-125 hover:shadow-lg transition-all shrink-0 cursor-pointer"
        >
          <i-tabler-chevron-right class="text-2xl" />
        </button>

        <!-- Next Card Preview (3D Skew) -->
        <div 
          v-if="nextCard"
          class="flex-1 h-[60vh] max-h-[500px] min-h-[350px] bg-white/60 rounded-2xl shadow-md flex items-center justify-center p-4 cursor-pointer hover:bg-white/80 transition-all"
          style="transform: perspective(800px) rotateY(15deg);"
          @click="goToNext"
        >
          <p class="text-zinc-400 text-sm text-center line-clamp-3">{{ nextCard.slice_translation || '...' }}</p>
        </div>
      </div>

    </div>
    
    <!-- Audio Element (Hidden) -->
    <audio ref="audioRef" class="hidden"></audio>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { reviewApi, type ReviewCard } from '@/api/reviewApi'
import { useAudio, type AudioSlice } from '@/composables/useAudio'
import { useRecording } from '@/composables/useRecording'
import EditableText from '@/components/EditableText.vue'

import IconoirEmojiSingLeftNote from '~icons/iconoir/emoji-sing-left-note';

// State
const loading = ref(true)
const dueCards = ref<ReviewCard[]>([])
const currentIndex = ref(0)
const showResult = ref(false)
const slideDirection = ref<'slide-left' | 'slide-right'>('slide-left')

// Refs
const audioRef = ref<HTMLAudioElement | null>(null)

// Computed
const currentCard = computed(() => dueCards.value[currentIndex.value])
const prevCard = computed(() => currentIndex.value > 0 ? dueCards.value[currentIndex.value - 1] : null)
const nextCard = computed(() => currentIndex.value < dueCards.value.length - 1 ? dueCards.value[currentIndex.value + 1] : null)
const totalCards = computed(() => dueCards.value.length)

// Audio slice for useAudio composable
const currentAudioSlice = computed<AudioSlice | null>(() => {
    const card = currentCard.value
    if (!card) return null
    return {
        audio_url: card.audio_url,
        start_time: card.start_time,
        end_time: card.end_time
    }
})

// Use audio composable
const { isPlaying, isLoading: isAudioLoading, toggle: playAudio } = useAudio(audioRef, currentAudioSlice)

// Use recording composable
const { isRecording, recordedAudioUrl, isPlayingRecordedAudio, toggleRecording, playRecording, clearRecording } = useRecording()

// Clear recording when switching cards
watch(currentIndex, () => {
    clearRecording()
})

// Lifecycle
onMounted(async () => {
  try {
    const response = await reviewApi.getDueReviews()
    dueCards.value = response.data
    window.addEventListener('keydown', handleKeydown)
  } catch (e) {
    console.error('Failed to fetch reviews', e)
  } finally {
    loading.value = false
  }
})

onUnmounted(() => {
    window.removeEventListener('keydown', handleKeydown)
})

// Methods
const handleKeydown = (e: KeyboardEvent) => {
    if (loading.value || !currentCard.value) return 
    
    // Space to Play Audio
    if (e.code === 'Space') {
        e.preventDefault()
        playAudio()
        return
    }

    if (!showResult.value) {
        // Enter to Reveal
        if (e.code === 'Enter') {
            e.preventDefault()
            revealAnswer()
        }
    } else {
        // 1 or ArrowLeft for Forgot
        if (e.key === '1' || e.code === 'ArrowLeft') {
            submitResult(false)
        }
        // 2 or ArrowRight or Enter for Good
        if (e.key === '2' || e.code === 'ArrowRight' || e.code === 'Enter') {
            submitResult(true)
        }
    }
}


// Navigation Methods
const goToPrev = () => {
  if (currentIndex.value > 0) {
    slideDirection.value = 'slide-right'
    showResult.value = false
    currentIndex.value--
  }
}

const goToNext = () => {
  if (currentIndex.value < dueCards.value.length - 1) {
    slideDirection.value = 'slide-left'
    showResult.value = false
    currentIndex.value++
  }
}

// Save field (unified handler for EditableText)
const saveField = async (field: 'translation' | 'original_text', value: string) => {
    if (!currentCard.value) return
    
    try {
        await reviewApi.updateSlice(currentCard.value.audio_slice, { [field]: value })
        
        // Update local state
        const card = dueCards.value[currentIndex.value]
        if (card) {
            if (field === 'translation') {
                card.slice_translation = value
            } else {
                card.slice_text = value
            }
        }
    } catch (e) {
        console.error(`Failed to update ${field}`, e)
        alert(`Failed to save ${field}`)
    }
}

const revealAnswer = () => {
    showResult.value = true
}

const submitResult = async (success: boolean) => {
    if (!currentCard.value) return

    // Optimistic UI update: Move to next card immediately
    const cardId = currentCard.value.id
    advanceToNextCard()

    // Background submission
    try {
        await reviewApi.submitReview(cardId, success)
    } catch (e) {
        console.error('Failed to submit review', e)
    }
}

const advanceToNextCard = () => {
  showResult.value = false
  
  if (currentIndex.value < dueCards.value.length - 1) {
    currentIndex.value++
  } else {
    // Finished
    dueCards.value = [] 
  }
}

</script>

<style>
/* Slide Left (Next) */
.slide-left-enter-active,
.slide-left-leave-active {
  transition: all 0.3s ease-out;
}

.slide-left-enter-from {
  opacity: 0;
  transform: translateX(50px);
}

.slide-left-leave-to {
  opacity: 0;
  transform: translateX(-50px);
}

/* Slide Right (Prev) */
.slide-right-enter-active,
.slide-right-leave-active {
  transition: all 0.3s ease-out;
}

.slide-right-enter-from {
  opacity: 0;
  transform: translateX(-50px);
}

.slide-right-leave-to {
  opacity: 0;
  transform: translateX(50px);
}

/* Arrow button animations */
.arrow-btn {
  animation: arrow-pulse 2s ease-in-out infinite;
}

.arrow-btn:hover {
  animation: none;
}

@keyframes arrow-pulse {
  0%, 100% { 
    opacity: 0.6;
    transform: scale(1);
  }
  50% { 
    opacity: 1;
    transform: scale(1.05);
  }
}
</style>
