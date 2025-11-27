<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api/axios'
import { ElMessage } from 'element-plus'
import AudioSlicer from '@/components/AudioSlicer.vue'
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
    console.log(chunk.value.file)
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
    <div v-else-if="chunk" class="min-h-0 flex flex-col flex-grow p-2">
      <AudioSlicer class="flex-grow min-h-0" :url="chunk.file" :title="chunk.title"/>
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
  /* Allow the body to shrink beyond its content's minimum size */
}
</style>