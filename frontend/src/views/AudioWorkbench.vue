<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api/axios'
import { getSlicesByChunk, type AudioSliceResponse, type AudioChunkResponse } from '@/api/slicerApi'
import { ElMessage } from 'element-plus'
import AudioSlicer from '@/components/AudioSlicer.vue'
import ResourceNotFoundJpg from '@/assets/resource_not_found.jpg'

const route = useRoute()
const chunk = ref<AudioChunkResponse | null>(null)
const savedSlices = ref<AudioSliceResponse[]>([])
const isLoading = ref(false)
const error = ref<string | null>(null)

// Review mode state
const nextChunkId = ref<number | null>(null)
const prevChunkId = ref<number | null>(null)
const totalChunks = ref(0)
const currentIndex = ref(0)
const nextEpisodeChunkId = ref<number | null>(null)
const nextSeasonChunkId = ref<number | null>(null)

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
  prevChunkId.value = null
  nextEpisodeChunkId.value = null
  nextSeasonChunkId.value = null
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
    
    // Fetch all chunks for this source audio to find next/prev
    if (chunk.value?.source_audio) {
      try {
        // Get all chunks for this source audio to find next
        const chunksResponse = await api.get(`/v1/audiochunks/`, {
          params: { source_audio: chunk.value.source_audio }
        })
        const chunks = chunksResponse.data.results || chunksResponse.data
        // Ensure chunks are strictly ordered by chunk_index so prev/next calculations are always logical
        chunks.sort((a: AudioChunkResponse, b: AudioChunkResponse) => a.chunk_index - b.chunk_index)
        totalChunks.value = chunks.length
        
        // Find current chunk's position and next/prev
        const currentIdx = chunks.findIndex((c: AudioChunkResponse) => c.id === Number(chunkId))
        
        if (currentIdx > 0) {
          prevChunkId.value = chunks[currentIdx - 1].id
        } else {
          prevChunkId.value = null
        }

        if (currentIdx !== -1 && currentIdx < chunks.length - 1) {
          nextChunkId.value = chunks[currentIdx + 1].id
        } else {
          nextChunkId.value = null
          
          // If this is the last chunk in the episode, find next episode in same season
          if (chunk.value?.source_audio) {
            try {
              const sourceAudioResponse = await api.get(`/v1/sourceaudios/${chunk.value.source_audio}/`)
              const sourceAudio = sourceAudioResponse.data
              
              // Find next episode in same season
              const nextEpisodeResponse = await api.get(`/v1/sourceaudios/`, {
                params: {
                  drama: sourceAudio.drama,
                  season: sourceAudio.season,
                  episode__gt: sourceAudio.episode
                }
              })
              const nextEpisodes = nextEpisodeResponse.data.results || nextEpisodeResponse.data
              
              if (nextEpisodes.length > 0) {
                // Get first chunk of next episode
                const nextEpisode = nextEpisodes[0]
                const firstChunkResponse = await api.get(`/v1/audiochunks/`, {
                  params: { source_audio: nextEpisode.id }
                })
                const firstChunks = firstChunkResponse.data.results || firstChunkResponse.data
                
                if (firstChunks.length > 0) {
                  // Sort by chunk_index and get the first one
                  firstChunks.sort((a: AudioChunkResponse, b: AudioChunkResponse) => a.chunk_index - b.chunk_index)
                  nextEpisodeChunkId.value = firstChunks[0].id
                }
              } else {
                // If no next episode in same season, try next season
                const nextSeasonResponse = await api.get(`/v1/sourceaudios/`, {
                  params: {
                    drama: sourceAudio.drama,
                    season__gt: sourceAudio.season
                  }
                })
                const nextSeasons = nextSeasonResponse.data.results || nextSeasonResponse.data
                
                if (nextSeasons.length > 0) {
                  // Get first chunk of first episode in next season
                  const nextSeason = nextSeasons[0]
                  const firstChunkResponse = await api.get(`/v1/audiochunks/`, {
                    params: { source_audio: nextSeason.id }
                  })
                  const firstChunks = firstChunkResponse.data.results || firstChunkResponse.data
                  
                  if (firstChunks.length > 0) {
                    // Sort by chunk_index and get the first one
                    firstChunks.sort((a: AudioChunkResponse, b: AudioChunkResponse) => a.chunk_index - b.chunk_index)
                    nextSeasonChunkId.value = firstChunks[0].id
                  }
                }
              }
            } catch (err) {
              console.error('Failed to fetch next episode/season info:', err)
            }
          }
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

const handleCompleted = (nextChunkId: number | null) => {
  // This is handled by ChunkCompleteBar internally
  console.log('Chunk completed, next chunk:', nextChunkId)
}

// Rough slicing 完成后重新拉取 slices（波形区域/切片卡展示新生成的 rough slices）
const handleRoughSliced = () => {
  const chunkId = route.params.id
  if (chunkId) {
    fetchChunkData(chunkId)
  }
}

onMounted(() => {
  if (route.params.id) {
    fetchChunkData(route.params.id)
  }
})
</script>

<template>
  <div v-loading="isLoading" class="w-full h-full flex-col flex relative">
    <el-card v-if="error" class="flex-grow flex flex-col items-center justify-center min-h-0">
      <div class="flex-1 w-full h-full min-h-0 relative">
        <img :src="ResourceNotFoundJpg" class="absolute w-full h-full object-contain" alt="Resource Not Found">
        <el-button class="absolute left-[50%] bottom-0 translate-x-[-50%] translate-y-[-50%]">Back to Chunk List</el-button>
      </div>
    </el-card>
    
    <div v-else-if="chunk" class="min-h-0 flex flex-col flex-grow p-2">
      <AudioSlicer 
        ref="slicerRef"
        class="flex-grow min-h-0" 
        :url="chunk.file" 
        :title="chunk.title" 
        :chunk-id="chunk.id"
        :initial-slices="savedSlices"
        :review-mode="isReviewMode"
        :prev-chunk-id="prevChunkId"
        :next-chunk-id="nextChunkId"
        :current-index="currentIndex"
        :total-chunks="totalChunks"
        :next-episode-chunk-id="nextEpisodeChunkId"
        :next-season-chunk-id="nextSeasonChunkId"
        @completed="handleCompleted"
        @rough-sliced="handleRoughSliced"
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