<template>
  <div class="flex flex-col">
    <!-- Definition Row -->
    <div class="flex items-center gap-1.5 text-[11px] h-9">
      <span class="shrink-0">📖</span>
      <span 
        v-if="dictionaryResult" 
        class="dict-text" 
        :class="{ 'is-editing': isEditingDefinition }"
        @click="$emit('definition-click')"
        title="点击编辑定义"
      >
        {{ dictionaryResult.word_or_phrase }}: {{ dictionaryResult.definition_cn }}
      </span>
      <span v-else class="text-slate-500 italic">点击右侧 ✨ 获取词义解释</span>
      <!-- Dictionary AI Button -->
      <el-button 
        text 
        size="small"
        circle 
        class="ai-btn ml-auto dark-bg-controls"
        :class="{
          'is-loading': dictStatus === 'loading',
          'is-active': dictStatus === 'active'
        }"
        @click="$emit('dict-click')"
      >
        <i-tabler-loader-2 v-if="dictStatus === 'loading'" class="spin-icon" />
        <span v-else>✨</span>
      </el-button>
    </div>
    
    <!-- Example Row -->
    <div v-if="dictionaryResult?.examples?.length" class="flex items-center gap-1.5 text-[11px] h-9">
      <span class="shrink-0">📝</span>
      <span class="dict-text">
        {{ showEnglishExample ? dictionaryResult?.examples?.[0]?.english : dictionaryResult?.examples?.[0]?.chinese }}
      </span>
      <el-button 
        text 
        size="small" 
        class="text-amber-400 text-[10px] font-semibold dark-bg-controls" 
        @click="$emit('toggle-language')"
        circle
      >
        {{ showEnglishExample ? 'EN' : 'ZH' }}
      </el-button>
      <!-- Refresh Example Button -->
      <el-button 
        text 
        size="small"
        circle 
        class="ai-btn dark-bg-controls"
        :class="{ 'is-loading': exampleStatus === 'loading' }"
        @click="$emit('refresh-example')"
      >
        <i-tabler-loader-2 v-if="exampleStatus === 'loading'" class="spin-icon" />
        <span v-else>✨</span>
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { DictionaryResponse } from '@/api/aiAnalysisApi'

defineProps<{
  dictionaryResult: DictionaryResponse | null
  dictStatus: 'default' | 'loading' | 'active'
  exampleStatus: 'default' | 'loading' | 'active'
  showEnglishExample: boolean
  isEditingDefinition: boolean
}>()

defineEmits<{
  (e: 'dict-click'): void
  (e: 'toggle-language'): void
  (e: 'refresh-example'): void
  (e: 'definition-click'): void
}>()
</script>

<style scoped>
/* Dictionary text - interactive styles */
.dict-text {
  color: #e2e8f0; /* slate-200 */
  flex: 1;
  line-height: 1.25;
  max-height: 36px;
  overflow-y: auto;
  cursor: pointer;
  transition: color 0.2s;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.dict-text::-webkit-scrollbar {
  display: none;
}

.dict-text:hover {
  color: #22d3ee; /* cyan-400 */
}

.dict-text.is-editing {
  color: #fbbf24; /* amber-400 */
}

/* AI Button states */
.ai-btn {
  color: #fbbf24 !important; /* amber-400 */
}

.ai-btn.is-loading {
  color: #60a5fa !important; /* blue-400 */
}

.ai-btn.is-active {
  color: #fef08a !important; /* yellow-200 */
  opacity: 0.6;
}
</style>
