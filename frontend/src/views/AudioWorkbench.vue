<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api/axios'
import { ElMessage } from 'element-plus'
import WaveSurfer from '@/components/WaveSurfer.vue'
import ResourceNotFoundJpg from '@/assets/resource_not_found.jpg'

const route = useRoute()
const chunk = ref<any>(null)
const isLoading = ref(false)
const error = ref<string | null>(null)

onMounted(async () => {
  const chunkId = route.params.id
  if (!chunkId) {
    error.value = 'No chunk ID provided in the URL.'
    ElMessage.error(error.value)
    return
  }

  isLoading.value = true
  try {
    const response = await api.get(`/v1/audiochunks/${chunkId}/`)
    chunk.value = response.data
  } catch (err) {
    error.value = 'Failed to fetch audio chunk data.'
    ElMessage.error(error.value)
    console.error(err)
  } finally {
    isLoading.value = false
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
    <div v-else-if="chunk" class="min-h-0">
      <h2 class="text-xl mb-4">Chunk #{{ chunk.chunk_index }} Details</h2>
      <p class="mb-4">File URL: <a :href="chunk.file" target="_blank" class="text-blue-500 hover:underline">{{ chunk.file }}</a></p>
      <pre class="bg-gray-100 p-4 rounded text-sm">{{ JSON.stringify(chunk, null, 2) }}</pre>
      <WaveSurfer :url="chunk.file" :title="`${chunk.drama} - ${chunk.title}`"/>
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
  /* Allow the body to shrink beyond its content's minimum size */
}
</style>