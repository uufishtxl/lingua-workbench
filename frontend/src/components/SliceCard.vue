<template>
    <el-card>
        <!-- Time Stamp with adjustment arrows inside -->
        <div class="w-full flex justify-between items-center text-xs">
            <div class="group bg-sky-100 text-blue-400 px-1 py-1 rounded flex items-center justify-center w-[7.5rem] transition-all duration-200">
                <!-- Backward arrow (adjust start earlier) -->
                <i-tabler-chevron-left 
                    class="text-blue-400 text-xs cursor-pointer hover:text-blue-600 w-0 opacity-0 group-hover:w-3 group-hover:opacity-100 transition-all duration-200 overflow-hidden flex-shrink-0" 
                    @click.stop="emit('adjust-start', -0.2)"
                    title="Start -0.2s"
                />
                <span class="tracking-widest group-hover:tracking-normal transition-all duration-200">{{ formatTime(props.start) }}~{{ formatTime(props.end) }}</span>
                <!-- Forward arrow (adjust end later) -->
                <i-tabler-chevron-right 
                    class="text-blue-400 text-xs cursor-pointer hover:text-blue-600 w-0 opacity-0 group-hover:w-3 group-hover:opacity-100 transition-all duration-200 overflow-hidden flex-shrink-0" 
                    @click.stop="emit('adjust-end', 0.2)"
                    title="End +0.2s"
                />
                <!-- Favorite toggle -->
                <i-tabler-star-filled 
                    v-if="isFavorite"
                    class="text-yellow-400 text-xs cursor-pointer ml-1" 
                    @click.stop="toggleFavorite"
                    title="取消收藏"
                />
                <i-tabler-star 
                    v-else
                    class="text-yellow-400 text-xs cursor-pointer hover:text-yellow-400 ml-1" 
                    @click.stop="toggleFavorite"
                    title="收藏"
                />
            </div>
            <div class="flex items-center gap-1">
                <!-- View Mode Buttons (Default) -->
                <template v-if="!activeHighlightId">
                    <el-button 
                        text 
                        type="primary" 
                        circle 
                        :loading="isTranscribing"
                        @click.stop="handleTranscribe"
                        title="Speech to Text"
                        :disabled="isEditingOriginal"
                    >
                        <ArcticonsLiveTranscribe v-if="!isTranscribing" class="text-sky-500" />
                    </el-button>
                    <el-button text type="danger" :icon="Delete" class="is-del" circle @click.stop="emit('delete', region.id)" :disabled="isEditingOriginal" />
                </template>
                
                <!-- Edit Mode Buttons (Recording - when Highlight active) -->
                <template v-else>
                    <el-button 
                        text 
                        :type="isRecording ? 'danger' : 'primary'" 
                        circle 
                        @click.stop="handleRecordToggle"
                        :title="isRecording ? 'Stop Recording' : 'Start Recording'"
                    >
                        <i-tabler-player-stop-filled v-if="isRecording" class="text-red-500 animate-pulse" />
                        <i-tabler-microphone v-else class="text-sky-500" />
                    </el-button>
                    <el-button 
                        text 
                        type="primary" 
                        circle 
                        :disabled="!recordedAudioUrl || isRecording"
                        @click.stop="handlePlayRecording"
                        title="Play Recording"
                    >
                        <i-tabler-player-play-filled class="text-sky-500" />
                    </el-button>
                </template>
            </div>
        </div>
        <!-- Original Text 浏览/编辑区域 -->
        <div class="font-semibold relative h-20 text-display-area" ref="textDisplayRef" @mouseup="handleTextSelection" :style="dynamicTextStyle">
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
            <InteractiveTextWithHilis v-else 
                :highlights="currentSlice.highlights" 
                :text="currentSlice.text"
                :current-active-id="activeHighlightId" 
                :analysis-results="analysisResults"
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
            <HighlightEditor :highlight="activeHighlight" :fullContext="currentSlice.text"
                :savedAnalysis="savedAnalysisForActive"
                :savedDictionary="savedDictionaryForActive"
                @update:highlight="handleHighlightUpdate"
                @cancel="handleHighlightCancel" @delete-highlight="handleHighlightDelete"
                @ai-result="handleAiResult" @save-data="handleSaveData" />
        </div>
        <div v-else class="bg-slate-900 flex flex-col h-[210px] p-2">
            <BaseWaveSurfer ref="wavesurferRef" :url="props.url" :height="170" :allow-selection="true"
                :start="props.start" :end="props.end" @play="isPlaying = true" @pause="isPlaying = false"
                @region-clicked="(region) => isLooping = region.loop" />
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
                    <PlaybackSpeedControl v-model="currentPlaybackRate" :options="speedOptions" @change="handleSpeedChange" />
                </div>
            </div>
        </div>
    </el-card>

</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted, onUnmounted, watch } from 'vue'
import { Delete, Edit } from '@element-plus/icons-vue'
import { v4 as uuidv4 } from 'uuid';
import { formatTime } from '@/utils/utils';
import InteractiveTextWithHilis from './InteractiveTextWithHilis.vue';
import BaseWaveSurfer from './BaseWaveSurfer.vue';
import HighlightEditor from './HighlightEditor.vue';
import { extractAudioSegment } from '@/utils/audioUtils';
import { transcribeAudio, pollTaskUntilComplete } from '@/api/whisperApi';
import ArcticonsLiveTranscribe from '~icons/arcticons/live-transcribe';
import PlaybackSpeedControl from './PlaybackSpeedControl.vue';

// Note: The AbbreviatedTag type is defined in HighlightEditor.vue
// For SliceCard's internal logic, we can just use `string` for simplicity,
// as it only passes the data around. For stricter typing, import from a shared types file.
type AbbreviatedTag = string;

interface Hili {
    id: string;
    start: number;
    end: number;
    content: string;
    tags: AbbreviatedTag[];
    note: string;
}

import type { HighlightData } from '@/api/slicerApi';

const props = defineProps<{
    url: string;
    start: number;
    end: number;
    region: {
    id: string;
    start: string;
    end: string;
    originalText: string;
    tags: string[];
    note: string;
  };
    initialHighlights?: HighlightData[];
    initialFavorite?: boolean;
}>();

const emit = defineEmits(['delete', 'adjust-start', 'adjust-end', 'toggle-favorite'])

// Favorite state - initialize from prop
const isFavorite = ref(props.initialFavorite ?? false)
const toggleFavorite = () => {
    isFavorite.value = !isFavorite.value
    emit('toggle-favorite', isFavorite.value)
}

const currentSlice = ref({text: "", highlights: [] as Hili[]});

// 同步 props.region.originalText 到 currentSlice.text
watch(
    () => props.region.originalText,
    (newText) => {
        currentSlice.value.text = newText;
    },
    { immediate: true } // 初始化时立即执行，而不是等更新后才执行
);

// 根据文本长度动态计算字体大小
const dynamicTextStyle = computed(() => {
    const textLength = currentSlice.value.text?.length || 0;
    let fontSize = '1.2rem';  // 默认 16px
    
    if (textLength > 150) {
        fontSize = '0.65rem';   // 11.2px
    } else if (textLength > 90) {
        fontSize = '0.75rem';  // 12px
    } else if (textLength > 60) {
        fontSize = '0.85rem';   // 12.8px
    } else if (textLength > 40) {
        fontSize = '1.1rem'; // 14px
    }
    
    return { fontSize };
});
const activeHighlightId = ref<string | null>(null);

const isEditingOriginal = ref(false)
const editingText = ref('')

// State for text selection and highlighter icon
const textDisplayRef = ref<HTMLElement | null>(null);
const selectedTextInfo = ref<{ text: string; start: number; end: number; rect: DOMRect | null } | null>(null);
const highlighterIconVisible = ref(false);
const highlighterIconPosition = reactive({ top: '0px', left: '0px' });
const isPlaying = ref(false);
const isLooping = ref(false);
const isTranscribing = ref(false);

// Whisper 转写功能
const handleTranscribe = async () => {
    if (isTranscribing.value) return;
    
    isTranscribing.value = true;
    try {
        const audioBlob = await extractAudioSegment(
            props.url,
            props.start,
            props.end
        );
        const { task_id } = await transcribeAudio(audioBlob);
        const result = await pollTaskUntilComplete(task_id, {
            onStatusChange: (status) => {
                console.log(`Transcription task ${task_id} status: ${status}`);
            }
        });
        
        // 更新文本
        currentSlice.value.text = result;
    } catch (error) {
        console.error('Transcription failed:', error);
    } finally {
        isTranscribing.value = false;
    }
};

// --- Playback Speed Control ---
const wavesurferRef = ref<any>(null); // Ref for the BaseWaveSurfer component
const currentPlaybackRate = ref(1);
const speedOptions = [0.5, 1];

const handleSpeedChange = (rate: number) => {
    currentPlaybackRate.value = rate;
    wavesurferRef.value?.setPlaybackRate(rate);
};

const handleToggleLoop = () => {
    if (wavesurferRef.value) {
        isLooping.value = wavesurferRef.value.toggleLoop();
    }
};

// -----------------------------

// Computed property for the active highlight
const activeHighlight = computed<Hili | undefined>(() => {
    return currentSlice.value.highlights.find(h => h.id === activeHighlightId.value);
});

// Computed properties for saved data (needed for Vue reactivity with Map)
const savedAnalysisForActive = computed(() => {
    return activeHighlightId.value ? analysisResults.value.get(activeHighlightId.value) : undefined;
});

const savedDictionaryForActive = computed(() => {
    return activeHighlightId.value ? dictionaryResults.value.get(activeHighlightId.value) : undefined;
});

// Helper to get flat text offsets from DOM Range
function getFlatTextOffsets(container: HTMLElement, range: Range): { start: number; end: number } | null {
    const preSelectionRange = document.createRange();
    preSelectionRange.selectNodeContents(container);
    preSelectionRange.setEnd(range.startContainer, range.startOffset);
    const start = preSelectionRange.toString().length;

    return {
        start: start,
        end: start + range.toString().length
    };
}

// Handle text selection
const handleTextSelection = () => {
    if (isEditingOriginal.value) return; // Don't show highlighter in edit mode
    const selection = window.getSelection();

    if (!selection || selection.rangeCount === 0 || selection.isCollapsed || !textDisplayRef.value) {
        return;
    }

    const range = selection.getRangeAt(0);
    const selectedText = selection.toString(); // Don't trim

    if (selectedText && textDisplayRef.value.contains(range.commonAncestorContainer)) {
        // Use string search instead of DOM position to avoid ruby text interference
        const originalText = currentSlice.value.text;
        const startIndex = originalText.indexOf(selectedText);
        
        if (startIndex === -1) {
            // Selected text not found in original (might include ruby text content)
            resetSelection();
            return;
        }
        
        const rect = range.getBoundingClientRect();
        const parentRect = textDisplayRef.value.getBoundingClientRect();

        selectedTextInfo.value = { 
            text: selectedText, 
            start: startIndex, 
            end: startIndex + selectedText.length, 
            rect 
        };

        highlighterIconPosition.top = `${rect.top - parentRect.top - 30}px`;
        highlighterIconPosition.left = `${rect.left - parentRect.left + rect.width / 2}px`;
        highlighterIconVisible.value = true;
    } else {
        resetSelection();
    }
};

// Reset selection state and hide highlighter icon
const resetSelection = () => {
    highlighterIconVisible.value = false;
};

// Handle click on highlighter icon
const handleHighlighterClick = () => {
    if (!selectedTextInfo.value) return;

    const newHighlight: Hili = {
        id: uuidv4(),
        start: selectedTextInfo.value.start,
        end: selectedTextInfo.value.end,
        content: selectedTextInfo.value.text,
        tags: [],
        note: '',
    };
    currentSlice.value.highlights.push(newHighlight);
    activeHighlightId.value = newHighlight.id; // Open editor for the new highlight
    window.getSelection()?.removeAllRanges();
    resetSelection();
};

// Global mouseup listener to clear selection
const handleWindowMouseUp = (event: MouseEvent) => {
    // A brief timeout allows the highlighter click to register before the selection is cleared.
    setTimeout(() => {
        const selection = window.getSelection();
        if (!selection || selection.isCollapsed) {
            resetSelection();
        }
    }, 100);
};

const startEditing = () => {
    editingText.value = currentSlice.value.text;
    isEditingOriginal.value = true;
    activeHighlightId.value = null;
    resetSelection();
};

const cancelEditing = () => {
    isEditingOriginal.value = false;
    editingText.value = '';
    // Stop recording if active when canceling
    if (isRecording.value) {
        stopRecording();
    }
};

const saveEditing = () => {
    const newText = editingText.value;
    currentSlice.value.text = newText;
    
    // Clear all highlights and analysis results since positions are invalidated
    currentSlice.value.highlights = [];
    analysisResults.value.clear();
    
    isEditingOriginal.value = false;
    // Stop recording if active when saving
    if (isRecording.value) {
        stopRecording();
    }
};

// --- Recording Logic ---
const isRecording = ref(false);
const recordedAudioUrl = ref<string | null>(null);
let mediaRecorder: MediaRecorder | null = null;
let audioChunks: Blob[] = [];

const handleRecordToggle = async () => {
    if (isRecording.value) {
        stopRecording();
    } else {
        await startRecording();
    }
};

const startRecording = async () => {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            if (recordedAudioUrl.value) {
                URL.revokeObjectURL(recordedAudioUrl.value);
            }
            recordedAudioUrl.value = URL.createObjectURL(audioBlob);
        };

        mediaRecorder.start();
        isRecording.value = true;
    } catch (err) {
        console.error('Error accessing microphone:', err);
        // You might want to show a user-friendly error message here
    }
};

const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
    }
    isRecording.value = false;
};

const handlePlayRecording = () => {
    if (recordedAudioUrl.value) {
        const audio = new Audio(recordedAudioUrl.value);
        audio.play();
    }
};

// Clean up URL on unmount
onUnmounted(() => {
    if (recordedAudioUrl.value) {
        URL.revokeObjectURL(recordedAudioUrl.value);
    }
});

const handleHighlightClick = (highlightData: Hili) => {
    resetSelection();
    if (activeHighlightId.value === highlightData.id) {
        activeHighlightId.value = null;
    } else {
        activeHighlightId.value = highlightData.id;
    }
};

// Stop recording when active highlight changes or is closed
watch(activeHighlightId, (newId, oldId) => {
    if (isRecording.value) {
        stopRecording();
    }
    // Optional: Clear recorded audio when switching highlights?
    // User said "recording doesn't need to be saved", so maybe clear it to avoid confusion.
    if (recordedAudioUrl.value) {
        URL.revokeObjectURL(recordedAudioUrl.value);
        recordedAudioUrl.value = null;
    }
});

// --- Click outside to cancel editor ---
const editorWrapperRef = ref<HTMLElement | null>(null);

const handleWindowClickForEditor = (event: MouseEvent) => {
    // If editor is not open, do nothing
    if (!activeHighlightId.value) return;

    const target = event.target as Node;

    // Check if the click is inside the main editor wrapper
    const isClickInsideEditor = editorWrapperRef.value && editorWrapperRef.value.contains(target);

    // Check if the click is inside the select's dropdown popper
    const popperEl = document.querySelector('.dark-popper');
    const isClickInsidePopper = popperEl && popperEl.contains(target);

    // If the click is NOT inside the editor AND NOT inside the popper, then cancel.
    if (!isClickInsideEditor && !isClickInsidePopper) {
        // handleHighlightCancel();
    }
};

onMounted(() => {
    document.addEventListener('mouseup', handleWindowMouseUp);
    document.addEventListener('mousedown', handleWindowClickForEditor);
});

onUnmounted(() => {
    document.removeEventListener('mouseup', handleWindowMouseUp);
    document.removeEventListener('mousedown', handleWindowClickForEditor);
});
// -----------------------------------------

const handleHighlightUpdate = (updatedHighlight: Hili) => {
    const index = currentSlice.value.highlights.findIndex(h => h.id === updatedHighlight.id);
    if (index !== -1) {
        currentSlice.value.highlights.splice(index, 1, updatedHighlight);
    }
    activeHighlightId.value = null;
};

const handleHighlightCancel = () => {
    activeHighlightId.value = null;
};

const handleHighlightDelete = (highlightId: string) => {
    currentSlice.value.highlights = currentSlice.value.highlights.filter(h => h.id !== highlightId);
    activeHighlightId.value = null; // Close editor after deletion
};

// Store AI analysis results per highlight
import type { SoundScriptResponse, DictionaryResponse } from '@/api/aiAnalysisApi';
const analysisResults = ref<Map<string, SoundScriptResponse>>(new Map());
const dictionaryResults = ref<Map<string, DictionaryResponse>>(new Map());

// Initialize from saved highlights (must be after analysisResults/dictionaryResults declared)
onMounted(() => {
    if (props.initialHighlights?.length) {
        // Restore highlights
        currentSlice.value.highlights = props.initialHighlights.map(hl => ({
            id: hl.id,
            start: hl.start,
            end: hl.end,
            content: hl.focus_segment,
            tags: [],
            note: ''
        }));
        
        // Restore analysis and dictionary results into Maps
        props.initialHighlights.forEach(hl => {
            if (hl.analysis) {
                analysisResults.value.set(hl.id, hl.analysis);
            }
            if (hl.dictionary) {
                dictionaryResults.value.set(hl.id, hl.dictionary);
            }
        });
    }
});

const handleAiResult = (result: SoundScriptResponse) => {
    if (activeHighlightId.value) {
        analysisResults.value.set(activeHighlightId.value, result);
        console.log('AI Result stored for highlight:', activeHighlightId.value, result);
    }
};

const handleSaveData = (data: { analysis: SoundScriptResponse | null; dictionary: DictionaryResponse | null }) => {
    if (activeHighlightId.value) {
        if (data.analysis) {
            analysisResults.value.set(activeHighlightId.value, data.analysis);
        }
        if (data.dictionary) {
            dictionaryResults.value.set(activeHighlightId.value, data.dictionary);
        }
    }
};

// Expose method for parent to collect data for saving
// HighlightData imported at top of script

const getSliceData = () => {
    // Store raw API responses directly - no conversion needed
    const highlights: HighlightData[] = currentSlice.value.highlights.map((h: Hili) => {
        const analysis = analysisResults.value.get(h.id);
        const dictionary = dictionaryResults.value.get(h.id);
        
        return {
            id: h.id,
            start: h.start,
            end: h.end,
            focus_segment: h.content,
            analysis: analysis || null,
            dictionary: dictionary || null
        };
    });

    return {
        start_time: props.start,
        end_time: props.end,
        original_text: currentSlice.value.text,
        highlights,
        is_favorite: isFavorite.value
    };
};

defineExpose({ getSliceData });
</script>

<style scoped>
.text-display-area {
    white-space: pre-wrap;
    /* This is the critical fix */
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
