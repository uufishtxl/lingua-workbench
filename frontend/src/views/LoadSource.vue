<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { ElMessage, type UploadInstance, type UploadRequestOptions } from 'element-plus'
import api from '@/api/axios'

// --- State for Selects ---
const dramas = ref<{ id: number; name: string }[]>([])
const seasons = ref<number[]>([])
const episodes = ref<number[]>([])

const selection = reactive({
  dramaId: null as number | null,
  season: null as number | null,
  episode: null as number | null,
})

// --- State for UI Control ---
const isLoadingDramas = ref(false)
const isLoadingSeasons = ref(false)
const isLoadingEpisodes = ref(false)
const isLoadingChunks = ref(false)

const showUpload = ref(false)
const showChunkGrid = ref(false)
const showUploadDialog = ref(false)

// --- State for Chunks ---
const chunks = ref<{ id: number; chunk_index: number; has_slices: boolean }[]>([])
const selectedChunkId = ref<number | null>(null)

// --- State for Upload Dialog ---
const uploadDialogForm = reactive({
  dramaId: null as number | null,
  season: null as number | null,
  episode: null as number | null,
})
const uploadInstance = ref<UploadInstance>()

// --- API Functions ---
const fetchDramas = async () => {
  isLoadingDramas.value = true
  try {
    const response = await api.get('/v1/dramas/')
    dramas.value = response.data.results
  } catch (error) {
    ElMessage.error('Failed to fetch dramas.')
    console.error(error)
  } finally {
    isLoadingDramas.value = false
  }
}

const fetchSeasons = async (dramaId: number) => {
  isLoadingSeasons.value = true
  try {
    const response = await api.get(`/v1/dramas/${dramaId}/seasons/`)
    seasons.value = response.data
  } catch (error) {
    ElMessage.error('Failed to fetch seasons.')
    console.error(error)
  } finally {
    isLoadingSeasons.value = false
  }
}

const fetchEpisodes = async (dramaId: number, season: number) => {
  isLoadingEpisodes.value = true
  try {
    const response = await api.get('/v1/audios/episodes/', {
      params: { drama_id: dramaId, season: season }
    })
    episodes.value = response.data
  } catch (error) {
    ElMessage.error('Failed to fetch episodes.')
    console.error(error)
  } finally {
    isLoadingEpisodes.value = false
  }
}

const lookupSourceAudio = async (dramaId: number, season: number, episode: number) => {
  isLoadingChunks.value = true
  showUpload.value = false
  showChunkGrid.value = false
  try {
    const response = await api.get('/v1/audios/lookup/', {
      params: { drama_id: dramaId, season: season, episode: episode }
    })
    chunks.value = response.data
    showChunkGrid.value = true
  } catch (error: any) {
    if (error.response && error.response.status === 404) {
      showUpload.value = true
    } else {
      ElMessage.error('Failed to lookup source audio.')
      console.error(error)
    }
  } finally {
    isLoadingChunks.value = false
  }
}


// --- Watchers for联动 ---
watch(() => selection.dramaId, (newDramaId) => {
  selection.season = null
  selection.episode = null
  seasons.value = []
  episodes.value = []
  showUpload.value = false
  showChunkGrid.value = false
  if (newDramaId) {
    fetchSeasons(newDramaId)
  }
})

watch(() => selection.season, (newSeason) => {
  selection.episode = null
  episodes.value = []
  showUpload.value = false
  showChunkGrid.value = false
  if (selection.dramaId && newSeason) {
    fetchEpisodes(selection.dramaId, newSeason)
  }
})

watch(() => selection.episode, (newEpisode) => {
  if (selection.dramaId && selection.season && newEpisode) {
    lookupSourceAudio(selection.dramaId, selection.season, newEpisode)
  } else {
    showUpload.value = false
    showChunkGrid.value = false
  }
})


// --- Component Lifecycle ---
import { onMounted } from 'vue'
onMounted(async () => {
  await fetchDramas()
  if (dramas.value && dramas.value.length) {
    selection.dramaId = dramas.value[0]?.id 
  }
})

// --- Methods ---
const handleUploadHttpRequest = async (options: UploadRequestOptions) => {
  const { file } = options
  const formData = new FormData()
  formData.append('file', file)

  const dramaId = showUploadDialog.value ? uploadDialogForm.dramaId : selection.dramaId;
  const season = showUploadDialog.value ? uploadDialogForm.season : selection.season;
  const episode = showUploadDialog.value ? uploadDialogForm.episode : selection.episode;

  if (dramaId) formData.append('drama', dramaId.toString());
  if (season) formData.append('season', season.toString());
  if (episode) formData.append('episode', episode.toString());

  try {
    await api.post('/v1/audios/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 120000
    })
    handleUploadSuccess()
  } catch (error) {
    ElMessage.error('Upload failed.')
    console.error(error)
  }
}

const handleUploadSuccess = () => {
    ElMessage.success('Upload successful! Chunks are being processed.')
    showUpload.value = false
    showUploadDialog.value = false
    isLoadingChunks.value = true
    setTimeout(() => {
        const dramaId = selection.dramaId || uploadDialogForm.dramaId;
        const season = selection.season || uploadDialogForm.season;
        const episode = selection.episode || uploadDialogForm.episode;
        if (dramaId && season && episode) {
            lookupSourceAudio(dramaId, season, episode)
        }
    }, 5000)
}

const handleStartEditing = () => {
    if (!selectedChunkId.value) {
        ElMessage.warning('Please select a chunk to start editing.')
        return
    }
    ElMessage.info(`Navigating to workbench for chunk ID: ${selectedChunkId.value}`)
}

const submitUpload = () => {
  if (!uploadDialogForm.dramaId || !uploadDialogForm.season || !uploadDialogForm.episode) {
    ElMessage.warning('Please fill in all fields.')
    return
  }
  console.log(uploadInstance.value)
  uploadInstance.value?.submit()
}

</script>

<template>
  <div class="p-8 flex flex-col h-full">
    <h1 class="text-2xl font-bold mb-6 flex-shrink-0">Load Source Audio</h1>

    <el-card class="mb-6 flex-shrink-0">
      <template #header>
        <div class="card-header">
          <span>1. Select Source</span>
        </div>
      </template>
      <el-row :gutter="20">
        <el-col :span="8">
          <el-select
            v-model="selection.dramaId"
            placeholder="Select Drama"
            allow-create
            filterable
            clearable
            :loading="isLoadingDramas"
            style="width: 100%;"
          >
            <el-option v-for="item in dramas" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-col>
        <el-col :span="8">
          <el-select
            v-model="selection.season"
            placeholder="Select Season"
            allow-create
            filterable
            clearable
            :disabled="!selection.dramaId"
            :loading="isLoadingSeasons"
            style="width: 100%;"
          >
             <el-option v-for="item in seasons" :key="item" :label="`Season ${item}`" :value="item" />
          </el-select>
        </el-col>
        <el-col :span="8">
          <el-select
            v-model="selection.episode"
            placeholder="Select Episode"
            allow-create
            filterable
            clearable
            :disabled="!selection.season"
            :loading="isLoadingEpisodes"
            style="width: 100%;"
          >
            <el-option v-for="item in episodes" :key="item" :label="`Episode ${item}`" :value="item" />
          </el-select>
        </el-col>
      </el-row>
    </el-card>

    <el-card v-if="showUpload" class="mb-6 flex-shrink-0">
        <template #header>
            <div class="card-header">
                <span>2. Upload Source File</span>
            </div>
        </template>
        <el-alert
            title="Source Not Found"
            type="info"
            description="This drama/season/episode combination does not exist yet. Please upload the corresponding audio file."
            :closable="false"
            class="mb-4"
        />
        <el-upload
            class="upload-demo"
            drag
            :http-request="handleUploadHttpRequest"
        >
            <i class="el-icon-upload"></i>
            <div class="el-upload__text">Drop file here or <em>click to upload</em></div>
            <template #tip>
            <div class="el-upload__tip">
                Audio files up to 50MB
            </div>
            </template>
        </el-upload>
    </el-card>

    <el-card v-if="showChunkGrid" v-loading="isLoadingChunks" class="flex-grow flex flex-col">
        <template #header>
            <div class="card-header">
                <span>2. Select a Chunk to Edit</span>
            </div>
        </template>
        <div class="flex-grow overflow-auto pretty-scrollbar">
            <div class="grid grid-cols-10 gap-2">
                <div
                    v-for="chunk in chunks"
                    :key="chunk.id"
                    class="p-4 rounded border text-center cursor-pointer"
                    :class="{
                        'bg-blue-500 text-white': selectedChunkId === chunk.id,
                        'bg-gray-200': chunk.has_slices,
                        'bg-white': !chunk.has_slices && selectedChunkId !== chunk.id
                    }"
                    @click="selectedChunkId = chunk.id"
                >
                    {{ String(chunk.chunk_index).padStart(3, '0') }}
                </div>
            </div>
        </div>
        <div class="pt-4 text-right flex-shrink-0">
            <el-button
                type="primary"
                @click="handleStartEditing"
                :disabled="!selectedChunkId"
                size="large"
            >
                Start Editing
            </el-button>
        </div>
    </el-card>

    <!-- Placeholder for Upload Button -->
    <el-card v-if="!showChunkGrid && !showUpload" class="flex-grow flex flex-col items-center justify-center text-center bg-gray-50">
        <div class="text-gray-500">
            <p class="mb-4">Select a source above to view audio chunks.</p>
            <p class="mb-4 text-sm">Or</p>
            <el-button type="primary" @click="showUploadDialog = true" size="large">
                Upload New Source Audio
            </el-button>
        </div>
    </el-card>

    <!-- Upload Dialog -->
    <el-dialog v-model="showUploadDialog" title="Upload New Source Audio" width="500px">
        <el-form :model="uploadDialogForm" label-position="top">
            <el-form-item label="Drama">
                <el-select v-model="uploadDialogForm.dramaId" placeholder="Select or Create Drama" allow-create filterable style="width: 100%;">
                    <el-option v-for="item in dramas" :key="item.id" :label="item.name" :value="item.id" />
                </el-select>
            </el-form-item>
            <el-form-item label="Season">
                <el-input-number v-model="uploadDialogForm.season" :min="1" placeholder="Season Number" style="width: 100%;" />
            </el-form-item>
            <el-form-item label="Episode">
                <el-input-number v-model="uploadDialogForm.episode" :min="1" placeholder="Episode Number" style="width: 100%;" />
            </el-form-item>
            <el-form-item label="Audio File">
                <el-upload
                    ref="uploadInstance"
                    class="upload-demo"
                    drag
                    :http-request="handleUploadHttpRequest"
                    :auto-upload="false"
                >
                    <i class="el-icon-upload"></i>
                    <div class="el-upload__text">Drop file here or <em>click to upload</em></div>
                </el-upload>
            </el-form-item>
        </el-form>
        <template #footer>
            <span class="dialog-footer">
                <el-button @click="showUploadDialog = false">Cancel</el-button>
                <el-button type="primary" @click="submitUpload">
                    Submit Upload
                </el-button>
            </span>
        </template>
    </el-dialog>

  </div>
</template>

<style scoped>
.pretty-scrollbar::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.pretty-scrollbar::-webkit-scrollbar-track {
  background-color: transparent;
}

.pretty-scrollbar::-webkit-scrollbar-thumb {
  background-color: #dcdfe6;
  border-radius: 3px;
}

.pretty-scrollbar::-webkit-scrollbar-thumb:hover {
  background-color: #c0c4cc;
}

/* Make el-card body a flex container to allow content to grow */
:deep(.el-card__body) {
  display: flex;
  flex-direction: column;
  height: 100%;
}
</style>