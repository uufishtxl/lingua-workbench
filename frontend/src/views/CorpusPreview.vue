<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getCorpusTask, getCorpusTaskModules, type CorpusTask } from '@/api/corpusApi'
import ModuleView from '@/components/corpus/ModuleView.vue'

const route = useRoute()
const router = useRouter()

const taskId = Number(route.params.taskId)
const task = ref<CorpusTask | null>(null)
const modules = ref<Record<string, string | null>>({})
const activeTab = ref('topic_words')

const TABS = [
  { key: 'topic_words', label: 'Topic Words' },
  { key: 'fun_time', label: 'Fun Time' },
  { key: 'talking_time', label: 'Talking Time' },
  { key: 'story_time', label: 'Story Time' },
  { key: 'project', label: 'Project' },
  { key: 'words_to_use', label: 'Words to use' },
]

onMounted(async () => {
  try {
    const [t, m] = await Promise.all([getCorpusTask(taskId), getCorpusTaskModules(taskId)])
    task.value = t
    modules.value = m
  } catch {
    ElMessage.error('任务不存在或已被删除')
    router.push('/corpus/dashboard')
  }
})
</script>

<template>
  <div class="p-8 max-w-5xl mx-auto">
    <template v-if="task">
      <!-- 页头 -->
      <div class="mb-6">
        <h1 class="text-2xl font-bold">Stage 2：模块脏预览</h1>
        <p class="text-gray-500 mt-1">{{ task.name }}</p>
      </div>

      <el-alert
        type="info"
        :closable="false"
        show-icon
        class="mb-4"
        title="以下为机械粗分桶结果，可能包含噪声或错位内容，将在校准阶段由 AI 归整为精准模块。"
      />

      <el-card shadow="never">
        <el-tabs v-model="activeTab">
          <el-tab-pane v-for="tab in TABS" :key="tab.key" :label="tab.label" :name="tab.key">
            <div v-if="modules[tab.key]" class="max-h-[60vh] overflow-auto p-2">
              <ModuleView :module="modules[tab.key]" />
            </div>
            <el-empty v-else description="（本单元无此模块，或分桶未识别）" :image-size="60" />
          </el-tab-pane>
        </el-tabs>
      </el-card>

      <!-- 导航 -->
      <div class="flex justify-between mt-6">
        <el-button @click="router.push(`/corpus/overview/${task.id}`)">返回总览</el-button>
        <el-button type="primary" @click="router.push(`/corpus/calibrate/${task.id}`)">进入校准</el-button>
      </div>
    </template>
  </div>
</template>
