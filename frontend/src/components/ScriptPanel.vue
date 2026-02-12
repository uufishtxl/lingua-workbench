<template>
  <div class="script-panel flex flex-col h-full">
    <!-- Header -->
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-center gap-2">
        <h2 class="font-bold text-gray-700">Script</h2>
        <el-button-group size="small">
          <el-button
            :type="displayLang === 'en' ? 'primary' : 'default'"
            @click="displayLang = 'en'"
          >
            EN
          </el-button>
          <el-button
            :type="displayLang === 'zh' ? 'primary' : 'default'"
            @click="displayLang = 'zh'"
          >
            中文
          </el-button>
          <el-button
            :type="displayLang === 'both' ? 'primary' : 'default'"
            @click="displayLang = 'both'"
          >
            Bi-lingual
          </el-button>
        </el-button-group>
        <!-- Width Toggle Button -->
        <el-button 
          size="small" 
          :type="scriptPanelWidth === 'wide' ? 'primary' : 'default'"
          @click="$emit('toggleWidth')"
          :title="scriptPanelWidth === 'wide' ? 'Shrink panel' : 'Expand panel'"
        >
          <i-tabler-arrows-horizontal class="text-sm" />
        </el-button>
      </div>
      <span v-if="totalCount > 0" class="text-xs text-gray-500">
        {{ lines.length }} / {{ totalCount }} lines
      </span>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex-1 flex items-center justify-center">
      <el-icon class="is-loading text-2xl text-blue-500">
        <i-tabler-loader-2 />
      </el-icon>
    </div>

    <!-- Empty State -->
    <div v-else-if="lines.length === 0" class="flex-1 flex flex-col items-center justify-center text-gray-500">
      <i-tabler-script-x class="text-4xl mb-2" />
      <p class="text-sm">No script loaded</p>
      <el-button
        v-if="canIngest"
        type="primary"
        size="small"
        class="mt-4"
        @click="$emit('ingest')"
      >
        Load Script
      </el-button>
    </div>

    <!-- Script Lines -->
    <div v-else class="flex-1 overflow-y-auto space-y-1.5">
      <TransitionGroup name="list">
        <ScriptLineItem
          v-for="line in lines"
          :key="line.id"
          :line="line"
          :next-chunk-id="nextChunkId"
          :can-split="!!nextChunkId"
          :display-lang="displayLang"
          @split="handleSplit"
          @search="handleSearch"
          @updated="handleLineUpdated"
        />
      </TransitionGroup>
      
      <!-- Load More -->
      <div v-if="hasMore" class="text-center py-4">
        <el-button size="small" @click="loadMore">
          Load More ({{ totalCount - lines.length }} remaining)
        </el-button>
      </div>
    </div>

    <!-- Undo Toast -->
    <Transition name="slide-up">
      <div
        v-if="undoState"
        class="absolute bottom-24 left-4 right-4 bg-gray-800 text-white px-4 py-3 rounded-lg shadow-lg flex items-center justify-between z-10"
      >
        <span>Moved {{ undoState.count }} lines to Chunk #{{ undoState.toChunkId }}</span>
        <el-button type="primary" size="small" @click="handleUndo">
          Undo
        </el-button>
      </div>
    </Transition>

    <!-- Review Mode: Complete & Continue Bar -->
    <ChunkCompleteBar
      v-if="reviewMode"
      :chunk-id="chunkId"
      :next-chunk-id="nextChunkId"
      :is-last-chunk="!nextChunkId"
      :current-index="currentIndex"
      :total-chunks="totalChunks"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import ScriptLineItem from './ScriptLine.vue'
import ChunkCompleteBar from './ChunkCompleteBar.vue'
import {
  getScriptLines,
  splitScript,
  undoSplit,
  type ScriptLine,
} from '@/api/scriptApi'
import { ElMessage } from 'element-plus'

const props = defineProps<{
  chunkId: number
  nextChunkId?: number
  canIngest?: boolean
  // Review mode props
  reviewMode?: boolean
  currentIndex?: number
  totalChunks?: number
  // Width control from parent
  scriptPanelWidth?: 'normal' | 'wide'
}>()

const emit = defineEmits<{
  ingest: []
  searchSlice: [text: string]
  toggleWidth: []
}>()

// State
const displayLang = ref<'en' | 'zh' | 'both'>('zh')
const lines = ref<ScriptLine[]>([])
const totalCount = ref(0)
const loading = ref(false)
const loadLimit = ref(50)

const undoState = ref<{
  count: number
  fromChunkId: number
  toChunkId: number
} | null>(null)

// Computed
const hasMore = computed(() => lines.value.length < totalCount.value)

// Load script lines
const loadLines = async (append = false) => {
  if (!props.chunkId) return
  
  loading.value = true
  try {
    const limit = append ? loadLimit.value + 50 : loadLimit.value
    const response = await getScriptLines(props.chunkId, limit)
    lines.value = response.results
    totalCount.value = response.count
    if (append) loadLimit.value = limit
  } catch (error) {
    console.error('Failed to load script lines:', error)
    ElMessage.error('Failed to load script')
  } finally {
    loading.value = false
  }
}

const loadMore = () => loadLines(true)

// Split handler
const handleSplit = async (startIndex: number) => {
  if (!props.nextChunkId) return
  
  try {
    const result = await splitScript(props.chunkId, startIndex, props.nextChunkId)
    
    // Animate removal
    lines.value = lines.value.filter(line => line.index < startIndex)
    totalCount.value -= result.moved_count
    
    // Show undo toast
    undoState.value = {
      count: result.moved_count,
      fromChunkId: props.chunkId,
      toChunkId: props.nextChunkId,
    }
    
    // Auto-clear undo after 5 seconds
    setTimeout(() => {
      undoState.value = null
    }, 5000)
    
    ElMessage.success(`Moved ${result.moved_count} lines to next chunk`)
  } catch (error) {
    console.error('Failed to split script:', error)
    ElMessage.error('Failed to split script')
  }
}

// Undo handler
const handleUndo = async () => {
  if (!undoState.value) return
  
  try {
    await undoSplit(undoState.value.fromChunkId, undoState.value.toChunkId)
    undoState.value = null
    await loadLines()
    ElMessage.success('Split undone')
  } catch (error) {
    console.error('Failed to undo split:', error)
    ElMessage.error('Failed to undo')
  }
}

// Search handler
const handleSearch = (line: ScriptLine) => {
  emit('searchSlice', line.text)
}

// Line update handler (e.g., highlight changed)
const handleLineUpdated = (updatedLine: ScriptLine) => {
  const index = lines.value.findIndex(l => l.id === updatedLine.id)
  if (index !== -1) {
    lines.value[index] = updatedLine
  }
}

// Watch chunk changes
watch(() => props.chunkId, () => {
  loadLines()
}, { immediate: true })

onMounted(() => {
  if (props.chunkId) {
    loadLines()
  }
})
</script>

<style scoped>
.list-enter-active,
.list-leave-active {
  transition: all 0.3s ease;
}

.list-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.list-leave-to {
  opacity: 0;
  transform: translateY(30px);
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(20px);
}
</style>
