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

      <!-- Speed Icon + AI Magic Button -->
      <div class="flex items-center gap-1">
        <el-button 
          text 
          circle 
          class="speed-btn"
          @click="isFastSpeed = !isFastSpeed"
          :title="isFastSpeed ? '极速语流' : '日常口语'"
        >
          <span class="text-lg">{{ isFastSpeed ? '🐇' : '🐢' }}</span>
        </el-button>
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
    </div>

    <!-- AI Analysis Results (read-only, colored) -->
    <div v-if="analysisResult?.phonetic_tags?.length" class="ai-results">
      <div 
        v-for="(tag, idx) in analysisResult.phonetic_tags" 
        :key="idx"
        class="segment-note"
        :class="getTypeClass(tag)"
      >
        <span class="type-badge">{{ tag }}</span>
        <span class="note-text">{{ analysisResult.phonetic_tag_notes?.[idx] || '' }}</span>
      </div>
    </div>

    <!-- User Note (editable) -->
    <div class="note-input-wrapper">
      <el-input ref="noteInput" v-model="editableHighlight.note" type="textarea" :rows="1"
        placeholder="添加你的笔记..." />
    </div>

    <!-- Dictionary Section -->
    <div class="dictionary-section">
      <!-- Definition Row -->
      <div class="dict-definition">
        <span class="dict-icon">📖</span>
        <span v-if="dictionaryResult" class="dict-text">
          {{ dictionaryResult.word_or_phrase }}: {{ dictionaryResult.definition_cn }}
        </span>
        <span v-else class="dict-placeholder">点击右侧 ✨ 获取词义解释</span>
        <!-- Dictionary AI Button -->
        <el-button 
          text 
          circle 
          class="dict-ai-btn"
          :class="{
            'is-loading': dictStatus === 'loading',
            'is-active': dictStatus === 'active'
          }"
          @click="handleDictClick"
        >
          <i-tabler-loader-2 v-if="dictStatus === 'loading'" class="spin-icon" />
          <span v-else>✨</span>
        </el-button>
      </div>
      <!-- Example Row -->
      <div v-if="dictionaryResult?.examples?.length" class="dict-example">
        <span class="dict-icon">📝</span>
        <span class="dict-text">{{ showEnglishExample ? dictionaryResult?.examples?.[0]?.english : dictionaryResult?.examples?.[0]?.chinese }}</span>
        <el-button 
          text 
          size="small" 
          class="lang-toggle" 
          @click="showEnglishExample = !showEnglishExample"
        >
          {{ showEnglishExample ? 'En' : 'Zh' }}
        </el-button>
        <!-- Refresh Example Button -->
        <el-button 
          text 
          circle 
          class="dict-ai-btn"
          :class="{ 'is-loading': exampleStatus === 'loading' }"
          @click="handleRefreshExample"
        >
          <i-tabler-loader-2 v-if="exampleStatus === 'loading'" class="spin-icon" />
          <span v-else>✨</span>
        </el-button>
      </div>
    </div>

    <!-- IPA Keyboard (disabled) -->
    <!-- <div class="flex flex-col gap-1"> ... </div> -->

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
// import ipaSymbols from '@/data/ipa';
import CilVoice from '~icons/cil/voice';
import HugeiconsAiMagic from '~icons/hugeicons/ai-magic';
import { analyzeSoundScript, lookupDictionary, refreshExample, type SoundScriptResponse, type DictionaryResponse } from '@/api/aiAnalysisApi';

// AI Button States: 'default' | 'loading' | 'active'
type AiStatus = 'default' | 'loading' | 'active'
const aiStatus = ref<AiStatus>('active') // 'default'

// Speed toggle: true = fast, false = normal
const isFastSpeed = ref(true);

// Dictionary display
const dictionaryResult = ref<DictionaryResponse | null>(null);
const showEnglishExample = ref(false);  // false = Chinese, true = English
const dictStatus = ref<AiStatus>('default');
const exampleStatus = ref<AiStatus>('default');
const emit = defineEmits<{
  (e: 'update:highlight', highlight: Hili): void;
  (e: 'delete-highlight', highlightId: string): void;
  (e: 'cancel'): void;
  (e: 'ai-analyze'): void;
  (e: 'ai-result', result: SoundScriptResponse): void;
}>();

const mockData: SoundScriptResponse = {
  speed_profile: "native_normal",
  card_type: "visual_sound_script",
  full_context: "It's up to you. It's your name. You gotta live with it.",
  focus_segment: "up to you",
  phonetic_tags: ["Reduction", "Linking"],
  phonetic_tag_notes: ["to弱化为tuh，元音弱化为schwa", "up to连读成uhp-tuh"],
  script_segments: [
    {
      original: "up",
      sound_display: "uhp",
      ipa: "/ʌp/",
      is_stressed: false,
    },
    {
      original: "to",
      sound_display: "tuh",
      ipa: "/tə/",
      is_stressed: false,
    },
    {
      original: "you",
      sound_display: "yoo",
      ipa: "/ju/",
      is_stressed: true,
    },
  ]
}

// AI Analysis result
const analysisResult = ref<SoundScriptResponse | null>(mockData) // null

// Handle AI button click
const handleAiClick = async () => {
  if (aiStatus.value === 'loading') return
  
  aiStatus.value = 'loading'
  
  try {
    const requestData = {
      full_context: props.fullContext,
      focus_segment: props.highlight.content,
      speed_profile: isFastSpeed.value ? 'native_fast' as const : 'native_normal' as const
    }
    console.log('AI Analysis request:', requestData)
    
    const result = await analyzeSoundScript(requestData)
    
    analysisResult.value = result
    aiStatus.value = 'active'
    console.log(result)
    
    // Emit result to parent (SliceCard)
    emit('ai-result', result)
  } catch (error) {
    console.error('AI analysis failed:', error)
    aiStatus.value = 'default'
  }
}

// Handle dictionary button click
const handleDictClick = async () => {
  if (dictStatus.value === 'loading') return
  
  dictStatus.value = 'loading'
  
  try {
    const requestData = {
      full_context: props.fullContext,
      word_or_phrase: props.highlight.content
    }
    console.log('Dictionary lookup request:', requestData)
    
    const result = await lookupDictionary(requestData)
    
    dictionaryResult.value = result
    dictStatus.value = 'active'
    console.log('Dictionary result:', result)
  } catch (error) {
    console.error('Dictionary lookup failed:', error)
    dictStatus.value = 'default'
  }
}

// Handle refresh example button click
const handleRefreshExample = async () => {
  if (exampleStatus.value === 'loading') return
  if (!dictionaryResult.value) return
  
  exampleStatus.value = 'loading'
  
  try {
    const result = await refreshExample({
      word_or_phrase: dictionaryResult.value.word_or_phrase
    })
    
    // Update the example in dictionaryResult
    dictionaryResult.value.examples = [result.example]
    exampleStatus.value = 'default'
    console.log('Refresh example result:', result)
  } catch (error) {
    console.error('Refresh example failed:', error)
    exampleStatus.value = 'default'
  }
}

// Handle tag click - show corresponding note in user input
const handleTagClick = (tag: string) => {
  if (!analysisResult.value) return
  
  const tagIndex = analysisResult.value.phonetic_tags.indexOf(tag)
  if (tagIndex !== -1 && analysisResult.value.phonetic_tag_notes?.[tagIndex]) {
    editableHighlight.value.note = analysisResult.value.phonetic_tag_notes[tagIndex]
  }
}

// Get CSS class based on segment type
const getTypeClass = (type: string): string => {
  const typeMap: Record<string, string> = {
    'Reduction': 'type-reduction',
    'Linking': 'type-linking',
    'Assimilation': 'type-assimilation',
    'Elision': 'type-elision',
    'Flap T': 'type-flap',
    'Glottal Stop': 'type-glottal'
  }
  return typeMap[type] || 'type-default'
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

// Note: AI results now display separately, no auto-fill to user note

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
  height: 240px; /**156 */
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

/* AI Results Display */
.ai-results {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  font-size: 10px;
}

.segment-note {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 6px;
  border-radius: 4px;
  background: #302849;
}

.type-badge {
  font-size: 8px;
  padding: 1px 4px;
  border-radius: 3px;
  font-weight: 600;
}

.note-text {
  color: #e2e8f0;
}

/* Type colors */
.type-reduction .type-badge { background: #fbbf24; color: #000; }
.type-linking .type-badge { background: #60a5fa; color: #000; }
.type-assimilation .type-badge { background: #34d399; color: #000; }
.type-elision .type-badge { background: #f472b6; color: #000; }
.type-flap .type-badge { background: #a78bfa; color: #000; }
.type-glottal .type-badge { background: #fb923c; color: #000; }
.type-default .type-badge { background: #6b7280; color: #fff; }

/* Dictionary Section */
.dictionary-section {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 11px;
}

.dict-definition,
.dict-example {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  background: #1e293b;
  border-radius: 4px;
}

.dict-icon {
  font-size: 12px;
}

.dict-text {
  color: #e2e8f0;
  flex: 1;
}

.dict-placeholder {
  color: #64748b;
  font-style: italic;
}

.lang-toggle {
  color: #fbbf24 !important;
  font-size: 10px !important;
  font-weight: 600;
}

.dict-ai-btn {
  margin-left: auto;
  color: #fbbf24 !important;
}

.dict-ai-btn.is-loading {
  color: #60a5fa !important;
}

.dict-ai-btn.is-active {
  color: #fef08a !important;
  opacity: 0.6;
}
</style>
