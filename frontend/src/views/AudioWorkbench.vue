<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api/axios'
import { getSlicesByChunk, type AudioSliceResponse } from '@/api/slicerApi'
import { ElMessage } from 'element-plus'
import AudioSlicer from '@/components/AudioSlicer.vue'
import ResourceNotFoundJpg from '@/assets/resource_not_found.jpg'

const route = useRoute()
const chunk = ref<any>(null)
const savedSlices = ref<AudioSliceResponse[]>([])
const isLoading = ref(false)
const error = ref<string | null>(null)

// Review mode state
const nextChunkId = ref<number | null>(null)
const totalChunks = ref(0)
const currentIndex = ref(0)

// Check if review mode is enabled via URL query
const isReviewMode = computed(() => route.query.mode === 'review')

// Fetch chunk data function
const fetchChunkData = async (chunkId: string | string[]) => {
  if (!chunkId) {
    error.value = 'No chunk ID provided in the URL.'
    ElMessage.error(error.value)
    return
  }

  // Reset state for new chunk
  chunk.value = null
  savedSlices.value = []
  nextChunkId.value = null
  error.value = null

  isLoading.value = true
  try {
    // Fetch chunk data
    const response = await api.get(`/v1/audiochunks/${chunkId}/`)

    console.log("response are", response)
    chunk.value = response.data
    currentIndex.value = response.data.chunk_index || 0
    
    // Fetch existing slices for this chunk
    const slices = await getSlicesByChunk(Number(chunkId))
    savedSlices.value = slices
    console.log("savedSlices are ", savedSlices.value)
    
    // If in review mode, fetch next chunk info
    if (isReviewMode.value && chunk.value?.source_audio) {
      try {
        // Get all chunks for this source audio to find next
        const chunksResponse = await api.get(`/v1/audiochunks/`, {
          params: { source_audio: chunk.value.source_audio }
        })
        const chunks = chunksResponse.data.results || chunksResponse.data
        totalChunks.value = chunks.length
        
        // Find current chunk's position and next
        const currentIdx = chunks.findIndex((c: any) => c.id === Number(chunkId))
        if (currentIdx !== -1 && currentIdx < chunks.length - 1) {
          nextChunkId.value = chunks[currentIdx + 1].id
        } else {
          nextChunkId.value = null
        }
      } catch (err) {
        console.error('Failed to fetch chunk navigation info:', err)
      }
    }
    
  } catch (err) {
    error.value = 'Failed to fetch audio chunk data.'
    ElMessage.error(error.value)
    console.error(err)
  } finally {
    isLoading.value = false
  }
}

// Watch for route param changes to reload data
watch(
  () => route.params.id,
  (newId) => {
    if (newId) {
      fetchChunkData(newId)
    }
  }
)

onMounted(() => {
  if (route.params.id) {
    fetchChunkData(route.params.id)
  }
})
</script>


<template>
  <div v-loading="isLoading" class="w-full h-full flex-col flex">
    <el-card v-if="error" class="flex-grow flex flex-col items-center justify-center min-h-0">
      <div class="flex-1 w-full h-full min-h-0 relative">
        <img :src="ResourceNotFoundJpg" class="absolute w-full h-full object-contain" alt="Resource Not Found">
        <el-button class="absolute left-[50%] bottom-0 translate-x-[-50%] translate-y-[-50%]">Back to Chunk List</el-button>
      </div>
    </el-card>
    
    <div v-else-if="chunk" class="min-h-0 flex flex-col flex-grow p-2">
      <AudioSlicer 
        class="flex-grow min-h-0" 
        :url="chunk.file" 
        :title="chunk.title" 
        :chunk-id="chunk.id"
        :initial-slices="savedSlices"
        :review-mode="isReviewMode"
        :next-chunk-id="nextChunkId"
        :current-index="currentIndex"
        :total-chunks="totalChunks"
      />
    </div>
  </div>
</template>

<style scoped>
:deep(.el-card__body) {
  width: 100%;
  display: flex;
  flex-direction: column;
  flex-grow: 1;
  min-height: 0;
  padding: 12px;
}
</style>