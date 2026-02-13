<template>
  <div
    :class="[
      'script-line group relative rounded-lg transition-all duration-200',
      lineBackgroundClass,
    ]"
    @mouseenter="showActions = true"
    @mouseleave="showActions = false"
  >
    <!-- Scene Line -->
    <div v-if="line.line_type === 'scene'" class="scene-header py-3">
      <div class="flex items-center gap-3">
        <span class="flex-1 border-b border-dashed border-gray-300"></span>
        <span class="text-gray-500 text-sm font-medium">{{ line.text }}</span>
        <span class="flex-1 border-b border-dashed border-gray-300"></span>
      </div>
    </div>

    <!-- Dialogue Line -->
    <div v-else-if="line.line_type === 'dialogue'" class="dialogue-line p-3">
      <div class="flex items-start gap-3">
        <!-- Speaker Badge -->
        <span 
          :class="[
            'speaker-badge px-2.5 py-1 rounded-full text-xs font-semibold flex-shrink-0 cursor-pointer hover:opacity-80 transition-opacity',
            speakerColorClass
          ]"
          @click="handleSpeakerClick"
          title="Ask about this line"
        >
          #{{ line.id + " " }}{{ line.speaker }}
        </span>
        
        <!-- Content -->
        <div class="flex-1 min-w-0">
          <div class="flex items-start justify-between gap-3">
            <div class="flex-1">
              <!-- Both Mode: Show EN and ZH -->
              <template v-if="displayLang === 'both'">
                <span class="text-gray-800 leading-relaxed block">{{ line.text }}</span>
                <span v-if="line.text_zh" class="text-gray-500 text-sm leading-relaxed block mt-0.5">
                  {{ line.text_zh }}
                </span>
              </template>
              <!-- Single Language Mode -->
              <span v-else class="text-gray-800 leading-relaxed">
                {{ showChinese && line.text_zh ? line.text_zh : line.text }}
              </span>
              
              <!-- Action Note -->
              <span v-if="line.action_note" class="action-note block mt-1 text-gray-500 text-xs italic">
                ({{ line.action_note }})
              </span>
            </div>

            <!-- Hover Actions (always present, use opacity for visibility) -->
            <div 
              :class="[
                'action-buttons flex items-center gap-1.5 flex-shrink-0 transition-opacity duration-150',
                showActions ? 'opacity-100' : 'opacity-0 pointer-events-none'
              ]"
            >
              <!-- Split -->
              <button
                v-if="canSplit"
                class="icon-btn"
                :title="`Split from here to Chunk #${nextChunkId}`"
                @click="confirmSplit"
              >
                <i-tabler-scissors class="text-sm" />
              </button>
              
              <!-- Search -->
              <button
                class="icon-btn"
                title="Find in audio slices"
                @click="$emit('search', line)"
              >
                <i-tabler-search class="text-sm" />
              </button>
              
              <!-- Toggle Language -->
              <button
                v-if="line.text_zh"
                class="icon-btn"
                :class="{ 'icon-btn-active': showChinese }"
                title="Toggle Chinese/English"
                @click="toggleLocalLang"
              >
                <i-tabler-language class="text-sm" />
              </button>
              
              <!-- Highlight Cycle -->
              <button
                class="icon-btn"
                :class="highlightButtonClass"
                :title="highlightTitle"
                @click="cycleHighlight"
              >
                <i-tabler-highlight class="text-sm" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Action Line (Stage Direction) -->
    <div v-else class="action-line py-2 px-3 text-center">
      <span class="text-gray-500 text-sm italic">({{ line.text }})</span>
    </div>

    <!-- Connected to slice indicator -->
    <span
      v-if="line.slice && !showActions"
      class="absolute right-3 top-1/2 -translate-y-1/2 text-green-500 text-xs"
      title="Connected to audio slice"
    >
      <i-tabler-link class="text-sm" />
    </span>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { ScriptLine } from '@/api/scriptApi'
import { updateScriptLine } from '@/api/scriptApi'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useChatStore } from '@/stores/chatStore'

const props = defineProps<{
  line: ScriptLine
  nextChunkId?: number
  canSplit?: boolean
  displayLang?: 'en' | 'zh' | 'both'
}>()

const emit = defineEmits<{
  split: [index: number]
  search: [line: ScriptLine]
  updated: [line: ScriptLine]
}>()

const showActions = ref(false)
const localLangOverride = ref<'en' | 'zh' | null>(null)  // Local override for single line toggle

// Computed: expose displayLang for template (respects local override for single-lang modes)
const displayLang = computed(() => {
  if (props.displayLang === 'both') return 'both'
  return localLangOverride.value ?? props.displayLang ?? 'en'
})

// Computed: use local override if set, otherwise use parent's displayLang
const showChinese = computed(() => {
  if (props.displayLang === 'both') return false  // Not used in both mode
  const lang = localLangOverride.value ?? props.displayLang ?? 'en'
  return lang === 'zh'
})

// Toggle local language override
const toggleLocalLang = () => {
  if (localLangOverride.value === null) {
    // First toggle: override to opposite of current
    localLangOverride.value = showChinese.value ? 'en' : 'zh'
  } else {
    // Subsequent toggles: flip or clear
    localLangOverride.value = localLangOverride.value === 'zh' ? 'en' : 'zh'
  }
}

// Speaker color mapping (Friends characters)
const speakerColors: Record<string, string> = {
  'Chandler': 'bg-teal-500 text-white',
  'Monica': 'bg-blue-500 text-white',
  'Ross': 'bg-purple-500 text-white',
  'Rachel': 'bg-pink-500 text-white',
  'Joey': 'bg-orange-500 text-white',
  'Phoebe': 'bg-amber-400 text-gray-800',
  'All': 'bg-gray-500 text-white',
}

const speakerColorClass = computed(() => {
  const speaker = props.line.speaker || ''
  return speakerColors[speaker] || 'bg-gray-400 text-white'
})

// Line background based on highlight
const lineBackgroundClass = computed(() => {
  switch (props.line.highlight) {
    case 'yellow':
      return 'bg-yellow-100 hover:bg-yellow-150'
    case 'red':
      return 'bg-red-100 hover:bg-red-150'
    default:
      return 'hover:bg-gray-50'
  }
})

// Highlight button styling
const highlightButtonClass = computed(() => {
  switch (props.line.highlight) {
    case 'yellow':
      return 'text-yellow-500'
    case 'red':
      return 'text-red-500'
    default:
      return ''
  }
})

const highlightTitle = computed(() => {
  switch (props.line.highlight) {
    case 'none':
      return 'Add yellow highlight'
    case 'yellow':
      return 'Change to red highlight'
    case 'red':
      return 'Remove highlight'
    default:
      return 'Toggle highlight'
  }
})

// Cycle through highlight states: none -> yellow -> red -> none
const cycleHighlight = async () => {
  const nextHighlight: Record<string, 'none' | 'yellow' | 'red'> = {
    'none': 'yellow',
    'yellow': 'red',
    'red': 'none',
  }
  
  const newHighlight = nextHighlight[props.line.highlight || 'none']
  
  try {
    const updated = await updateScriptLine(props.line.id, { highlight: newHighlight })
    // Update the line locally through parent
    emit('updated', updated)
  } catch (error) {
    console.error('Failed to update highlight:', error)
    ElMessage.error('Failed to update highlight')
  }
}
// Confirm before split
const confirmSplit = async () => {
  try {
    await ElMessageBox.confirm(
      `Move lines from index ${props.line.index} onwards to Chunk #${props.nextChunkId}?`,
      'Confirm Split',
      { confirmButtonText: 'Split', cancelButtonText: 'Cancel', type: 'warning' }
    )
    emit('split', props.line.index)
  } catch {
    // User cancelled
  }
}

// Global Chat Store
const chatStore = useChatStore()

const handleSpeakerClick = () => {
  chatStore.open()
  chatStore.appendToInput(`台词 #${props.line.id}`)
}
</script>

<style scoped>
.script-line {
  box-sizing: border-box;
}

.action-buttons {
  box-sizing: border-box;
  min-width: 7.5rem;  /* Reserve space for 4 icons */
}

.icon-btn {
  width: 1.75rem;
  height: 1.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.375rem;
  color: rgb(107 114 128);
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.icon-btn:hover {
  color: rgb(55 65 81);
  background-color: rgb(243 244 246);
}

.icon-btn-active {
  color: rgb(59 130 246);
  background-color: rgb(239 246 255);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
