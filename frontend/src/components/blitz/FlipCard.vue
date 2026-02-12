<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { type BlitzCard, updateCardStatus } from '@/api/blitzApi'
import { useAudio } from '@/composables/useAudio'
import { useRecording } from '@/composables/useRecording'
import IonColorFillSharp from '~icons/ion/color-fill-sharp'

import { getSpeakerAttributes } from '@/utils/speakerAssets'
import CardAvatar from './CardAvatar.vue'

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
  const start_time = props.card.content.start_time || 0
  const end_time = props.card.content.end_time || 0
  return {
    audio_url: props.card.content.audio_url || '',
    start_time,
    end_time,
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
  const { episode, chunk_id } = props.card
  // e.g. Friends S10E12 #10
  // Backend now returns standardized episode string like "S10E12"
  return `${episode} #${chunk_id} #${props.card.id}`
})

function getTextSizePerLength(text: string) {
  const len = text.length
  if (len < 20) return 'text-[18px]';       // 短句：超大号字体
  if (len < 50) return 'text-lg';       // 中句：正常大号
  if (len < 80) return 'text-md';       // 长句：中号
  if (len < 200) return 'text-xs';       // 超长句：小号
  return 'text-base';                    // 作文级别：基础字体
}

const fontSizeEn = computed(() => {
  return getTextSizePerLength(props.card.content.text)
})

const fontSizeZh = computed(() => {
  return getTextSizePerLength(props.card.content.text_zh)
})

const speakerAttrs = computed(() => getSpeakerAttributes(props.card.speaker))

</script>

<template>
  <!-- Card Container -->
  <div class="flip-card-container w-full h-[300px] perspective-1000">
    <!-- Hidden Audio Element -->
    <audio ref="audioEl" class="hidden" preload="auto"></audio>

    <div 
      class="flip-card-inner relative w-full h-full transition-transform duration-500 transform-style-3d"
      :class="{ 'rotate-y-180': isFlipped }"
    >
      
      <!-- FRONT SIDE -->
      <div class="flip-card-front absolute w-full h-full backface-hidden flex flex-col rounded-2xl shadow-lg overflow-hidden bg-white dark:bg-gray-800">
        
        <!-- Top Half: Avatar + Colored BG -->
        <!-- Click here to flip -->
        <div 
          class="h-1/4 w-full flex items-center justify-center cursor-pointer relative"
          :style="{ backgroundColor: speakerAttrs.themeColor }"
          @click="toggleFlip"
        >
          <CardAvatar 
            :avatarUrl="speakerAttrs.avatarUrl" 
            :speaker="card.speaker"
          />
        </div>

        <!-- Bottom Half: Source + Chinese -->
        <div class="h-3/4 w-full bg-white flex flex-col p-6 items-start justify-center gap-2">
           <div class="text-xs font-bold text-gray-500 uppercase tracking-wide pt-4">
             {{ sourceDisplay }}
           </div>
           <p :class="fontSizeZh" class="flex-1 text-gray-800 font-medium leading-relaxed line-clamp-4">
             {{ card.content.text_zh || 'No translation available' }}
           </p>
        </div>

      </div>

      <!-- BACK SIDE -->
      <div 
        class="flip-card-back absolute w-full h-full backface-hidden rotate-y-180 flex flex-col rounded-2xl shadow-xl overflow-hidden bg-gray-800"
      >
        <!-- Top Half: Avatar + Colored BG (Same) -->
        <!-- Click here to flip back -->
        <div 
          class="h-1/4 w-full flex items-center justify-center cursor-pointer relative"
          :style="{ backgroundColor: speakerAttrs.themeColor }"
          @click="toggleFlip"
        >
          <CardAvatar 
             :avatarUrl="speakerAttrs.avatarUrl" 
             :speaker="card.speaker"
          />
        </div>

        <!-- Bottom Half: English + Controls -->
        <div class="flex-grow  w-full bg-gray-800 flex flex-col p-5 pt-10 justify-between">
           <!-- English Text -->
           <p :class="fontSizeEn" class="text-white font-medium leading-relaxed line-clamp-4 select-text">
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
                <IonColorFillSharp class="text-lg" />
             </button>

             <!-- Rec/Play Rec -->
             <div class="flex gap-3">
               <button 
                 class="w-7 h-7 rounded-full flex items-center justify-center transition-all"
                 :class="isRecording ? 'bg-red-500 text-white animate-pulse' : 'bg-gray-700 text-blue-400 hover:bg-gray-600'"
                 @click.stop="toggleRecording"
               >
                  <i-tabler-microphone v-if="!isRecording" class="text-sm" />
                  <i-tabler-player-stop-filled v-else class="text-sm" />
               </button>

               <button 
                 v-if="recordedAudioUrl"
                 class="w-7 h-7 rounded-full flex items-center justify-center bg-green-900/50 text-green-400 hover:bg-green-900 transition-colors"
                 @click.stop="playRecording"
               >
                 <i-tabler-ear class="text-sm" />
               </button>
             </div>

             <!-- Play Original -->
             <button 
               class="w-7 h-7 rounded-full flex items-center justify-center bg-green-500 text-gray-900 hover:bg-green-400 transition-colors shadow-lg shadow-green-500/20"
               @click.stop="toggleOriginal"
               v-if="props.card.content.end_time"
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
