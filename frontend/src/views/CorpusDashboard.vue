<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  listCorpusTasks,
  getCorpusTaskStats,
  deleteCorpusTask,
  type CorpusTask,
  type CorpusTaskStats,
} from '@/api/corpusApi'

const router = useRouter()

const stats = ref<CorpusTaskStats>({ total: 0, completed: 0, in_progress: 0, units_covered: 0 })
const tasks = ref<CorpusTask[]>([])
const isLoading = ref(false)

const STATUS_META: Record<CorpusTask['status'], { label: string; type: 'info' | 'primary' | 'success' }> = {
  draft: { label: '草稿', type: 'info' },
  proofreading: { label: '校订中', type: 'primary' },
  completed: { label: '已完成', type: 'success' },
}

const loadAll = async () => {
  isLoading.value = true
  try {
    const [s, t] = await Promise.all([getCorpusTaskStats(), listCorpusTasks()])
    stats.value = s
    tasks.value = t
  } catch (e: any) {
    ElMessage.error(`加载失败: ${e?.message ?? e}`)
  } finally {
    isLoading.value = false
  }
}

// --- 操作按钮 ---
const stageRoute = (task: CorpusTask): string => {
  switch (task.stage) {
    case 2: return `/corpus/preview/${task.id}`
    case 3: return `/corpus/calibrate/${task.id}`
    default: return `/corpus/overview/${task.id}`  // stage 0/1 都去总览
  }
}

const handleContinue = (task: CorpusTask) => {
  router.push(stageRoute(task))
}

const handleEdit = (task: CorpusTask) => {
  router.push(`/corpus/calibrate/${task.id}`)
}

const handleExport = (task: CorpusTask) => {
  ElMessage.info(`导出功能将在下一迭代（S8）开放：${task.name}`)
}

const handleDelete = async (task: CorpusTask) => {
  try {
    await ElMessageBox.confirm(`确定删除任务「${task.name}」？关联的媒体产物将一并清理。`, '删除确认', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  try {
    await deleteCorpusTask(task.id)
    ElMessage.success(`已删除「${task.name}」`)
    await loadAll()
  } catch (e: any) {
    ElMessage.error(`删除失败: ${e?.message ?? e}`)
  }
}

onMounted(loadAll)
</script>

<template>
  <div class="p-8 max-w-6xl mx-auto">
    <!-- 页头 + 快速开始 -->
    <div class="mb-6 flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold">任务仪表盘</h1>
        <p class="text-gray-500 mt-1">Manage your linguistic extraction tasks and results.</p>
      </div>
      <el-button type="primary" size="large" @click="router.push('/corpus/extract')">
        新建任务
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-4 gap-4 mb-6">
      <el-card shadow="hover" class="text-center">
        <div class="text-3xl font-bold text-gray-700">{{ stats.total }}</div>
        <div class="text-gray-500 mt-1">总任务数</div>
      </el-card>
      <el-card shadow="hover" class="text-center">
        <div class="text-3xl font-bold text-green-600">{{ stats.completed }}</div>
        <div class="text-gray-500 mt-1">已完成</div>
      </el-card>
      <el-card shadow="hover" class="text-center">
        <div class="text-3xl font-bold text-blue-600">{{ stats.in_progress }}</div>
        <div class="text-gray-500 mt-1">进行中</div>
      </el-card>
      <el-card shadow="hover" class="text-center">
        <div class="text-3xl font-bold text-amber-600">{{ stats.units_covered }}</div>
        <div class="text-gray-500 mt-1">覆盖单元数</div>
      </el-card>
    </div>

    <!-- 任务表 -->
    <el-card shadow="never">
      <template #header>
        <span class="font-semibold">语料任务</span>
      </template>
      <el-table :data="tasks" v-loading="isLoading" empty-text="暂无任务，点击右上角「新建任务」开始">
        <el-table-column prop="name" label="任务名称" min-width="200" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="STATUS_META[row.status as CorpusTask['status']]?.type ?? 'info'" size="small">
              {{ STATUS_META[row.status as CorpusTask['status']]?.label ?? row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="模块进度" width="100">
          <template #default="{ row }">{{ row.module_count }}/6</template>
        </el-table-column>
        <el-table-column label="知识点进度" width="110">
          <template #default="{ row }">
            <span>{{ row.kp_progress ?? 0 }}/7</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button size="small" link type="primary" @click="handleContinue(row)">继续</el-button>
            <el-button size="small" link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button
              v-if="row.status !== 'draft'"
              size="small"
              link
              type="success"
              @click="handleExport(row)"
            >导出</el-button>
            <el-button size="small" link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>
