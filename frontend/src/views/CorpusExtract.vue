<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type UploadRequestOptions } from 'element-plus'
import {
  listTextbooks,
  uploadTextbook,
  createCorpusTask,
  getCorpusTask,
  listCorpusTasks,
  type Textbook,
  type CorpusTask,
  type TaskRunStatus,
} from '@/api/corpusApi'

const router = useRouter()

// --- 教材列表 ---
const textbooks = ref<Textbook[]>([])
const selectedTextbookId = ref<number | null>(null)
const isLoading = ref(false)

const fetchTextbooks = async () => {
  isLoading.value = true
  try {
    const list = await listTextbooks()
    textbooks.value = list
    const first = list.find(() => true)
    if (!selectedTextbookId.value && first) {
      selectedTextbookId.value = first.id
    }
  } catch (e: any) {
    ElMessage.error(`加载教材列表失败: ${e?.message ?? e}`)
  } finally {
    isLoading.value = false
  }
}

// --- 上传新教材 ---
const uploadName = ref('')
const uploadGrade = ref('')
const uploadSemester = ref('')
const showUpload = ref(false)

const handleUpload = async (options: UploadRequestOptions) => {
  const formData = new FormData()
  formData.append('pdf_file', options.file)
  if (uploadName.value.trim()) formData.append('name', uploadName.value.trim())
  if (uploadGrade.value.trim()) formData.append('grade', uploadGrade.value.trim())
  if (uploadSemester.value.trim()) formData.append('semester', uploadSemester.value.trim())

  try {
    const created = await uploadTextbook(formData)
    ElMessage.success(`教材「${created.name}」上传成功`)
    textbooks.value.unshift(created)
    selectedTextbookId.value = created.id
    showUpload.value = false
    uploadName.value = ''
    uploadGrade.value = ''
    uploadSemester.value = ''
    options.onSuccess(created)
  } catch (e: any) {
    ElMessage.error(`上传失败: ${e?.response?.data?.detail ?? e?.message ?? e}`)
    options.onError(e)
  }
}

// --- Unit 提取（S2）---
const unitInput = ref<number | null>(null)
const isStarting = ref(false)

// 提取队列：本会话新建 + 历史任务
const tasks = ref<CorpusTask[]>([])
let pollTimer: ReturnType<typeof setInterval> | null = null

const STATUS_META: Record<TaskRunStatus, { label: string; type: 'info' | 'warning' | 'success' | 'danger' }> = {
  pending: { label: '排队中', type: 'info' },
  running: { label: '执行中', type: 'warning' },
  done: { label: '已完成', type: 'success' },
  error: { label: '失败', type: 'danger' },
}

const hasActiveTask = () => tasks.value.some((t) => t.extract_status === 'pending' || t.extract_status === 'running')

const startExtraction = async () => {
  if (!selectedTextbookId.value) {
    ElMessage.warning('请先选择教材')
    return
  }
  if (!unitInput.value || unitInput.value < 1) {
    ElMessage.warning('请填写单元号 Unit')
    return
  }
  isStarting.value = true
  try {
    const task = await createCorpusTask({ textbook: selectedTextbookId.value, unit: unitInput.value })
    tasks.value.unshift(task)
    ElMessage.success(`任务「${task.name}」已创建，开始提取`)
    ensurePolling()
  } catch (e: any) {
    ElMessage.error(`创建任务失败: ${e?.response?.data?.detail ?? e?.message ?? e}`)
  } finally {
    isStarting.value = false
  }
}

const refreshTask = async (id: number) => {
  try {
    const updated = await getCorpusTask(id)
    const idx = tasks.value.findIndex((t) => t.id === id)
    if (idx !== -1) tasks.value[idx] = updated
    return updated
  } catch {
    return null
  }
}

const pollOnce = async () => {
  const active = tasks.value.filter((t) => t.extract_status === 'pending' || t.extract_status === 'running')
  if (active.length === 0) {
    stopPolling()
    return
  }
  const results = await Promise.all(active.map((t) => refreshTask(t.id)))
  // 完成/失败时提示
  results.forEach((r) => {
    if (!r) return
    const prev = tasks.value.find((t) => t.id === r.id)
    if (prev && prev.extract_status !== r.extract_status && (r.extract_status === 'done' || r.extract_status === 'error')) {
      if (r.extract_status === 'done') {
        ElMessage.success(`「${r.name}」提取完成，进入 Stage 1 总览`)
      } else {
        ElMessage.error(`「${r.name}」提取失败：${r.extract_error || '未知错误'}`)
      }
    }
  })
  if (!hasActiveTask()) stopPolling()
}

const ensurePolling = () => {
  if (pollTimer) return
  pollTimer = setInterval(pollOnce, 5000)
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

const loadTasks = async () => {
  try {
    tasks.value = await listCorpusTasks()
    if (hasActiveTask()) ensurePolling()
  } catch (e: any) {
    ElMessage.error(`加载任务列表失败: ${e?.message ?? e}`)
  }
}

onMounted(() => {
  fetchTextbooks()
  loadTasks()
})
onUnmounted(stopPolling)
</script>

<template>
  <div class="p-8 max-w-5xl mx-auto">
    <!-- 页头：标记当前 Unit -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold">Stage 0：原始语料提取</h1>
      <p class="text-gray-500 mt-1">
        选择教材并指定单元，提取分模块结构化语料
        <span v-if="unitInput" class="ml-2 text-blue-600 font-medium">当前 Unit：{{ unitInput }}</span>
      </p>
    </div>

    <!-- 教材选择 -->
    <el-card shadow="never" class="mb-6">
      <template #header>
        <div class="flex items-center justify-between">
          <span class="font-semibold">教材选择</span>
          <el-button size="small" type="primary" plain @click="showUpload = !showUpload">
            {{ showUpload ? '收起' : '上传新教材' }}
          </el-button>
        </div>
      </template>

      <el-select v-model="selectedTextbookId" placeholder="选择教材" class="w-full" :loading="isLoading">
        <el-option
          v-for="tb in textbooks"
          :key="tb.id"
          :label="[tb.grade, tb.semester, tb.name].filter(Boolean).join(' ')"
          :value="tb.id"
        />
      </el-select>

      <!-- 上传表单 -->
      <div v-if="showUpload" class="mt-4 border-t pt-4 border-gray-100">
        <el-upload drag :show-file-list="false" :http-request="handleUpload" accept=".pdf">
          <div class="el-upload__text">拖拽 PDF 到此处或 <em>点击上传</em></div>
          <template #tip>
            <div class="el-upload__tip">仅支持 PDF，最大 100MB；教材解析缓存会在首次提取时生成</div>
          </template>
        </el-upload>
        <div class="grid grid-cols-3 gap-3 mt-4">
          <el-input v-model="uploadName" placeholder="教材名（可选，缺省用文件名）" />
          <el-input v-model="uploadGrade" placeholder="年级（可选，如 五年级）" />
          <el-input v-model="uploadSemester" placeholder="学期（可选，如 上册）" />
        </div>
      </div>
    </el-card>

    <!-- Unit 设置 + 开始提取 -->
    <el-card shadow="never" class="mb-6">
      <template #header>
        <span class="font-semibold">提取设置</span>
      </template>
      <div class="flex items-center gap-4">
        <span class="text-gray-600 whitespace-nowrap">单元号 Unit</span>
        <el-input-number v-model="unitInput" :min="1" :max="20" placeholder="如 2" class="w-40" />
        <el-button type="primary" :loading="isStarting" @click="startExtraction">开始提取</el-button>
      </div>
    </el-card>

    <!-- 提取队列 -->
    <el-card shadow="never">
      <template #header>
        <span class="font-semibold">提取队列</span>
      </template>
      <el-table :data="tasks" empty-text="暂无任务，请选择教材并开始提取">
        <el-table-column prop="name" label="任务名称" min-width="200" />
        <el-table-column prop="unit" label="Unit" width="80" />
        <el-table-column label="提取状态" width="110">
          <template #default="{ row }">
            <el-tag :type="STATUS_META[row.extract_status as TaskRunStatus]?.type ?? 'info'" size="small">
              {{ STATUS_META[row.extract_status as TaskRunStatus]?.label ?? row.extract_status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="错误信息" min-width="200">
          <template #default="{ row }">
            <span v-if="row.extract_status === 'error'" class="text-red-500 text-sm">{{ row.extract_error }}</span>
            <el-button
              v-else-if="row.extract_status === 'done'"
              size="small"
              link
              type="primary"
              @click="router.push(`/corpus/overview/${row.id}`)"
            >查看 Stage 1 总览</el-button>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
      </el-table>
    </el-card>
  </div>
</template>
