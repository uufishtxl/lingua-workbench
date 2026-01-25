<template>
  <!-- Main Container: Fill available space, no scroll. -->
  <div class="h-full w-full flex flex-col justify-center items-center p-4">
    
    <!-- Wrapper to constrain width and height visually -->
    <div class="w-full max-w-2xl flex flex-col h-full max-h-[800px]">
        
        <!-- Header -->
        <header class="flex justify-between items-center mb-6 shrink-0">
        <div>
            <h1 class="text-xl font-bold text-white tracking-tight flex items-center gap-2">
                <i class="i-mdi-cards-playing-outline text-blue-400"></i> Daily Review
            </h1>
            <p class="text-zinc-500 text-xs mt-1 font-medium">
            <span v-if="loading">Loading...</span>
            <span v-else>{{ currentIndex + 1 }} / {{ dueCards.length }} Due</span>
            </p>
        </div>
        <button @click="$router.push('/')" class="text-zinc-500 hover:text-white transition-colors p-2 rounded-full hover:bg-zinc-800">
            <i class="i-mdi-close text-xl"></i>
        </button>
        </header>

        <!-- Empty State -->
        <div v-if="!loading && dueCards.length === 0" class="flex-1 flex flex-col items-center justify-center text-center bg-zinc-900/30 rounded-3xl border border-zinc-800/50 backdrop-blur-sm p-8">
            <div class="text-5xl mb-6 filter drop-shadow-lg">🎉</div>
            <h2 class="text-xl font-bold text-white mb-2">All caught up!</h2>
            <p class="text-zinc-400 mb-8 max-w-xs text-sm">Great job keeping up with your daily reviews.</p>
            <button 
                @click="$router.push('/')"
                class="px-6 py-2.5 bg-white text-zinc-900 font-semibold rounded-full hover:bg-zinc-200 transition-colors shadow-lg active:scale-95 text-sm"
            >
                Back to Dashboard
            </button>
        </div>

        <!-- Active Card -->
        <div v-else-if="currentCard" class="flex-1 flex flex-col min-h-0 relative group">
            
            <!-- Card Surface -->
            <div 
                class="flex-1 flex flex-col bg-gradient-to-br from-zinc-800 to-zinc-900 rounded-3xl border border-zinc-700/50 shadow-2xl relative overflow-hidden transition-all duration-500"
                :class="{'ring-1 ring-blue-500/20 shadow-blue-500/5': !showResult, 'ring-1 ring-zinc-600/50': showResult}"
            >
                <!-- Background decoration -->
                <div class="absolute top-0 right-0 w-64 h-64 bg-blue-500/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 pointer-events-none"></div>

                <!-- Tag -->
                <div class="absolute top-6 left-6 z-10">
                    <span 
                        class="px-3 py-1 rounded-full text-[10px] font-bold tracking-wider uppercase border shadow-sm"
                        :class="currentCard.review_type === 'translation' 
                            ? 'bg-blue-500/10 text-blue-300 border-blue-500/20' 
                            : 'bg-purple-500/10 text-purple-300 border-purple-500/20'"
                    >
                        {{ currentCard.review_type }}
                    </span>
                </div>

                <!-- Main Content (Middle Aligned) -->
                <div class="flex-1 flex flex-col justify-center items-center px-8 relative z-0">
                    
                    <!-- Question (Always Visible) -->
                    <div class="flex-shrink-0 mb-6 w-full px-4">
                        <!-- Translation Section -->
                        <div class="min-h-[60px] relative group/edit flex flex-col justify-center items-center">
                            
                            <!-- Display Mode -->
                            <div v-if="!isEditing" class="relative">
                                <h3 class="text-2xl md:text-3xl font-serif text-zinc-200 leading-relaxed tracking-wide text-center cursor-pointer hover:text-white transition-colors" @click="startEdit">
                                    {{ currentCard.slice_translation || "..." }}
                                </h3>
                                <!-- Edit Button (Visible on hover) -->
                                <button 
                                    @click.stop="startEdit"
                                    class="absolute -right-10 top-1/2 -translate-y-1/2 text-zinc-600 hover:text-blue-400 opacity-0 group-hover/edit:opacity-100 transition-all p-2"
                                    title="Edit Translation"
                                >
                                    <i class="i-mdi-pencil text-lg"></i>
                                </button>
                            </div>

                            <!-- Edit Mode -->
                            <div v-else class="w-full max-w-lg flex flex-col gap-3 animate-fade-in">
                                <textarea
                                    v-model="editingText"
                                    ref="editInputRef"
                                    rows="3"
                                    class="w-full bg-zinc-800 border-2 border-zinc-700 rounded-xl p-4 text-white text-xl text-center focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 outline-none resize-none font-serif shadow-xl"
                                    @keydown.ctrl.enter="saveEdit"
                                    @keydown.esc="cancelEdit"
                                    placeholder="Enter translation..."
                                ></textarea>
                                <div class="flex justify-center gap-3">
                                    <button 
                                        @click="cancelEdit"
                                        class="px-4 py-1.5 text-xs font-bold rounded-lg bg-zinc-700 hover:bg-zinc-600 text-zinc-300 transition-colors uppercase tracking-wider"
                                    >
                                        Cancel
                                    </button>
                                    <button 
                                        @click="saveEdit"
                                        class="px-4 py-1.5 text-xs font-bold rounded-lg bg-blue-600 hover:bg-blue-500 text-white transition-colors shadow-lg uppercase tracking-wider"
                                    >
                                        Save
                                    </button>
                                </div>
                            </div>
                        </div>

                        <!-- Audio Player -->
                        <div 
                             v-if="!isEditing && (currentCard.review_type === 'listening' || showResult)"
                             class="flex justify-center h-16 transition-opacity duration-300 animate-fade-in mt-8"
                        >
                            <button 
                                @click.stop="playAudio"
                                class="w-16 h-16 rounded-full bg-zinc-700 hover:bg-zinc-600 text-white flex items-center justify-center transition-all hover:scale-110 active:scale-95 shadow-xl shadow-black/20 group border border-white/5"
                                title="Play Audio (Space)"
                            >
                                <i class="i-mdi-volume-high text-2xl group-hover:text-white transition-colors"></i>
                            </button>
                        </div>
                    </div>

                    <!-- Revealed Answer (Absolute positioned or Flow?) Flow is safer for varying text length -->
                    <transition name="slide-fade">
                        <div v-if="showResult" class="w-full mt-8 pt-8 border-t border-white/5 text-center bg-black/5 -mx-8 px-8 pb-4 rounded-b-lg">
                            <p class="text-xl md:text-2xl font-serif text-blue-200 leading-relaxed mb-1 selection:bg-blue-500/30">
                                {{ currentCard.slice_text }}
                            </p>
                        </div>
                    </transition>
                </div>
            </div>

            <!-- Action Bar (Fixed Height) -->
            <div class="h-24 shrink-0 flex items-center justify-center pt-6">
                
                <!-- Reveal Action -->
                <button 
                    v-if="!showResult"
                    @click="revealAnswer"
                    class="w-full max-w-sm py-3.5 bg-white text-zinc-900 font-bold text-base rounded-2xl shadow-xl shadow-white/5 hover:bg-zinc-50 hover:shadow-white/10 hover:-translate-y-0.5 active:translate-y-0 active:scale-95 transition-all flex items-center justify-center gap-2"
                >
                    <i class="i-mdi-eye-outline text-lg"></i>
                    Show Answer
                </button>

                <!-- Grading Actions -->
                <div v-else class="flex gap-4 w-full max-w-sm">
                    <button 
                        @click="submitResult(false)"
                        class="flex-1 py-3.5 rounded-2xl bg-[#2a2a2e] border border-zinc-700 hover:bg-red-500/10 hover:border-red-500/50 hover:text-red-400 text-zinc-400 font-medium transition-all active:scale-95 flex items-center justify-center gap-2 group shadow-lg"
                    >
                        <i class="i-mdi-close text-lg group-hover:scale-110 transition-transform"></i>
                        Forgot
                    </button>

                    <button 
                        @click="submitResult(true)"
                        class="flex-1 py-3.5 rounded-2xl bg-[#2a2a2e] border border-zinc-700 hover:bg-green-500/10 hover:border-green-500/50 hover:text-green-400 text-zinc-400 font-medium transition-all active:scale-95 flex items-center justify-center gap-2 group shadow-lg"
                    >
                        <i class="i-mdi-check text-lg group-hover:scale-110 transition-transform"></i>
                        Good
                    </button>
                </div>

            </div>

        </div>

    </div>
    
    <!-- Audio Element (Hidden) -->
    <audio ref="audioRef" class="hidden"></audio>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { reviewApi, type ReviewCard } from '@/api/reviewApi'

// State
const loading = ref(true)
const dueCards = ref<ReviewCard[]>([])
const currentIndex = ref(0)
const showResult = ref(false)

// Edit State
const isEditing = ref(false)
const editingText = ref('')
const editInputRef = ref<HTMLTextAreaElement | null>(null)

// Refs
const audioRef = ref<HTMLAudioElement | null>(null)

// Computed
const currentCard = computed(() => dueCards.value[currentIndex.value])

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

const playAudio = () => {
  if (currentCard.value && audioRef.value) {
    audioRef.value.src = currentCard.value.audio_url 
    audioRef.value.currentTime = currentCard.value.start_time
    audioRef.value.play().catch(e => console.warn("Audio play blocked", e))
    
    const stopTime = currentCard.value.end_time
    const handleTimeUpdate = () => {
      if (audioRef.value && audioRef.value.currentTime >= stopTime) {
        audioRef.value.pause()
        audioRef.value.removeEventListener('timeupdate', handleTimeUpdate)
      }
    }
    audioRef.value.addEventListener('timeupdate', handleTimeUpdate)
  }
}

// Edit Methods
const startEdit = () => {
    if (!currentCard.value) return
    editingText.value = currentCard.value.slice_translation || ''
    isEditing.value = true
    // Auto focus
    setTimeout(() => editInputRef.value?.focus(), 100)
}

const cancelEdit = () => {
    isEditing.value = false
    editingText.value = ''
}

const saveEdit = async () => {
    if (!currentCard.value) return
    const newText = editingText.value.trim()
    if (!newText || newText === currentCard.value.slice_translation) {
        cancelEdit()
        return
    }

    try {
        await reviewApi.updateTranslation(currentCard.value.audio_slice, newText)
        
        // Update local state
        // We need to verify if `currentCard.value` is reactive in a way that allows direct mutation 
        // since it is a computed property from `dueCards`. Mutating the source array item works.
        const card = dueCards.value[currentIndex.value]
        if (card) {
            card.slice_translation = newText
        }
        
        isEditing.value = false
    } catch (e) {
        console.error('Failed to update translation', e)
        alert('Failed to save translation')
    }
}

const revealAnswer = () => {
    showResult.value = true
}

const submitResult = async (success: boolean) => {
    if (!currentCard.value) return

    // Optimistic UI update: Move to next card immediately
    const cardId = currentCard.value.id
    nextCard()

    // Background submission
    try {
        await reviewApi.submitReview(cardId, success)
    } catch (e) {
        console.error('Failed to submit review', e)
    }
}

const nextCard = () => {
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
.slide-fade-enter-active {
  transition: all 0.3s ease-out;
}

.slide-fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}
</style>
