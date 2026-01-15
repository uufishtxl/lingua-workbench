<template>
  <div class="dark-editor-base dark-textarea h-[210px] p-2 rounded flex flex-col gap-1 overflow-x-hidden">
    <!-- Top row: Note input + Icons -->
    <div class="flex items-center justify-between gap-1.5">
      <!-- Left: Mode Toggle + Note input -->
      <div class="flex items-center gap-1.5 flex-1">
        <!-- Mode Toggle Button -->
        <el-button 
          text 
          circle 
          class="dark-bg-controls"
          @click="aiAnalysis.editorMode.value = aiAnalysis.editorMode.value === 'note' ? 'sound' : 'note'"
          :title="aiAnalysis.editorMode.value === 'note' ? 'AI Note 模式' : 'Sound Display 模式'"
        >
          <i-tabler-notes v-if="aiAnalysis.editorMode.value === 'note'" class="text-red-500" />
          <i-tabler-abc v-else class="text-cyan-400" />
        </el-button>
        <!-- User Note (editable) with inline save button -->
        <div class="relative flex-1">
          <el-input 
            ref="noteInput" 
            v-model="editableHighlight.note" 
            type="textarea" 
            :rows="1"
            :placeholder="aiAnalysis.editorMode.value === 'note' ? '添加笔记...' : '编辑发音...'" 
            class="w-full note-input"
            @keydown.enter.prevent="handleSave_Input"
          />
          <!-- Save Note Button (inside input) -->
          <button 
            class="save-note-btn-inline"
            @click="handleSave_Input"
            :disabled="!editableHighlight.note?.trim()"
            :title="dictionary.isEditingDefinition.value ? '保存定义' : (aiAnalysis.editorMode.value === 'note' ? '保存笔记' : '保存发音')"
          >
            <i-tabler-device-floppy />
          </button>
        </div>
      </div>
      
      <!-- Right: Speed Icon + AI Magic Button -->
      <div class="flex items-center gap-0.5 shrink-0">
        <el-button 
          text 
          circle 
          class="dark-bg-controls"
          @click="aiAnalysis.isFastSpeed.value = !aiAnalysis.isFastSpeed.value"
          :title="aiAnalysis.isFastSpeed.value ? '极速语流' : '日常口语'"
          dark-bg-controls
        >
          <span class="text-md">{{ aiAnalysis.isFastSpeed.value ? '🐇' : '🐢' }}</span>
        </el-button>
        <el-button 
          text 
          size="small"
          circle 
          class="ai-btn dark-bg-controls"
          :class="{ 'is-loading': aiAnalysis.aiStatus.value === 'loading' }"
          @click="handleAiClick"
          title="点击获取 AI 语音图谱"
        >
          <i-tabler-loader-2 v-if="aiAnalysis.aiStatus.value === 'loading'" class="spin-icon" />
          <span v-else>✨</span>
        </el-button>
      </div>
    </div>

    <!-- AI Note 模式: phonetic_tags + notes -->
    <div v-if="aiAnalysis.editorMode.value === 'note' && aiAnalysis.analysisResult.value?.phonetic_tags?.length" class="flex flex-wrap gap-1 text-[10px]">
      <div 
        v-for="(tag, idx) in aiAnalysis.analysisResult.value.phonetic_tags" 
        :key="idx"
        class="segment-note"
        :class="aiAnalysis.getTypeClass(tag)"
        @click="handleTagClick(tag)"
      >
        <span class="type-badge">{{ tag.length > 4 ? tag.slice(0, 4) + '+' : tag }}</span>
        <span class="text-slate-200">{{ aiAnalysis.analysisResult.value.phonetic_tag_notes?.[idx] || '' }}</span>
        <i-tabler-x 
          class="cursor-pointer text-slate-400 text-[10px] opacity-50 hover:opacity-100 hover:text-red-400 transition-opacity" 
          @click.stop="aiAnalysis.handleDeleteNote(idx)" 
        />
      </div>
    </div>

    <!-- Sound Display 模式: script_segments -->
    <div v-if="aiAnalysis.editorMode.value === 'sound' && aiAnalysis.analysisResult.value?.script_segments?.length" class="flex flex-wrap gap-1 text-[10px]">
      <div 
        v-for="(seg, idx) in aiAnalysis.analysisResult.value.script_segments" 
        :key="idx"
        class="segment-note segment-sound-item"
        :class="{ 
          'is-editing': aiAnalysis.editingSegmentIndex.value === idx,
          'is-stressed': seg.is_stressed 
        }"
        @click="handleSegmentClick(idx)"
      >
        <span class="type-badge">{{ seg.original }}</span>
        <span class="text-slate-200">{{ seg.sound_display }}</span>
      </div>
    </div>

    <!-- Dictionary Section -->
    <DictionarySection
      :dictionary-result="dictionary.dictionaryResult.value"
      :dict-status="dictionary.dictStatus.value"
      :example-status="dictionary.exampleStatus.value"
      :show-english-example="dictionary.showEnglishExample.value"
      :is-editing-definition="dictionary.isEditingDefinition.value"
      @dict-click="handleDictClick"
      @toggle-language="dictionary.toggleExampleLanguage"
      @refresh-example="dictionary.handleRefreshExample"
      @definition-click="handleDefinitionClick"
    />

    <!-- Actions -->
    <div class="flex justify-end mt-auto">
      <el-button text circle type="danger" class="dark-bg-controls" @click="handleDelete">
        <i-tabler-eraser />
      </el-button>
      <el-button text circle type="primary" class="dark-bg-controls" @click="handleSave">
        <i-tabler-device-floppy />
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useAiAnalysis } from '@/composables/useAiAnalysis'
import { useDictionary } from '@/composables/useDictionary'
import DictionarySection from './highlight-editor/DictionarySection.vue'
import type { SoundScriptResponse, DictionaryResponse } from '@/api/aiAnalysisApi'

import type { Hili } from '@/types/highlight'

// Props & Emits
const props = defineProps<{
  highlight: Hili
  fullContext: string
  savedAnalysis?: SoundScriptResponse | null
  savedDictionary?: DictionaryResponse | null
}>()

const emit = defineEmits<{
  (e: 'update:highlight', highlight: Hili): void
  (e: 'delete-highlight', highlightId: string): void
  (e: 'cancel'): void
  (e: 'ai-analyze'): void
  (e: 'ai-result', result: SoundScriptResponse): void
  (e: 'save-data', data: { analysis: SoundScriptResponse | null; dictionary: DictionaryResponse | null }): void
}>()

// Editable state
const editableHighlight = ref<Hili>({ ...props.highlight })
const noteInput = ref<HTMLElement | null>(null)

// Computed refs for composables
const fullContextRef = computed(() => props.fullContext)
const focusSegmentRef = computed(() => props.highlight.content)

// Composables
const aiAnalysis = useAiAnalysis({
  fullContext: fullContextRef,
  focusSegment: focusSegmentRef
})

const dictionary = useDictionary({
  fullContext: fullContextRef,
  wordOrPhrase: focusSegmentRef
})

// Watch for prop changes
watch(() => props.highlight, (newHighlight) => {
  editableHighlight.value = { ...newHighlight }
}, { deep: true, immediate: true })

// Initialize from saved data
watch(() => [props.savedAnalysis, props.savedDictionary] as const, ([newAnalysis, newDictionary]) => {
  aiAnalysis.initFromSaved(newAnalysis || null)
  dictionary.initFromSaved(newDictionary || null)
}, { immediate: true })

// Handlers
const handleAiClick = async () => {
  const result = await aiAnalysis.handleAiClick()
  if (result) {
    emit('ai-result', result)
  }
}

const handleDictClick = () => {
  dictionary.handleDictClick()
}

const handleTagClick = (tag: string) => {
  const note = aiAnalysis.handleTagClick(tag)
  if (note) {
    editableHighlight.value.note = note
  }
}

const handleSegmentClick = (idx: number) => {
  const content = aiAnalysis.handleSegmentClick(idx)
  if (content) {
    editableHighlight.value.note = content
  }
}

const handleDefinitionClick = () => {
  const content = dictionary.handleDefinitionClick()
  if (content) {
    editableHighlight.value.note = content
  }
}

const handleSave_Input = () => {
  const content = editableHighlight.value.note?.trim()
  if (!content) return
  
  if (dictionary.isEditingDefinition.value) {
    dictionary.handleSaveDefinition(content)
  } else if (aiAnalysis.editorMode.value === 'note') {
    aiAnalysis.handleSaveNote(content)
  } else {
    aiAnalysis.handleSaveSegment(content)
  }
  
  editableHighlight.value.note = ''
}

const handleSave = () => {
  emit('save-data', {
    analysis: aiAnalysis.analysisResult.value,
    dictionary: dictionary.dictionaryResult.value
  })
  emit('update:highlight', editableHighlight.value)
}

const handleDelete = () => {
  emit('delete-highlight', props.highlight.id)
}
</script>

<style scoped>
/* Note input - specific padding for inline button */
.note-input :deep(.el-textarea__inner) {
  min-height: 28px !important;
  padding: 6px 28px 6px 8px;
  font-size: 11px;
  line-height: 1.4;
}

/* Save note button - positioned inside input */
.save-note-btn-inline {
  position: absolute;
  right: 4px;
  top: 50%;
  transform: translateY(-50%);
  background: transparent;
  border: none;
  cursor: pointer;
  color: #64748b; /* slate-500 */
  font-size: 12px;
  padding: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s;
}

.save-note-btn-inline:hover:not(:disabled) {
  color: #22d3ee; /* cyan-400 */
}

.save-note-btn-inline:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

/* AI Button */
.ai-btn {
  color: #fbbf24 !important; /* amber-400 */
}

.ai-btn.is-loading {
  color: #60a5fa !important; /* blue-400 */
}

/* Segment Note - base styles */
.segment-note {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 4px;
  border-radius: 4px;
  background: #302849;
}

.type-badge {
  font-size: 9px;
  padding: 2px 4px;
  border-radius: 4px;
  font-weight: 600;
}

/* Type colors */
.type-reduction .type-badge { background: #fbbf24; color: #000; }
.type-linking .type-badge { background: #60a5fa; color: #000; }
.type-assimilation .type-badge { background: #34d399; color: #000; }
.type-elision .type-badge { background: #f472b6; color: #000; }
.type-flap .type-badge { background: #a78bfa; color: #000; }
.type-glottal .type-badge { background: #fb923c; color: #000; }
.type-custom .type-badge { background: #22d3ee; color: #000; }
.type-default .type-badge { background: #6b7280; color: #fff; }

/* Sound Display mode - interactive states */
.segment-sound-item {
  cursor: pointer;
  transition: all 0.2s;
}

.segment-sound-item .type-badge {
  background: #22d3ee;
  color: #000;
}

.segment-sound-item:hover {
  background: #3d3566;
}

.segment-sound-item.is-editing {
  background: #4E466E;
  box-shadow: 0 0 0 1px #22d3ee;
}

.segment-sound-item.is-stressed .type-badge {
  background: #f87171;
  color: #fff;
}

.segment-sound-item.is-stressed .note-text {
  color: #fca5a5;
  font-weight: 600;
}
</style>
