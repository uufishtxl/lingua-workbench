<template>
  <div class="dark-editor">
    <!-- Top row: Tags and Close button -->
    <div class="flex justify-between items-center">
      <!-- <div class="flex items-center gap-2"> -->
      <!-- Tag 图标 -->
      <!-- <i-tabler-tag class="text-gray-400" /> -->
      <!-- Tag 选择器 -->
      <!-- <el-select v-model="editableHighlight.tags" multiple placeholder="Select tags" size="small"  class="tags-select"
          popper-class="dark-popper">
          <el-option v-for="tagOption in allTagOptions" :key="tagOption.value" :label="tagOption.value"
            :value="tagOption.value">
            {{ tagOption.label }}
          </el-option>
        </el-select> -->
      <!-- </div> -->
      <div class="flex items-center gap-2">
        <CilVoice class="text-red-600" />

        <!-- Dynamic phonetic tags from AI -->
        <el-tag 
          v-for="tag in analysisResult?.phonetic_tags ?? []" 
          :key="tag"
          type="success" 
          effect="dark" 
          round
          size="small"
          class="cursor-pointer"
          @click="handleTagClick(tag)"
        >
          {{ tag }}
        </el-tag>
        
        <!-- Placeholder when no tags -->
        <span v-if="!analysisResult" class="text-gray-500 text-xs">点击 ✨ 获取分析</span>
      </div>

      <!-- AI Magic Button with 3 states -->
      <el-button 
        text 
        circle 
        class="ai-magic-btn"
        :class="{
          'is-default': aiStatus === 'default',
          'is-loading': aiStatus === 'loading',
          'is-active': aiStatus === 'active'
        }"
        @click="handleAiClick"
      >
        <i-tabler-loader-2 v-if="aiStatus === 'loading'" class="spin-icon" />
        <HugeiconsAiMagic v-else />
      </el-button>
    </div>

    <!-- Note -->
    <div class="note-input-wrapper">
      <el-input ref="noteInput" v-model="editableHighlight.note" type="textarea" :rows="2"
        placeholder="Add a note..." />
    </div>

    <!-- IPA Keyboard -->
    <div class="flex flex-col gap-1">
      <div class="flex items-center justify-center">
        <el-button class="symbol-button" @click="addSymbol(_symbol)" v-for="(_symbol, sid) in ipaSymbols" :key="sid"
          size="small">{{ _symbol }}</el-button>
      </div>
    </div>

    <!-- Actions -->
    <div class="flex justify-end mt-auto">
      <el-button text circle type="danger" @click="handleDelete">
        <i-tabler-eraser />
      </el-button>
      <el-button text circle type="primary" @click="handleSave">
        <i-tabler-device-floppy />
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import ipaSymbols from '@/data/ipa';
import CilVoice from '~icons/cil/voice';
import HugeiconsAiMagic from '~icons/hugeicons/ai-magic';
import { analyzeSoundScript, type SoundScriptResponse } from '@/api/aiAnalysisApi';

// AI Button States: 'default' | 'loading' | 'active'
type AiStatus = 'default' | 'loading' | 'active'
const aiStatus = ref<AiStatus>('default')

const emit = defineEmits<{
  (e: 'update:highlight', highlight: Hili): void;
  (e: 'delete-highlight', highlightId: string): void;
  (e: 'cancel'): void;
  (e: 'ai-analyze'): void;
}>();

// AI Analysis result
const analysisResult = ref<SoundScriptResponse | null>(null)

// Handle AI button click
const handleAiClick = async () => {
  if (aiStatus.value === 'loading') return
  
  aiStatus.value = 'loading'
  
  try {
    const requestData = {
      full_context: props.fullContext,
      focus_segment: props.highlight.content,
      speed_profile: 'native_fast' as const
    }
    console.log('AI Analysis request:', requestData)
    
    const result = await analyzeSoundScript(requestData)
    
    analysisResult.value = result
    aiStatus.value = 'active'
    
    // Auto-fill the first segment's note
    if (result.script_segments.length > 0) {
      editableHighlight.value.note = result.script_segments
        .map(seg => `${seg.original}: ${seg.sound_display} (${seg.note})`)
        .join('\n')
    }
  } catch (error) {
    console.error('AI analysis failed:', error)
    aiStatus.value = 'default'
  }
}

// Handle tag click - show corresponding segment note
const handleTagClick = (tag: string) => {
  if (!analysisResult.value) return
  
  const segment = analysisResult.value.script_segments.find(s => s.type === tag)
  if (segment) {
    editableHighlight.value.note = `${segment.original}: ${segment.sound_display}\n${segment.ipa}\n${segment.note}`
  }
}

type TagType = 'Flap T' | 'Reduction' | 'Linking' | 'Resyllabification' | 'Flap-T'; // These are the full display names
type AbbreviatedTag = 'FT' | 'RED' | 'LINK' | 'RESYL' | 'FT_HYPHEN'; // These are the actual values stored

interface Hili {
  id: string;
  start: number;
  end: number;
  content: string;
  tags: AbbreviatedTag[]; // tags now store abbreviated values
  note: string;
}

const props = defineProps<{
  highlight: Hili;
  fullContext: string;  // The complete sentence for AI analysis
}>();

const editableHighlight = ref<Hili>({ ...props.highlight });

const noteInput = ref<HTMLElement | null>(null)

const allTagOptions: { value: AbbreviatedTag; label: TagType }[] = [
  { value: 'FT', label: 'Flap T' },
  { value: 'RED', label: 'Reduction' },
  { value: 'LINK', label: 'Linking' },
  { value: 'RESYL', label: 'Resyllabification' },
  { value: 'FT_HYPHEN', label: 'Flap-T' },
];

watch(() => props.highlight, (newHighlight) => {
  editableHighlight.value = { ...newHighlight };
}, { deep: true, immediate: true });

const addSymbol = (symbol: string) => {
  editableHighlight.value.note += symbol
  if (noteInput.value) {
    noteInput.value.focus()
  }
}

const handleSave = () => {
  emit('update:highlight', editableHighlight.value);
};

const handleCancel = () => {
  emit('cancel');
};

const handleDelete = () => {
  emit('delete-highlight', props.highlight.id);
}
</script>

<style scoped>
.dark-editor {
  background-color: #1C1338;
  height: 156px;
  /* Adjusted height for better spacing */
  padding: 8px;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow-x: hidden;
  /* Hide horizontal scrollbar */
}

.tags-select {
  width: 200px;
}

:deep(.el-input__wrapper),
:deep(.el-textarea__inner) {
  background-color: #302849;
  box-shadow: none;
  color: white;
  border: 1px solid #4E466E;
}

:deep(.el-input__inner::placeholder),
:deep(.el-textarea__inner::placeholder) {
  color: #7d7a8c;
}

:deep(.el-select .el-select__tags-text) {
  color: white;
}

:deep(.tags-select .el-tag) {
  --el-tag-bg-color: #4E466E;
  --el-tag-border-color: #675F93;
  --el-tag-hover-color: #7d7a8c;
}

:deep(.el-tag__close) {
  color: white;
}

:deep(.el-tag__close:hover) {
  background-color: #7d7a8c;
}

/* Ensure the el-select's input wrapper also gets the dark background */
:deep(.tags-select .el-input__wrapper) {
  background-color: #302849 !important;
  border: 1px solid #4E466E;
  box-shadow: none;
  color: white;
}

/* For the dropdown options list itself */
:deep(.el-select__wrapper),
:deep(.el-select__selection) {
  background: #1C1338;
}


:deep(.el-select__popper) {
  background-color: #302849 !important;
  border: 1px solid #4E466E;
}

:deep(.el-select-dropdown__item) {
  color: white;
}

:deep(.el-select-dropdown__item.hover),
:deep(.el-select-dropdown__item.selected) {
  background-color: #4E466E !important;
}

:deep(.el-button--small) {
  font-size: 10px;
  padding: 4px 6px;
}

:deep(.el-button:hover) {
  background-color: #4E466E !important;
}

:deep(.symbol-button.el-button) {
  background: black;
  color: white;
}

:deep(.el-tag--small) {
  font-size: 8px;
}

:deep(.el-textarea__inner) {
  border: 1px solid black;
  background: #302849;
  font-size: 10px;
  resize: none;
}

/* AI Magic Button States */
.ai-magic-btn {
  transition: all 0.3s ease;
}

/* Default: 明黄色，吸引用户点击 */
.ai-magic-btn.is-default {
  color: #facc15 !important;
}

.ai-magic-btn.is-default:hover {
  color: #fde047 !important;
  transform: scale(1.1);
}

/* Loading: 蓝色 + 旋转 */
.ai-magic-btn.is-loading {
  color: #60a5fa !important;
  pointer-events: none;
}

/* Active: 淡黄色，表示已有内容 */
.ai-magic-btn.is-active {
  color: #fef08a !important;
  opacity: 0.5;
}

.ai-magic-btn.is-active:hover {
  opacity: 0.8;
  color: #fef9c3 !important;
}

/* Spinning animation for loading */
.spin-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
