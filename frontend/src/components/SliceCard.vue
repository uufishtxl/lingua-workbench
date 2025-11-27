<template>
    <el-card>
        <!-- Time Stamp -->
        <div class="w-full flex justify-between items-center text-xs">
            <p class="bg-sky-100 text-blue-400 px-2 py-1 rounded">{{ formatTime(props.start) }}~{{ formatTime(props.end) }}</p>
            <el-button text type="danger" :icon="Delete" class="is-del" circle @click.stop="emit('delete', region.id)"  />
        </div>
        <!-- Original Text 浏览/编辑区域 -->
        <div class="font-semibold relative h-20 text-display-area" ref="textDisplayRef" @mouseup="handleTextSelection">
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
                :current-active-id="activeHighlightId" @click-highlight="handleHighlightClick" />
            <el-button v-if="!isEditingOriginal" text class="absolute bottom-2 right-2 is-edit" :icon="Edit"
                size="small" circle @click="startEditing" />

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
            <HighlightEditor :highlight="activeHighlight" @update:highlight="handleHighlightUpdate"
                @cancel="handleHighlightCancel" @delete-highlight="handleHighlightDelete" />
        </div>
        <div v-else class="bg-slate-900 flex flex-col h-[140px] p-2">
            <BaseWaveSurfer ref="wavesurferRef" :url="props.url" :height="100" :allow-selection="true"
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
                    <el-dropdown @command="handleSpeedChange" trigger="click" popper-class="dark-popper">
                        <el-button size="small" circle class="speed-control-btn control-button is-dark">
                            <span class="text-[0.7em] text-sky-500">{{ currentPlaybackRate }}x</span>
                        </el-button><template #dropdown>
                            <el-dropdown-menu>
                                <el-dropdown-item v-for="speed in speedOptions" :key="speed" :command="speed">
                                    {{ speed }}x
                                </el-dropdown-item>
                            </el-dropdown-menu>
                        </template>
                    </el-dropdown>
                </div>
            </div>
        </div>
    </el-card>

</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted, onUnmounted } from 'vue'
import { Delete, Edit } from '@element-plus/icons-vue'
import { v4 as uuidv4 } from 'uuid';
import { formatTime } from '@/utils/utils';
import InteractiveTextWithHilis from './InteractiveTextWithHilis.vue';
import BaseWaveSurfer from './BaseWaveSurfer.vue';
import HighlightEditor from './HighlightEditor.vue';

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

const mockData = {
    // 1. 原文文本
    text: "Just not enough to put us in the original wedding party.",

    // 2. 高亮数组 (注意 start 和 end 的位置)
    highlights: [
        {
            id: 'uuid-001',          // 唯一ID，用于 key
            start: 4,                // "not enough" 开始的索引
            end: 15,                 // 结束索引
            content: "not enough",   // 对应文本(可选，方便调试)
            tags: ["FT", "RED"], // 使用缩写
            note: "实际听感：No-duh-nuff ( /nɑːdɪˈnʌf/ )" // 笔记
        },
        {
            id: 'uuid-002',
            start: 16,               // "put us in" 开始的索引
            end: 25,                 // 结束索引
            content: "put us in",
            tags: ["LINK", "RESYL"],
            note: "典型的连读：Pu-du-sin"
        }
    ]
};

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
  }
}>();

const emit = defineEmits(['delete'])

const currentSlice = ref({text: "", highlights: []});
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

// --- Playback Speed Control ---
const wavesurferRef = ref<any>(null); // Ref for the BaseWaveSurfer component
const currentPlaybackRate = ref(1);
const speedOptions = [0.5, 0.8, 1];

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
        const offsets = getFlatTextOffsets(textDisplayRef.value, range);
        if (offsets) {
            const rect = range.getBoundingClientRect();
            const parentRect = textDisplayRef.value.getBoundingClientRect();

            selectedTextInfo.value = { text: selectedText, start: offsets.start, end: offsets.end, rect };

            highlighterIconPosition.top = `${rect.top - parentRect.top - 30}px`;
            highlighterIconPosition.left = `${rect.left - parentRect.left + rect.width / 2}px`;
            highlighterIconVisible.value = true;
        }
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

const saveEditing = () => {
    const newText = editingText.value;
    currentSlice.value.text = newText;
    isEditingOriginal.value = false;
};

const cancelEditing = () => {
    isEditingOriginal.value = false;
    editingText.value = '';
};

const handleHighlightClick = (highlightData: Hili) => {
    resetSelection();
    if (activeHighlightId.value === highlightData.id) {
        activeHighlightId.value = null;
    } else {
        activeHighlightId.value = highlightData.id;
    }
};

// --- Click outside to cancel editor ---
const editorWrapperRef = ref<HTMLElement | null>(null);

const handleWindowClickForEditor = (event: MouseEvent) => {
    // If editor is not open, do nothing
    if (!activeHighlightId.value) return;

    const target = event.target as Node;

    // Check if the click is inside the main editor wrapper
    const isClickInsideEditor = editorWrapperRef.value && editorWrapperRef.value.contains(target);

    // Check if the click is inside the select's dropdown popper
    const popperEl = document.querySelector('.dark-select-popper');
    const isClickInsidePopper = popperEl && popperEl.contains(target);

    // If the click is NOT inside the editor AND NOT inside the popper, then cancel.
    if (!isClickInsideEditor && !isClickInsidePopper) {
        handleHighlightCancel();
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
