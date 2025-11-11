<template>
  <el-card v-if="!workbenchVisible" class="episode-loader" shadow="never">
    <template #header>
      <div class="card-header">
        <strong>1. Select Episode to Work On</strong>
      </div>
    </template>

    <el-row :gutter="20">
      <el-col :span="8">
        <el-select
          v-model="selectedShow"
          placeholder="Select Show"
          @change="handleShowChange"
          clearable
          style="width: 100%;"
        >
          <el-option v-for="show in shows" :key="show.id" :label="show.name" :value="show.id" />
        </el-select>
      </el-col>
      <el-col :span="8">
        <el-select
          v-model="selectedSeason"
          placeholder="Select Season"
          @change="handleSeasonChange"
          :disabled="!selectedShow"
          :loading="isLoadingSeasons"
          clearable
          style="width: 100%;"
        >
          <el-option v-for="season in seasons" :key="season.id" :label="season.name" :value="season.id" />
        </el-select>
      </el-col>
      <el-col :span="8">
        <el-select
          v-model="selectedEpisode"
          placeholder="Select Episode"
          @change="handleEpisodeChange"
          :disabled="!selectedSeason"
          :loading="isLoadingEpisodes"
          clearable
          style="width: 100%;"
        >
          <el-option v-for="episode in episodes" :key="episode.id" :label="episode.name" :value="episode.id" />
        </el-select>
      </el-col>
    </el-row>

    <div v-if="chunksForEpisode.length > 0" class="chunk-list-area">
      <h3 class="chunk-list-title">
        2. Select a Chunk for {{ findEpisodeName(selectedEpisode) }}
      </h3>
      
      <el-radio-group v-model="selectedChunkUrl" class="chunk-radio-group">
        <el-radio
          v-for="chunk in chunksForEpisode"
          :key="chunk.url"
          :value="chunk.url"
          border
          class="chunk-radio"
        >
          <strong>{{ chunk.name }}</strong>
          <span>(Duration: {{ chunk.duration }})</span>
        </el-radio>
      </el-radio-group>
    </div>

    <div class="actions">
      <el-button
        v-if="selectedSeason && !selectedEpisode"
        type="success"
        size="large"
        @click="showUploadDialog = true"
        class="action-button"
      >
        Upload New Episode for {{ findSeasonName(selectedSeason) }}
      </el-button>

      <el-button
        v-if="selectedEpisode && chunksForEpisode.length === 0"
        @click="loadChunksForEpisode"
        :loading="isLoadingChunks"
        size="large"
        class="action-button"
      >
        Load Chunks for {{ findEpisodeName(selectedEpisode) }}
      </el-button>
      
      <el-button
        v-if="selectedChunkUrl"
        type="primary"
        size="large"
        @click="startWorkbench"
        class="action-button"
      >
        Start Editing {{ findChunkName(selectedChunkUrl) }}
      </el-button>
    </div>
  </el-card>

  <div v-else class="workbench-container">
    <el-alert
      :title="`Workbench Loaded: ${findEpisodeName(selectedEpisode)} - ${findChunkName(selectedChunkUrl)}`"
      type="success"
      :closable="false"
    >
      <p>Wavesurfer component should now load with this URL:</p>
      <strong>{{ selectedChunkUrl }}</strong>
      <br />
      <el-button @click="resetLoader" style="margin-top: 20px;">
        Load Another Chunk/Episode
      </el-button>
    </el-alert>
    </div>

  <el-dialog v-model="showUploadDialog" title="Upload New Episode">
    </el-dialog>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

// --- 模拟数据库 (Mock Database) ---
// [重要] MOCK_DB.chunks 的结构已更改，以包含更丰富的信息
const MOCK_DB = {
  shows: [{ id: 's1', name: 'Friends' }],
  seasons: [{ id: 'se10', showId: 's1', name: 'Season 10 (Friends)' }],
  episodes: [
    { id: 'ep12', seasonId: 'se10', name: 'S10E12' },
    { id: 'ep11', seasonId: 'se10', name: 'S10E11' },
  ],
  // [MODIFIED] Chunks 现在是对象数组，而不是字符串
  chunks: {
    'ep12': [
      { name: 'Chunk 1', duration: '00:00 - 01:00', url: '/media/s10e12/chunk1.mp3' },
      { name: 'Chunk 2', duration: '01:00 - 02:00', url: '/media/s10e12/chunk2.mp3' },
      { name: 'Chunk 3', duration: '02:00 - 03:00', url: '/media/s10e12/chunk3.mp3' },
      // ... (总共 29 个)
    ],
    'ep11': [
      { name: 'Chunk 1', duration: '00:00 - 01:00', url: '/media/s10e11/chunk1.mp3' },
      { name: 'Chunk 2', duration: '01:00 - 02:00', url: '/media/s10e11/chunk2.mp3' },
    ],
  }
}

// --- 状态 (State) ---

// 1. Selects 的 v-model (与之前相同)
const selectedShow = ref<string | null>(null)
const selectedSeason = ref<string | null>(null)
const selectedEpisode = ref<string | null>(null)

// 2. Selects 的 <el-option> 数据 (与之前相同)
const shows = ref<any[]>([])
const seasons = ref<any[]>([])
const episodes = ref<any[]>([])

// 3. UI 状态
const isLoadingSeasons = ref(false)
const isLoadingEpisodes = ref(false)
const showUploadDialog = ref(false)
const workbenchVisible = ref(false)

// 4. [NEW] 切片选择的状态
interface ChunkInfo {
  name: string;
  duration: string;
  url: string;
}
const chunksForEpisode = ref<ChunkInfo[]>([]) // “主区域”的数据
const selectedChunkUrl = ref<string | null>(null) // `el-radio` 的 v-model
const isLoadingChunks = ref(false)

// (onMounted, mockApiCall 与之前相同)
onMounted(() => {
  mockApiCall(MOCK_DB.shows, 0).then(data => {
    shows.value = data
  })
})
const mockApiCall = (data: any, delay = 500): Promise<any> => {
  return new Promise(resolve => {
    setTimeout(() => {
      resolve(data)
    }, delay)
  })
}

// --- 事件处理 (Event Handlers) ---

// (A) 当 "Show" 改变时
const handleShowChange = (showId: string | null) => {
  // 重置 *所有* 子级
  selectedSeason.value = null
  selectedEpisode.value = null
  selectedChunkUrl.value = null
  seasons.value = []
  episodes.value = []
  chunksForEpisode.value = [] // [MODIFIED]

  if (!showId) return
  isLoadingSeasons.value = true
  const filteredSeasons = MOCK_DB.seasons.filter(s => s.showId === showId)
  mockApiCall(filteredSeasons).then(data => {
    seasons.value = data
    isLoadingSeasons.value = false
  })
}

// (B) 当 "Season" 改变时
const handleSeasonChange = (seasonId: string | null) => {
  // 重置子级
  selectedEpisode.value = null
  selectedChunkUrl.value = null
  episodes.value = []
  chunksForEpisode.value = [] // [MODIFIED]

  if (!seasonId) return
  isLoadingEpisodes.value = true
  const filteredEpisodes = MOCK_DB.episodes.filter(e => e.seasonId === seasonId)
  mockApiCall(filteredEpisodes).then(data => {
    episodes.value = data
    isLoadingEpisodes.value = false
  })
}

// (C) [NEW] 当 "Episode" 改变时 (可选，但更好)
const handleEpisodeChange = () => {
  // 当用户切换剧集时，重置已加载的 chunks
  chunksForEpisode.value = []
  selectedChunkUrl.value = null
}

// (D) [NEW] "Load Chunks" 按钮点击
const loadChunksForEpisode = () => {
  if (!selectedEpisode.value) return
  isLoadingChunks.value = true
  
  // @ts-ignore
  const chunks = MOCK_DB.chunks[selectedEpisode.value] || []
  
  mockApiCall(chunks).then(data => {
    chunksForEpisode.value = data
    isLoadingChunks.value = false
  })
}

// (E) [NEW] "Start Editing" 按钮点击
const startWorkbench = () => {
  if (!selectedChunkUrl.value) return
  
  // 隐藏加载器，显示工作台
  workbenchVisible.value = true
}

// (F) 重置按钮
const resetLoader = () => {
  workbenchVisible.value = false
  // 重置 *部分* 状态，以便用户可以选择同一剧集的 *不同* chunk
  // 我们不重置 selectedShow/Season/Episode
  selectedChunkUrl.value = null 
  // chunksForEpisode.value = [] // (可选) 是否要重新加载 chunk 列表
}


// (Upload 相关函数与之前相同，这里省略以保持简洁)
// const newEpisodeName = ref('')
// const fakeUploadRequest = (options: UploadRequestOptions) => { ... }


// --- 帮助函数 (Helper Functions) ---
const findSeasonName = (seasonId: string | null) => {
  if (!seasonId) return ''
  return MOCK_DB.seasons.find(s => s.id === seasonId)?.name
}
const findEpisodeName = (episodeId: string | null) => {
  if (!episodeId) return ''
  return MOCK_DB.episodes.find(e => e.id === episodeId)?.name
}
const findChunkName = (chunkUrl: string | null) => {
  if (!chunkUrl) return ''
  // 在真实应用中，您会从 chunksForEpisode 中查找
  const chunk = chunksForEpisode.value.find(c => c.url === chunkUrl)
  return chunk ? chunk.name : ''
}
</script>

<style scoped>
.episode-loader {
  max-width: 900px;
  margin: 40px auto;
  border: 1px solid var(--el-border-color);
}
.card-header {
  font-size: 1.2rem;
}

/* [NEW] Main Area (Chunk List) Styles */
.chunk-list-area {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--el-border-color-light);
}
.chunk-list-title {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 16px;
}
.chunk-radio-group {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.chunk-radio {
  width: 100%;
  margin-right: 0; /* 覆盖 el-radio 默认的 margin */
  height: auto;
  padding: 12px;
}
.chunk-radio span {
  margin-left: 12px;
  color: var(--el-text-color-secondary);
}

/* Action Button Styles */
.actions {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--el-border-color-light);
  text-align: center;
}
.action-button {
  min-width: 300px;
  height: 50px;
}

.workbench-container {
  max-width: 900px;
  margin: 40px auto;
}
</style>