<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getCorpusTask, type CorpusTask } from '@/api/corpusApi'

const route = useRoute()
const router = useRouter()

const taskId = Number(route.params.taskId)
const task = ref<CorpusTask | null>(null)
const notFound = ref(false)

const MODULE_LABELS: Record<string, string> = {
  topic_words: 'Topic Words',
  fun_time: 'Fun Time',
  talking_time: 'Talking Time',
  story_time: 'Story Time',
  project: 'Project',
  words_to_use: 'Words to use',
}

onMounted(async () => {
  try {
    task.value = await getCorpusTask(taskId)
  } catch {
    notFound.value = true
    ElMessage.error('任务不存在或已被删除')
  }
})
</script>

<template>
  <div class="p-8 max-w-5xl mx-auto">
    <template v-if="notFound">
      <el-empty description="任务不存在">
        <el-button type="primary" @click="router.push('/corpus/dashboard')">返回仪表盘</el-button>
      </el-empty>
    </template>

    <template v-else-if="task">
      <!-- 页头 -->
      <div class="mb-6">
        <h1 class="text-2xl font-bold">Stage 1：提取总览</h1>
        <p class="text-gray-500 mt-1">{{ task.name }}</p>
      </div>

      <!-- 统计卡片 -->
      <div class="grid grid-cols-4 gap-4 mb-6">
        <el-card shadow="hover" class="text-center">
          <div class="text-3xl font-bold text-gray-700">{{ task.total_chars.toLocaleString() }}</div>
          <div class="text-gray-500 mt-1">Total Characters</div>
        </el-card>
        <el-card shadow="hover" class="text-center">
          <div class="text-3xl font-bold text-gray-700">
            {{ task.page_start ?? '-' }} - {{ task.page_end ?? '-' }}
          </div>
          <div class="text-gray-500 mt-1">Page Coverage</div>
        </el-card>
        <el-card shadow="hover" class="text-center">
          <div class="text-3xl font-bold text-blue-600">{{ task.module_count }}/6</div>
          <div class="text-gray-500 mt-1">Modules Identified</div>
        </el-card>
        <el-card shadow="hover" class="text-center">
          <div class="text-3xl font-bold text-amber-600">{{ task.words_count }}</div>
          <div class="text-gray-500 mt-1">Words to Use</div>
        </el-card>
      </div>

      <!-- 模块识别结果 -->
      <el-card shadow="never" class="mb-6">
        <template #header>
          <span class="font-semibold">模块识别</span>
        </template>
        <div class="flex flex-wrap gap-2">
          <el-tag
            v-for="(label, key) in MODULE_LABELS"
            :key="key"
            :type="task.modules_present.includes(key) ? 'success' : 'info'"
            size="large"
            effect="plain"
          >
            {{ label }}
            <span v-if="!task.modules_present.includes(key)" class="ml-1 text-xs">
              缺失
            </span>
          </el-tag>
        </div>
        <p class="text-gray-400 text-sm mt-3">模块为机械粗分桶结果，将在校准阶段由 AI 归整</p>
      </el-card>

      <!-- 导航 -->
      <div class="flex justify-between">
        <el-button @click="router.push('/corpus/dashboard')">返回仪表盘</el-button>
        <div class="flex gap-3">
          <el-button @click="router.push(`/corpus/preview/${task.id}`)">查看脏预览</el-button>
          <el-button type="primary" @click="router.push(`/corpus/calibrate/${task.id}`)">进入校准</el-button>
        </div>
      </div>
    </template>
  </div>
</template>
