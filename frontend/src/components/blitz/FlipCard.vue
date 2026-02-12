<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { type BlitzCard, updateCardStatus } from '@/api/blitzApi'
import { useAudio } from '@/composables/useAudio'
import { useRecording } from '@/composables/useRecording'
import IonColorFillSharp from '~icons/ion/color-fill-sharp'

import { getSpeakerAttributes } from '@/utils/speakerAssets'

const props = defineProps<{
  card: BlitzCard
}>()

const isFlipped = ref(false)
const audioEl = ref<HTMLAudioElement | null>(null)
const isMounted = ref(false)

// --- Audio Playback ---
// Adapt BlitzCard to AudioSlice interface expected by useAudio
// Delayed computation ensures useAudio receives data only AFTER mount,
// guaranteeing audioEl ref is populated when the watch triggers.
const audioSliceData = computed(() => {
  if (!isMounted.value) return null
  return {
    audio_url: props.card.content.audio_url || '',
    start_time: props.card.content.start_time || 0,
    end_time: props.card.content.end_time || 0
  }
})

const { isPlaying: isPlayingOriginal, toggle: toggleOriginal } = useAudio(audioEl, audioSliceData)

onMounted(() => {
  isMounted.value = true
})

// --- Recording ---
const { 
  isRecording, 
  toggleRecording, 
  recordedAudioUrl, 
  isPlayingRecordedAudio, 
  playRecording 
} = useRecording()

// --- Status Toggle ---
const isUpdatingStatus = ref(false)
const localHighlight = ref(props.card.highlight)

const toggleStatus = async (e: Event) => {
  e.stopPropagation() // Prevent card flip just in case
  if (isUpdatingStatus.value) return

  // Cycle: none -> red (hard) -> yellow (review) -> none
  const cycle: Record<string, 'red' | 'yellow' | 'none'> = {
    'none': 'red',
    'red': 'yellow',
    'yellow': 'none'
  }
  const nextStatus = cycle[localHighlight.value] || 'red'
  
  isUpdatingStatus.value = true
  try {
    await updateCardStatus(props.card.id, nextStatus)
    localHighlight.value = nextStatus
    props.card.highlight = nextStatus 
  } catch (err) {
    console.error('Failed to update status', err)
  } finally {
    isUpdatingStatus.value = false
  }
}

// --- Flip Logic ---
// Only flip when clicking the top part
const toggleFlip = () => {
  isFlipped.value = !isFlipped.value
  // Ensure audio doesn't auto-play on flip (default behavior is correct)
}

// --- Visual & Data Logic ---
// const bgColorClass = computed(() => {
//   // Using theme_color from backend now
//   // But we need to use inline style for hex code if backend returns hex
//   return '' 
// })

// Episode Source Display
const sourceDisplay = computed(() => {
  const { episode, order } = props.card
  // e.g. Friends S10E12 #10
  // Backend now returns standardized episode string like "S10E12"
  return `${episode} #${order} #${props.card.id}`
})

const speakerAttrs = computed(() => getSpeakerAttributes(props.card.speaker))

</script>

<template>
  <!-- Card Container -->
  <div class="flip-card-container w-full h-[360px] perspective-1000">
    <!-- Hidden Audio Element -->
    <audio ref="audioEl" class="hidden" preload="auto"></audio>

    <div 
      class="flip-card-inner relative w-full h-full transition-transform duration-500 transform-style-3d"
      :class="{ 'rotate-y-180': isFlipped }"
    >
      
      <!-- FRONT SIDE -->
      <div class="flip-card-front absolute w-full h-full backface-hidden flex flex-col rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden bg-white dark:bg-gray-800">
        
        <!-- Top Half: Avatar + Colored BG -->
        <!-- Click here to flip -->
        <div 
          class="h-1/2 w-full flex items-center justify-center cursor-pointer relative"
          :style="{ backgroundColor: speakerAttrs.themeColor }"
          @click="toggleFlip"
        >
          <!-- Text Hint if avatar missing? (Should allow default) -->
          <div class="w-28 h-28 rounded-full border-4 border-white/50 overflow-hidden shadow-sm bg-white">
             <!-- Use API_BASE relative path or absolute URL from backend -->
             <img :src="speakerAttrs.avatarUrl" :alt="card.speaker" class="w-full h-full object-cover" />
          </div>
        </div>

        <!-- Bottom Half: Source + Chinese -->
        <div class="h-1/2 w-full bg-white flex flex-col p-6 items-start justify-center gap-2">
           <div class="text-xs font-bold text-gray-500 uppercase tracking-wide">
             {{ sourceDisplay }}
           </div>
           <p class="text-lg text-gray-800 font-medium leading-relaxed line-clamp-4">
             {{ card.content.text_zh || 'No translation available' }}
           </p>
        </div>

      </div>

      <!-- BACK SIDE -->
      <div 
        class="flip-card-back absolute w-full h-full backface-hidden rotate-y-180 flex flex-col rounded-2xl shadow-xl overflow-hidden bg-gray-800 border border-gray-700"
      >
        <!-- Top Half: Avatar + Colored BG (Same) -->
        <!-- Click here to flip back -->
        <div 
          class="h-1/2 w-full flex items-center justify-center cursor-pointer relative"
          :style="{ backgroundColor: speakerAttrs.themeColor }"
          @click="toggleFlip"
        >
          <div class="w-28 h-28 rounded-full border-4 border-white/50 overflow-hidden shadow-sm bg-white">
             <img :src="speakerAttrs.avatarUrl" :alt="card.speaker" class="w-full h-full object-cover" />
          </div>
        </div>

        <!-- Bottom Half: English + Controls -->
        <div class="h-1/2 w-full bg-gray-800 flex flex-col p-5 justify-between">
           <!-- English Text -->
           <p class="text-white text-base font-medium leading-relaxed line-clamp-4 select-text">
             {{ card.content.text }}
           </p>

           <!-- Controls Row -->
           <div class="flex items-center justify-between mt-2 pt-3 border-t border-gray-700">
             
             <!-- Status (Paint Bucket) -->
             <button 
               class="text-gray-400 hover:text-white transition-colors p-1"
               :class="{
                   'text-red-500 hover:text-red-400': localHighlight === 'red',
                   'text-yellow-500 hover:text-yellow-400': localHighlight === 'yellow'
               }"
               @click.stop="toggleStatus"
               title="Mark Difficulty"
             >
                <IonColorFillSharp class="text-xl" />
             </button>

             <!-- Rec/Play Rec -->
             <div class="flex gap-3">
               <button 
                 class="w-10 h-10 rounded-full flex items-center justify-center transition-all"
                 :class="isRecording ? 'bg-red-500 text-white animate-pulse' : 'bg-gray-700 text-blue-400 hover:bg-gray-600'"
                 @click.stop="toggleRecording"
               >
                  <i-tabler-microphone v-if="!isRecording" class="text-lg" />
                  <i-tabler-player-stop-filled v-else class="text-lg" />
               </button>

               <button 
                 v-if="recordedAudioUrl"
                 class="w-8 h-8 rounded-full flex items-center justify-center bg-green-900/50 text-green-400 hover:bg-green-900 transition-colors"
                 @click.stop="playRecording"
               >
                 <i-tabler-ear class="text-sm" />
               </button>
             </div>

             <!-- Play Original -->
             <button 
               class="w-8 h-8 rounded-full flex items-center justify-center bg-green-500 text-gray-900 hover:bg-green-400 transition-colors shadow-lg shadow-green-500/20"
               @click.stop="toggleOriginal"
             >
                <i-tabler-player-pause-filled v-if="isPlayingOriginal" class="text-sm" />
                <i-tabler-player-play-filled v-else class="text-sm" />
             </button>

           </div>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
.perspective-1000 {
  perspective: 1000px;
}
.transform-style-3d {
  transform-style: preserve-3d;
}
.backface-hidden {
  backface-visibility: hidden;
}
.rotate-y-180 {
  transform: rotateY(180deg);
}
</style>
