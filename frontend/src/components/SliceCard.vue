<template>
    <el-card>
        <!-- Time Stamp with adjustment arrows inside -->
        <div class="w-full flex justify-between items-center text-xs">
            <div class="flex-1 flex items-center">
                <div
                    class="group bg-sky-100 text-blue-400 px-1 py-1 rounded flex items-center justify-center w-[7rem] transition-all duration-200">
                    <!-- Backward arrow (adjust start earlier) -->
                    <i-tabler-chevron-left class="time-adjust-icon hover-reveal-icon"
                        @click.stop="emit('adjust-start', -0.2)" title="Start -0.2s" />
                    <span class="tracking-widest group-hover:tracking-normal transition-all duration-200">{{
                        formatTime(props.start) }} - {{ formatTime(props.end) }}</span>
                    <!-- Forward arrow (adjust end later) -->
                    <i-tabler-chevron-right class="time-adjust-icon hover-reveal-icon"
                        @click.stop="emit('adjust-end', 0.2)" title="End +0.2s" />
                </div>
                <!-- Toggle Icons: Pronunciation & Idiom -->
                <div class="flex items-center gap-1 ml-2">
                    <i-tabler-volume 
                        :class="isPronunciationHard ? 'text-yellow-400' : 'text-gray-400 hover:text-yellow-300'"
                        class="text-sm cursor-pointer transition-colors pt-0.1"
                        @click.stop="togglePronunciation"
                        title="发音难点" />
                    <i-tabler-bulb 
                        :class="isIdiom ? 'text-yellow-400' : 'text-gray-400 hover:text-yellow-300'"
                        class="text-sm cursor-pointer transition-colors"
                        @click.stop="toggleIdiom"
                        title="习语/生词" />
                </div>
            </div>
            <!-- Button Group: Transcribe / Delete -->
            <div class="flex items-center gap-1">
                <!-- View Mode Buttons (Default) -->
                <template v-if="!activeHighlightId">
                    <el-button text type="primary" circle :loading="isTranscribing" @click.stop="handleTranscribe"
                        title="Speech to Text" :disabled="isEditingOriginal">
                        <ArcticonsLiveTranscribe v-if="!isTranscribing" class="text-sky-500" />
                    </el-button>
                    <el-button text type="danger" :icon="Delete" class="is-del" circle
                        @click.stop="emit('delete', region.id)" :disabled="isEditingOriginal" />
                </template>

                <!-- Edit Mode Buttons (Recording - when Highlight active) -->
                <template v-else>
                    <el-button text :type="isRecording ? 'danger' : 'primary'" circle @click.stop="handleRecordToggle"
                        :title="isRecording ? 'Stop Recording' : 'Start Recording'">
                        <i-tabler-player-stop-filled v-if="isRecording" class="text-red-500 animate-pulse" />
                        <i-tabler-microphone v-else class="text-sky-500" />
                    </el-button>
                    <el-button text type="primary" circle :disabled="!recordedAudioUrl || isRecording"
                        @click.stop="handlePlayRecording" title="Play Recording">
                        <i-tabler-player-play-filled class="text-sky-500" />
                    </el-button>
                </template>
            </div>
        </div>
        <!-- Original Text 浏览/编辑区域 -->
        <div class="font-semibold relative h-20 text-display-area" ref="textDisplayRef" @mouseup="handleTextSelection"
            :style="dynamicTextStyle">
            <div class="original-text__wrapper rounded relative h-full" v-if="isEditingOriginal">
                <el-input v-model="editingText" :auto-size="false" type="textarea" :rows="3" />
                <div class="absolute right-2 bottom-2 input__icons">
                    <el-button text circle size="small" @click="saveEditing">
                        <i-tabler-device-floppy class="text-sm text-green-600" />
                    </el-button>
                    <el-button text circle size="small" @click="cancelEditing">
                        <i-tabler-x class="text-sm text-red-400" />
                    </el-button>
                </div>
            </div>
            <InteractiveTextWithHilis v-else :highlights="currentSlice.highlights" :text="currentSlice.text"
                :current-active-id="activeHighlightId" :analysis-results="analysisResults"
                @click-highlight="handleHighlightClick" />
            <el-button v-if="!isEditingOriginal" text class="absolute bottom-2 right-2 is-edit" :icon="Edit"
                size="small" circle @click="startEditing" :disabled="!!activeHighlightId" />

            <!-- Highlighter Icon -->
            <transition name="fade">
                <el-button v-if="highlighterIconVisible"
                    :style="{ top: highlighterIconPosition.top, left: highlighterIconPosition.left }"
                    class="absolute z-10 highlighter-icon" type="primary" circle size="small"
                    @mousedown.prevent="handleHighlighterClick">
                    <i-tabler-pencil class="text-sm" />
                </el-button>
            </transition>
        </div>
        <!-- Wave / Highlight Editor -->
        <div v-if="activeHighlightId && activeHighlight" ref="editorWrapperRef">
            <HighlightEditor :highlight="activeHighlight" :fullContext="currentSlice.text" :isPlaying="isPlaying"
                :savedAnalysis="savedAnalysisForActive" :savedDictionary="savedDictionaryForActive"
                @play-original="handlePlayOriginal" @update:highlight="handleHighlightUpdate"
                @cancel="handleHighlightCancel" @delete-highlight="handleHighlightDelete"
                @ai-result="handleAiResult" @save-data="handleSaveData" />
        </div>
        <div v-show="!activeHighlightId" class="bg-slate-900 flex flex-col h-[210px] p-2">
            <BaseWaveSurfer ref="wavesurferRef" :url="props.url" :height="170" :allow-selection="true"
                :start="props.start" :end="props.end" @play="isPlaying = true" @pause="isPlaying = false"
                @region-out="handleRegionOut" />
            <div class="flex items-center justify-between px-2">
                <div class="flex items-center gap-2">
                    <el-button size="small" @click="wavesurferRef?.playPause()" circle class="control-button is-dark">
                        <i-tabler-player-play-filled class="text-sky-500 text-xs" v-if="!isPlaying" />
                        <i-tabler-player-pause-filled v-else class="text-sky-500 text-xs" />
                    </el-button>
                    <el-button size="small" @click="handleToggleLoop" circle class="control-button is-dark">
                        <i-tabler-repeat-off v-if="!isLooping" class="text-gray-400 text-xs" />
                        <i-tabler-repeat v-else class="text-sky-500 text-xs" />
                    </el-button>
                </div>
                <div>
                    <PlaybackSpeedControl v-model="currentPlaybackRate" :options="speedOptions" />
                </div>
            </div>
        </div>
    </el-card>

</template>

<script setup lang="ts">
// ============================================================================
// IMPORTS
// ============================================================================
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { Delete, Edit } from '@element-plus/icons-vue'
import { formatTime } from '@/utils/utils'
import type { Region } from 'wavesurfer.js/dist/plugins/regions.js'

// Components
import InteractiveTextWithHilis from './InteractiveTextWithHilis.vue'
import BaseWaveSurfer from './BaseWaveSurfer.vue'
import HighlightEditor from './HighlightEditor.vue'
import PlaybackSpeedControl from './PlaybackSpeedControl.vue'
import ArcticonsLiveTranscribe from '~icons/arcticons/live-transcribe'

// Composables
import { useRecording } from '@/composables/useRecording'
import { useTranscription } from '@/composables/useTranscription'
import { useHighlightSelection } from '@/composables/useHighlightSelection'

// Types
import type { Hili } from '@/types/highlight'
import type { HighlightData } from '@/api/slicerApi'
import type { SoundScriptResponse, DictionaryResponse } from '@/api/aiAnalysisApi'

// ============================================================================
// PROPS & EMITS
// ============================================================================
const props = defineProps<{
    url: string
    start: number
    end: number
    region: {
        id: string
        start: string
        end: string
        originalText: string
    }
    initialHighlights?: HighlightData[]
    initialPronunciationHard?: boolean
    initialIdiom?: boolean
}>()

const emit = defineEmits(['delete', 'adjust-start', 'adjust-end', 'update-markers'])

// ============================================================================
// REFS (State)
// ============================================================================
// Core slice data
const currentSlice = ref({ text: '', highlights: [] as Hili[] })
const activeHighlightId = ref<string | null>(null)

// Marker states
const isPronunciationHard = ref(props.initialPronunciationHard ?? false)
const isIdiom = ref(props.initialIdiom ?? false)

// Editing state
const isEditingOriginal = ref(false)
const editingText = ref('')

// Playback state
const isPlaying = ref(false)
const isLooping = ref(true)
const currentPlaybackRate = ref(1)
const speedOptions = [0.5, 1]

// Template refs
const textDisplayRef = ref<HTMLElement | null>(null)
const wavesurferRef = ref<InstanceType<typeof BaseWaveSurfer> | null>(null)
const editorWrapperRef = ref<HTMLElement | null>(null)

// AI results storage
const analysisResults = ref<Map<string, SoundScriptResponse>>(new Map())
const dictionaryResults = ref<Map<string, DictionaryResponse>>(new Map())

// ============================================================================
// COMPUTED
// ============================================================================
const dynamicTextStyle = computed(() => {
    const textLength = currentSlice.value.text?.length || 0
    let fontSize = '1.2rem'

    if (textLength > 150) fontSize = '0.65rem'
    else if (textLength > 90) fontSize = '0.75rem'
    else if (textLength > 60) fontSize = '0.85rem'
    else if (textLength > 40) fontSize = '1.1rem'

    return { fontSize }
})

const activeHighlight = computed<Hili | undefined>(() => {
    return currentSlice.value.highlights.find(h => h.id === activeHighlightId.value)
})

const savedAnalysisForActive = computed(() => {
    return activeHighlightId.value ? analysisResults.value.get(activeHighlightId.value) : undefined
})

const savedDictionaryForActive = computed(() => {
    return activeHighlightId.value ? dictionaryResults.value.get(activeHighlightId.value) : undefined
})

// ============================================================================
// COMPOSABLES
// ============================================================================
const recording = useRecording()
const { 
    isRecording, 
    recordedAudioUrl, 
    toggleRecording: handleRecordToggle, 
    playRecording: handlePlayRecording, 
    stopRecording 
} = recording

const transcription = useTranscription()
const { isTranscribing } = transcription

const highlightSelection = useHighlightSelection({
    containerRef: textDisplayRef,
    currentText: () => currentSlice.value.text,
    isEditingMode: () => isEditingOriginal.value,
    onHighlightCreated: (highlight: Hili) => {
        currentSlice.value.highlights.push(highlight)
        activeHighlightId.value = highlight.id
    }
})

const { 
    highlighterIconVisible, 
    highlighterIconPosition, 
    handleTextSelection, 
    handleHighlighterClick, 
    resetSelection 
} = highlightSelection

// ============================================================================
// METHODS
// ============================================================================

// --- Marker Toggle ---
const togglePronunciation = () => {
    isPronunciationHard.value = !isPronunciationHard.value
    emit('update-markers', { isPronunciationHard: isPronunciationHard.value, isIdiom: isIdiom.value })
}

const toggleIdiom = () => {
    isIdiom.value = !isIdiom.value
    emit('update-markers', { isPronunciationHard: isPronunciationHard.value, isIdiom: isIdiom.value })
}

// --- Transcription ---
const handleTranscribe = async () => {
    const result = await transcription.transcribe({
        audioUrl: props.url,
        startTime: props.start,
        endTime: props.end
    })
    if (result) {
        currentSlice.value.text = result
    }
}

// --- Editing ---
const startEditing = () => {
    editingText.value = currentSlice.value.text
    isEditingOriginal.value = true
    activeHighlightId.value = null
    resetSelection()
}

const cancelEditing = () => {
    isEditingOriginal.value = false
    editingText.value = ''
    if (isRecording.value) {
        stopRecording()
    }
}

const saveEditing = () => {
    currentSlice.value.text = editingText.value
    isEditingOriginal.value = false
}

// --- Highlight Interaction ---
const handleHighlightClick = (highlightData: Hili) => {
    resetSelection()
    activeHighlightId.value = activeHighlightId.value === highlightData.id ? null : highlightData.id
}

const handleHighlightUpdate = (updatedHighlight: Hili) => {
    const index = currentSlice.value.highlights.findIndex(h => h.id === updatedHighlight.id)
    if (index !== -1) {
        currentSlice.value.highlights.splice(index, 1, updatedHighlight)
    }
    activeHighlightId.value = null
}

const handleHighlightCancel = () => {
    activeHighlightId.value = null
}

const handleHighlightDelete = (highlightId: string) => {
    currentSlice.value.highlights = currentSlice.value.highlights.filter(h => h.id !== highlightId)
    activeHighlightId.value = null
}

// --- Playback ---
const handleToggleLoop = () => {
    isLooping.value = !isLooping.value
}

const handleRegionOut = (region: Region) => {
    if (isLooping.value) {
        region.play()
    } else if (wavesurferRef.value) {
        wavesurferRef.value.pause()
    }
}

const handlePlayOriginal = () => {
    isPlaying.value = !isPlaying.value
    wavesurferRef.value?.playPause()
}

// --- AI Results ---
const handleAiResult = (result: SoundScriptResponse) => {
    if (activeHighlightId.value) {
        analysisResults.value.set(activeHighlightId.value, result)
    }
}

const handleSaveData = (data: { analysis: SoundScriptResponse | null; dictionary: DictionaryResponse | null }) => {
    if (activeHighlightId.value) {
        if (data.analysis) analysisResults.value.set(activeHighlightId.value, data.analysis)
        if (data.dictionary) dictionaryResults.value.set(activeHighlightId.value, data.dictionary)
    }
}

// --- Data Collection (for parent) ---
const getSliceData = () => {
    const highlights: HighlightData[] = currentSlice.value.highlights.map((h: Hili) => ({
        id: h.id,
        start: h.start,
        end: h.end,
        focus_segment: h.content,
        analysis: analysisResults.value.get(h.id) || null,
        dictionary: dictionaryResults.value.get(h.id) || null
    }))

    return {
        start_time: props.start,
        end_time: props.end,
        original_text: currentSlice.value.text,
        highlights,
        is_pronunciation_hard: isPronunciationHard.value,
        is_idiom: isIdiom.value
    }
}

// --- Click Outside (disabled feature, kept for reference) ---
const handleWindowClickForEditor = (event: MouseEvent) => {
    if (!activeHighlightId.value) return
    const target = event.target as Node
    const isClickInsideEditor = editorWrapperRef.value?.contains(target)
    const popperEl = document.querySelector('.dark-popper')
    const isClickInsidePopper = popperEl?.contains(target)
    if (!isClickInsideEditor && !isClickInsidePopper) {
        // 功能已禁用：点击外部自动关闭编辑器，体验不佳容易误触
        // handleHighlightCancel()
    }
}

// ============================================================================
// WATCH
// ============================================================================
watch(() => props.region.originalText, (newText) => {
    currentSlice.value.text = newText
}, { immediate: true })

watch(activeHighlightId, () => {
    if (isRecording.value) stopRecording()
    if (recordedAudioUrl.value) {
        URL.revokeObjectURL(recordedAudioUrl.value)
        recordedAudioUrl.value = null
    }
})

watch(currentPlaybackRate, (newRate) => {
    wavesurferRef.value?.setPlaybackRate(newRate)
})

watch(() => currentSlice.value.text, () => {
    currentSlice.value.highlights = []
    analysisResults.value.clear()
    dictionaryResults.value.clear()
    if (isRecording.value) stopRecording()
})

// ============================================================================
// LIFECYCLE
// ============================================================================
onMounted(() => {
    document.addEventListener('mousedown', handleWindowClickForEditor)
    
    // Initialize from saved highlights
    if (props.initialHighlights?.length) {
        currentSlice.value.highlights = props.initialHighlights.map(hl => ({
            id: hl.id,
            start: hl.start,
            end: hl.end,
            content: hl.focus_segment,
            tags: [],
            note: ''
        }))

        props.initialHighlights.forEach(hl => {
            if (hl.analysis) analysisResults.value.set(hl.id, hl.analysis)
            if (hl.dictionary) dictionaryResults.value.set(hl.id, hl.dictionary)
        })
    }
})

onUnmounted(() => {
    document.removeEventListener('mousedown', handleWindowClickForEditor)
})

// ============================================================================
// EXPOSE
// ============================================================================
defineExpose({ getSliceData })
</script>

<style scoped>
.text-display-area {
    white-space: pre-wrap;
}

:deep(.el-card__body) {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 10px;
}

:deep(.el-button.is-text.is-disabled) {
    color: #888;
}

:deep(.is-del.el-button.is-text) {
    color: oklch(70.4% 0.191 22.216);
}

:deep(.is-edit.el-button.is-text) {
    color: #3AA2E8;
}

:deep(.original-text__wrapper .input__icons .el-button.is-text:hover),
:deep(.original-text__wrapper .input__icons .el-button.is-text:focus) {
    background-color: #302849;
}

.original-text__wrapper {
    background: #1C1338;
    padding: 8px;
}

.original-text__wrapper :deep(.el-textarea__inner) {
    background: transparent;
    font-size: 12px;
    font-weight: 400;
}

:deep(.el-textarea__inner) {
    resize: none;
    scrollbar-width: none;
    color: white;
    border: none;
    box-shadow: none;
}

:deep(.el-textarea__inner::-webkit-scrollbar) {
    display: none;
}

:deep(.el-textarea__inner:focus) {
    box-shadow: none;
}

:deep(.el-button+.el-button) {
    margin-left: 2px;
}

.highlighter-icon {
    transform: translateX(-50%);
}

.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
    opacity: 0;
}
</style>
