<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  listTextbooks,
  listCorpusTasks,
  getTtsData,
  getCorpusTaskModules,
  updateTtsSlices,
  type Textbook,
  type CorpusTask,
  type TtsTimestamp,
} from '@/api/corpusApi'
import ModuleView from '@/components/corpus/ModuleView.vue'

// --- 选择器：年级/学期（Textbook）→ Unit（有音频的任务） ---
const textbooks = ref<Textbook[]>([])
const tasks = ref<CorpusTask[]>([])
const selectedTextbookId = ref<number | null>(null)
const selectedTaskId = ref<number | null>(null)
const isLoading = ref(false)

// 可跟读任务：有音频
const availableTasks = computed(() =>
  tasks.value.filter((t) => t.tts_audio_url && t.tts_status === 'done'),
)

const loadTextbooks = async () => {
  isLoading.value = true
  try {
    const [tbs, tks] = await Promise.all([listTextbooks(), listCorpusTasks()])
    textbooks.value = tbs
    tasks.value = tks
    const first = tbs.find(() => true)
    if (first) {
      selectedTextbookId.value = first.id
      onTextbookChange()
    }
  } catch (e: any) {
    ElMessage.error(`加载失败: ${e?.message ?? e}`)
  } finally {
    isLoading.value = false
  }
}

const onTextbookChange = () => {
  selectedTaskId.value = null
  ttsData.value = null
  const firstTask = availableTasks.value.find((t) => t.textbook === selectedTextbookId.value)
  if (firstTask) {
    selectedTaskId.value = firstTask.id
    loadTask(firstTask.id)
  }
}

// --- 跟读数据 ---
const AUDIO_MODULES = [
  { key: 'fun_time', label: 'Fun Time' },
  { key: 'talking_time', label: 'Talking Time' },
  { key: 'story_time', label: 'Story Time' },
  { key: 'project', label: 'Project' },
]
const TEXT_MODULES = [
  { key: 'topic_words', label: 'Topic Words' },
  { key: 'words_to_use', label: 'Words to use' },
]

const ttsData = ref<{ tts_audio_url: string; tts_timestamps: Record<string, TtsTimestamp[]> } | null>(null)
const textModules = ref<Record<string, unknown>>({})
const activeTab = ref('fun_time')
const audioRef = ref<HTMLAudioElement | null>(null)
const currentTime = ref(0)
const isPlaying = ref(false)
// 句子播放模式：点击句子后只播这一句（到 end 自动暂停）
const sentenceEnd = ref<number | null>(null)

const currentSentences = computed<TtsTimestamp[]>(() =>
  ttsData.value?.tts_timestamps?.[activeTab.value] ?? [],
)

const currentSentenceIndex = computed(() => {
  const t = currentTime.value
  return currentSentences.value.findIndex(
    (s) => s.start != null && s.end != null && t >= s.start && t < s.end,
  )
})

// --- 音频切片表（整个音频 1 个 chunk，句子为 slices，可编辑试听） ---
interface SliceRow {
  modKey: string
  modLabel: string
  idx: number
  text: string
  start: number | null
  end: number | null
}

const slices = ref<SliceRow[]>([])
const audioDuration = ref(0)

const buildSlices = () => {
  const rows: SliceRow[] = []
  if (!ttsData.value) return
  for (const m of AUDIO_MODULES) {
    const list = ttsData.value.tts_timestamps[m.key] ?? []
    list.forEach((s, i) =>
      rows.push({ modKey: m.key, modLabel: m.label, idx: i, text: s.text, start: s.start, end: s.end }),
    )
  }
  slices.value = rows
}

const onLoadedMetadata = () => {
  audioDuration.value = audioRef.value?.duration ?? 0
}

const saveSlices = async () => {
  if (!ttsData.value || !selectedTaskId.value) return
  const timestamps: Record<string, TtsTimestamp[]> = {}
  for (const m of AUDIO_MODULES) {
    timestamps[m.key] = slices.value
      .filter((r) => r.modKey === m.key)
      .map((r) => ({ text: r.text, start: r.start, end: r.end }))
  }
  try {
    await updateTtsSlices(selectedTaskId.value, timestamps)
    ttsData.value = { ...ttsData.value, tts_timestamps: timestamps }
    ElMessage.success('切片时间已保存')
  } catch (e: any) {
    ElMessage.error(`保存失败: ${e?.response?.data?.error ?? e?.message ?? e}`)
  }
}

const playSlice = (row: SliceRow) => playSentence({ text: row.text, start: row.start, end: row.end })

const loadTask = async (taskId: number) => {
  try {
    const [td, mods] = await Promise.all([getTtsData(taskId), getCorpusTaskModules(taskId)])
    ttsData.value = td
    textModules.value = mods
    // 默认切到第一个有音频的模块
    const first = AUDIO_MODULES.find((m) => (td.tts_timestamps[m.key]?.length ?? 0) > 0)
    activeTab.value = first?.key ?? 'fun_time'
    buildSlices()
    if (audioRef.value) {
      audioRef.value.currentTime = 0
    }
  } catch (e: any) {
    ElMessage.error(`加载跟读数据失败: ${e?.response?.data?.error ?? e?.message ?? e}`)
  }
}

const onTaskChange = (taskId: number) => {
  loadTask(taskId)
}

const playSentence = (s: TtsTimestamp) => {
  const a = audioRef.value
  if (!a || s.start == null) return
  sentenceEnd.value = s.end != null ? s.end : null
  // 先 play（promise resolve 表示音频已就绪、缓冲开始加载），再 seek 到目标句。
  // 对 130s 大 WAV 最可靠（seek 前必须保证音频已加载，否则 seek 回退从头）。
  a.play()
    .then(() => {
      a.currentTime = s.start!
    })
    .catch(() => {
      // autoplay 被拒/加载失败：先 seek 再尝试播放
      a.currentTime = s.start!
      a.play().catch(() => {})
    })
}

const onTimeUpdate = () => {
  if (audioRef.value) {
    currentTime.value = audioRef.value.currentTime
    // 句子播放模式：到达句尾自动暂停
    if (sentenceEnd.value != null && currentTime.value >= sentenceEnd.value) {
      audioRef.value.pause()
      sentenceEnd.value = null
    }
  }
}

const onPlay = () => (isPlaying.value = true)
const onPause = () => (isPlaying.value = false)
const onEnded = () => {
  isPlaying.value = false
  currentTime.value = 0
  sentenceEnd.value = null
}

onMounted(loadTextbooks)
</script>

<template>
  <div class="p-8 max-w-6xl mx-auto">
    <!-- 页头 -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold">教材学习</h1>
      <p class="text-gray-500 mt-1">选择教材与单元，逐句跟读练习</p>
    </div>

    <!-- 选择器 -->
    <div class="flex items-center gap-4 mb-6">
      <el-select
        v-model="selectedTextbookId"
        placeholder="选择 年级 / 学期"
        class="w-64"
        :loading="isLoading"
        @change="onTextbookChange"
      >
        <el-option
          v-for="tb in textbooks"
          :key="tb.id"
          :label="[tb.grade, tb.semester, tb.name].filter(Boolean).join(' ')"
          :value="tb.id"
        />
      </el-select>
      <el-select
        v-model="selectedTaskId"
        placeholder="选择 Unit（需已生成学习音频）"
        class="w-64"
        @change="onTaskChange"
      >
        <el-option
          v-for="t in availableTasks.filter((t) => t.textbook === selectedTextbookId)"
          :key="t.id"
          :label="`Unit ${t.unit}`"
          :value="t.id"
        />
      </el-select>
      <span v-if="selectedTaskId && ttsData" class="text-green-600 text-sm">✓ 学习音频已就绪</span>
    </div>

    <!-- 跟读区 -->
    <template v-if="ttsData">
      <el-card shadow="never" class="mb-4">
        <!-- 音频播放器 -->
        <div class="flex items-center gap-3">
          <el-button
            circle
            :icon="isPlaying ? undefined : undefined"
            @click="isPlaying ? audioRef?.pause() : audioRef?.play()"
          >
            {{ isPlaying ? '⏸' : '▶' }}
          </el-button>
          <audio
            ref="audioRef"
            :src="`/media/${ttsData.tts_audio_url}`"
            class="flex-1"
            controls
            @timeupdate="onTimeUpdate"
            @play="onPlay"
            @pause="onPause"
            @ended="onEnded"
            @loadedmetadata="onLoadedMetadata"
          />
          <span class="text-sm text-gray-400">
            {{ currentSentenceIndex >= 0 ? `第 ${currentSentenceIndex + 1} 句` : '—' }}
          </span>
        </div>
      </el-card>

      <el-card shadow="never">
        <el-tabs v-model="activeTab">
          <!-- 四模块：带时间戳跟读 -->
          <el-tab-pane v-for="m in AUDIO_MODULES" :key="m.key" :label="m.label" :name="m.key">
            <div class="max-h-[55vh] overflow-auto">
              <div
                v-for="(s, i) in currentSentences"
                :key="i"
                class="py-1.5 px-2 rounded cursor-pointer transition-colors"
                :class="i === currentSentenceIndex
                  ? 'bg-blue-100 border-l-4 border-blue-500'
                  : 'hover:bg-gray-50 border-l-4 border-transparent'"
                @click="playSentence(s)"
              >
                <span class="text-xs text-gray-400 mr-2">
                  {{ s.start != null ? s.start.toFixed(1) : '--' }}
                </span>
                {{ s.text }}
              </div>
              <el-empty v-if="currentSentences.length === 0" description="本模块暂无时间戳" :image-size="50" />
            </div>
          </el-tab-pane>

          <!-- 两个文本模块：无音频 -->
          <el-tab-pane v-for="m in TEXT_MODULES" :key="m.key" :label="m.label" :name="m.key">
            <div class="mb-2">
              <el-tag size="small" type="info">无音频（仅文本）</el-tag>
            </div>
            <div class="max-h-[55vh] overflow-auto">
              <ModuleView v-if="textModules[m.key]" :module="textModules[m.key]" />
              <el-empty v-else description="（本单元无此模块）" :image-size="50" />
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-card>

      <!-- 音频切片表：整个音频 1 个 chunk，句子为 slices（可编辑试听） -->
      <el-card shadow="never">
        <template #header>
          <div class="flex items-center justify-between flex-wrap gap-2">
            <div class="flex items-center gap-2">
              <span class="font-medium">音频切片表</span>
              <el-tag size="small" type="info">整个音频 1 个 chunk</el-tag>
              <span class="text-xs text-gray-400">{{ ttsData.tts_audio_url }}</span>
            </div>
            <div class="flex items-center gap-3">
              <span class="text-xs text-gray-400">总时长 {{ audioDuration.toFixed(1) }}s · {{ slices.length }} 个切片</span>
              <el-button size="small" type="primary" @click="saveSlices">保存切片</el-button>
            </div>
          </div>
        </template>
        <el-table :data="slices" size="small" max-height="420" @row-click="playSlice">
          <el-table-column prop="modLabel" label="模块" width="110" />
          <el-table-column prop="idx" label="#" width="48" />
          <el-table-column prop="text" label="句子" min-width="260" show-overflow-tooltip />
          <el-table-column label="开始 (s)" width="140">
            <template #default="{ row }">
              <el-input-number
                v-model="row.start"
                :step="0.01"
                :precision="2"
                :min="0"
                :max="audioDuration || undefined"
                size="small"
                controls-position="right"
                @click.stop
              />
            </template>
          </el-table-column>
          <el-table-column label="结束 (s)" width="140">
            <template #default="{ row }">
              <el-input-number
                v-model="row.end"
                :step="0.01"
                :precision="2"
                :min="0"
                :max="audioDuration || undefined"
                size="small"
                controls-position="right"
                @click.stop
              />
            </template>
          </el-table-column>
          <el-table-column label="时长 (s)" width="90">
            <template #default="{ row }">
              {{ row.start != null && row.end != null ? (row.end - row.start).toFixed(2) : '--' }}
            </template>
          </el-table-column>
          <el-table-column label="试听" width="66">
            <template #default="{ row }">
              <el-button size="small" circle @click.stop="playSlice(row)">▶</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </template>

    <el-empty v-else-if="!isLoading" description="请选择教材与单元（需任务完成校订并生成学习音频）">
      <el-button type="primary" @click="$router.push('/corpus/dashboard')">前往语料加工</el-button>
    </el-empty>
  </div>
</template>
