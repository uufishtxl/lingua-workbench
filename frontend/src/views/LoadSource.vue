<script setup lang="ts">
import { ref, reactive, watch, nextTick } from 'vue'
import { ElMessage, type ElSelect, type UploadRequestOptions } from 'element-plus'
import { isAxiosError } from 'axios'
import api from '@/api/axios'
// import waitGif from '@/assets/wait.gif'
import waitJpg from '@/assets/wait.jpg'

// --- State for Selects ---
const dramas = ref<{ id: number; name: string }[]>([])
const seasons = ref<number[]>([])
const episodes = ref<number[]>([])

const serverDramas = ref<{ id: number; name: string }[]>([])
const serverSeasons = ref<number[]>([])

const dramaSelectRef = ref<InstanceType<typeof ElSelect> | null>(null);
const seasonSelectRef = ref<InstanceType<typeof ElSelect> | null>(null);
const episodeSelectRef = ref<InstanceType<typeof ElSelect> | null>(null);

const selection = reactive({
  dramaId: null as number | string | null,
  season: null as number | null,
  episode: null as number | null
})

// --- State for UI Control ---
const isLoadingDramas = ref(false)
const isLoadingSeasons = ref(false)
const isLoadingEpisodes = ref(false)
const isLoadingChunks = ref(false)

const showUpload = ref(false)
const showChunkGrid = ref(false)

// --- State for Chunks ---
const chunks = ref<{ id: number; chunk_index: number; has_slices: boolean }[]>([])
const selectedChunkId = ref<number | null>(null)

// --- API Functions ---
const fetchDramas = async () => {
  isLoadingDramas.value = true
  try {
    const response = await api.get('/v1/dramas/')
    dramas.value = response.data.results
    serverDramas.value = JSON.parse(JSON.stringify(response.data.results)) // 注意：这里是为了进行深拷贝一个纯净的来自服务器的列表，而不至于被任何对 dramas.value 的 mutation 所影响
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
    serverSeasons.value = [...response.data]
    if (!seasons.value.length) {
      ElMessage({
        message:
          "This drama doesn't have any source audio yet. Please enter the Season and Episode numbers to upload a new source.",
        type: 'info',
        duration: 5000
      })
    }
  } catch (error) {
    if (isAxiosError(error)) {
      if (error.response && error.response.status === 404) {
        ElMessage({
          message:
            'This appears to be a new drama. Please enter the Season and Episode numbers to continue with the upload.',
          type: 'info',
          duration: 5000
        })
      } else {
        ElMessage.error('Failed to fetch season list due to an unexpected error. Please try again.')
        console.error(error)
      }
    }
  } finally {
    isLoadingSeasons.value = false
  }
}

const fetchEpisodes = async (dramaId: number | string, season: number) => {
  isLoadingEpisodes.value = true
  try {
    const response = await api.get('/v1/audios/episodes/', {
      params: { drama_id: dramaId, season: season }
    })
    episodes.value = response.data
    if (!episodes.value.length) {
      ElMessage({
        message:
          'This appears to be a new season. Please enter the episode number to continue with the upload.',
        type: 'info',
        duration: 5000
      })
    }
  } catch (error) {
    if (isAxiosError(error)) {
      if (error.response && error.response.status == 404) {
        ElMessage({
          message:
            'This appears to be a new drama and/or a new season. Please enter the Episode number to continue with the upload.',
          type: 'info',
          duration: 5000
        })
      } else {
        ElMessage({ type: 'error', message: 'Failed to fetch episodes.', duration: 5000 })
        console.error(error)
      }
    }
  } finally {
    isLoadingEpisodes.value = false
  }
}

const lookupSourceAudio = async (dramaId: number | string, season: number, episode: number) => {
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

const handleDramaChange = (val: string | number) => {
  if (typeof val === 'string') {
    const existingDrama = dramas.value.find(d => d.name === val);
    if (!existingDrama) {
      const newDrama = { id: -Date.now(), name: val };
      dramas.value.push(newDrama);
      dramas.value.sort((a, b) => a.name.localeCompare(b.name));
      nextTick(() => {
        selection.dramaId = newDrama.id;
      });
    } else {
      selection.dramaId = existingDrama.id;
    }
  }
  if (dramaSelectRef.value) {
    dramaSelectRef.value.blur();
  }
}

const handleSeasonChange = (val: string | number) => {
  if (typeof val === 'string') {
    const numVal = parseInt(val, 10)
    if (!isNaN(numVal)) {
      if (!seasons.value.includes(numVal)) {
        seasons.value.push(numVal)
        seasons.value.sort((a, b) => a - b)
      }
      selection.season = numVal
    }
  }
  if (seasonSelectRef.value) {
    seasonSelectRef.value.blur();
  }
}

const handleEpisodeChange = (val: string | number) => {
  if (typeof val === 'string') {
    const numVal = parseInt(val, 10)
    if (!isNaN(numVal)) {
      if (!episodes.value.includes(numVal)) {
        episodes.value.push(numVal)
        episodes.value.sort((a, b) => a - b)
      }
      selection.episode = numVal
    }
  }
  if (episodeSelectRef.value) {
    episodeSelectRef.value.blur();
  }
}

// --- Watchers for联动 ---
watch(
  () => selection.dramaId,
  (newDramaId) => {
    selection.season = null
    selection.episode = null
    seasons.value = []
    serverSeasons.value = []
    episodes.value = []
    showUpload.value = false
    showChunkGrid.value = false
    if (newDramaId) {
      const isRealDrama = typeof newDramaId === 'number' && serverDramas.value.some(d => d.id === newDramaId);
      if (isRealDrama) {
        fetchSeasons(newDramaId);
      }
    }
  }
)

watch(
  () => selection.season,
  (newSeason) => {
    selection.episode = null
    episodes.value = []
    showUpload.value = false
    showChunkGrid.value = false
    if (selection.dramaId && newSeason) {
      const isRealDrama = typeof selection.dramaId === 'number' && selection.dramaId > 0;
      const isRealSeason = typeof newSeason === 'number' && serverSeasons.value.includes(newSeason);
      if (isRealDrama && isRealSeason) {
        fetchEpisodes(selection.dramaId, newSeason);
      }
    }
  }
)

watch(
  () => selection.episode,
  (newEpisode) => {
    if (selection.dramaId && selection.season && newEpisode) {
      lookupSourceAudio(selection.dramaId, selection.season, newEpisode)
    } else {
      showUpload.value = false
      showChunkGrid.value = false
    }
  }
)


// --- Component Lifecycle ---
import { onMounted } from 'vue'
onMounted(async () => {
  await fetchDramas()
  if (dramas.value && dramas.value.length) {
    selection.dramaId = dramas.value[0]?.id || null
  }
})

// --- Methods ---
const handleUploadHttpRequest = async (options: UploadRequestOptions) => {
  const { file } = options
  const formData = new FormData()
  formData.append('file', file)

  const dramaId = selection.dramaId;
  const season = selection.season;
  const episode = selection.episode;

  let dramaToSend: string | number | null = dramaId;

  // If the dramaId is a negative number, it's a temporary ID for a new drama.
  // We need to find the corresponding name to send to the backend.
  if (typeof dramaId === 'number' && dramaId < 0) {
    const tempDrama = dramas.value.find(d => d.id === dramaId);
    if (tempDrama) {
      dramaToSend = tempDrama.name;
    }
  }

  if (dramaToSend) formData.append('drama', dramaToSend.toString());
  if (season) formData.append('season', season.toString());
  if (episode) formData.append('episode', episode.toString());

  try {
    const response = await api.post('/v1/audios/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 120000
    })
    handleUploadSuccess(response.data)
  } catch (error) {
    ElMessage.error('Upload failed.')
    console.error(error)
  }
}

const handleUploadSuccess = (newSourceAudio: { drama: number, season: number, episode: number }) => {
  ElMessage.success('Upload successful! Chunks are being processed.')
  showUpload.value = false
  isLoadingChunks.value = true

  const tempDramaId = selection.dramaId;
  const realDramaId = newSourceAudio.drama;

  // If the selected dramaId was a temporary one (negative number)
  if (typeof tempDramaId === 'number' && tempDramaId < 0) {
    // Find the placeholder drama in our local list
    const dramaIndex = dramas.value.findIndex(d => d.id === tempDramaId);
    if (dramaIndex !== -1 && dramas.value[dramaIndex]) {
      // Update its ID to the real one from the server
      dramas.value[dramaIndex].id = realDramaId;
    }
    // Also update the main selection model to the real ID
    selection.dramaId = realDramaId;
  }

  // Now, proceed with looking up the chunks for the newly created source
  lookupSourceAudio(newSourceAudio.drama, newSourceAudio.season, newSourceAudio.episode);
}

const handleStartEditing = () => {
  if (!selectedChunkId.value) {
    ElMessage.warning('Please select a chunk to start editing.')
    return
  }
  ElMessage.info(`Navigating to workbench for chunk ID: ${selectedChunkId.value}`)
}
</script>

<template>
  <div class="px-8 flex flex-col h-full">
    <!-- <h1 class="text-2xl font-bold mb-6 flex-shrink-0">Load Source Audio</h1> -->

    <el-card class="mb-6 flex-shrink-0">
      <template #header>
        <div class="card-header">
          <span>1. Select Source</span>
        </div>
      </template>
      <el-row :gutter="20">
        <el-col :span="8">
          <el-select ref="dramaSelectRef" v-model="selection.dramaId" placeholder="Select Drama" allow-create filterable
            clearable :loading="isLoadingDramas" style="width: 100%;" @change="handleDramaChange">
            <el-option v-for="item in dramas" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-col>
        <el-col :span="8">
          <el-select ref="seasonSelectRef" v-model="selection.season" placeholder="Select Season" allow-create
            filterable clearable default-first-option :disabled="!selection.dramaId" :loading="isLoadingSeasons"
            style="width: 100%" @change="handleSeasonChange">
            <el-option v-for="item in seasons" :key="item" :label="`Season ${item}`" :value="item" />
          </el-select>
        </el-col>
        <el-col :span="8">
          <el-select ref="episodeSelectRef" v-model="selection.episode" placeholder="Select Episode" allow-create
            filterable clearable default-first-option :disabled="!selection.season" :loading="isLoadingEpisodes"
            style="width: 100%" @change="handleEpisodeChange">
            <el-option v-for="item in episodes" :key="item" :label="`Episode ${item}`" :value="item" />
          </el-select>
        </el-col>
      </el-row>
    </el-card>

    <el-card v-show="showUpload" class="mb-6 flex-shrink-0">
      <template #header>
        <div class="card-header">
          <span>2. Upload Source File</span>
        </div>
      </template>
      <el-alert title="Source Not Found" type="info"
        description="This drama/season/episode combination does not exist yet. Please upload the corresponding audio file."
        :closable="false" class="mb-4" />
      <el-upload class="upload-demo" drag :http-request="handleUploadHttpRequest">
        <i class="el-icon-upload"></i>
        <div class="el-upload__text">Drop file here or <em>click to upload</em></div>
        <template #tip>
          <div class="el-upload__tip">
            Audio files up to 50MB
          </div>
        </template>
      </el-upload>
    </el-card>

    <el-card v-show="showChunkGrid" v-loading="isLoadingChunks" class="flex-grow flex flex-col">
      <template #header>
        <div class="card-header">
          <span>2. Select a Chunk to Edit</span>
        </div>
      </template>
      <div class="flex-grow overflow-auto pretty-scrollbar">
        <div class="grid grid-cols-10 gap-2">
          <div v-for="chunk in chunks" :key="chunk.id" class="p-4 rounded border text-center cursor-pointer" :class="{
            'bg-blue-500 text-white': selectedChunkId === chunk.id,
            'bg-sky-100': chunk.has_slices,
            'bg-white': !chunk.has_slices && selectedChunkId !== chunk.id
          }" @click="selectedChunkId = chunk.id">
            {{ String(chunk.chunk_index).padStart(3, '0') }}
          </div>
        </div>
      </div>
      <div class="mt-4 text-center flex-shrink-0 w-full">
        <el-button type="primary" @click="handleStartEditing" :disabled="!selectedChunkId" size="large">
          Start Editing
        </el-button>
      </div>
    </el-card>

    <!-- Wait for User Process -->
    <el-card v-show="!showChunkGrid && !showUpload && !isLoadingChunks"
      class="flex-grow flex flex-col items-center justify-center text-center min-h-0">
      <p class="text-xs text-gray-400 mb-2">Fill in Drama/Season/Episode to continue.</p>
      <!-- This div will grow and shrink, and be a container for the image -->
      <div class="flex-1 w-full min-h-0 relative">
        <img :src="waitJpg" class="absolute w-full h-full object-contain" />
      </div>
    </el-card>
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
  width: 100%;
  display: flex;
  flex-direction: column;
  flex-grow: 1;
  min-height: 0;
  /* Allow the body to shrink beyond its content's minimum size */
}
</style>