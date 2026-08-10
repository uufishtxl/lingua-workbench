<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  getCorpusTask,
  getCorpusTaskModules,
  triggerBucket,
  updateCorpusTask,
  completeCorpusTask,
  fixModule,
  applyModule,
  regenerateKp,
  applyKp,
  type CorpusTask,
} from '@/api/corpusApi'
import ModuleView from '@/components/corpus/ModuleView.vue'

const route = useRoute()
const router = useRouter()

const taskId = Number(route.params.taskId)
const task = ref<CorpusTask | null>(null)
const modules = ref<Record<string, string | null>>({})
const activeModule = ref('topic_words')
const activeKp = ref('vocabulary')
const kpValues = ref<Record<string, string>>({})
const isSaving = ref(false)
let pollTimer: ReturnType<typeof setInterval> | null = null

const MODULE_TABS = [
  { key: 'topic_words', label: 'Topic Words' },
  { key: 'fun_time', label: 'Fun Time' },
  { key: 'talking_time', label: 'Talking Time' },
  { key: 'story_time', label: 'Story Time' },
  { key: 'project', label: 'Project' },
  { key: 'words_to_use', label: 'Words to use' },
]

const KP_TABS = [
  { key: 'vocabulary', label: '词汇' },
  { key: 'phrases', label: '短语' },
  { key: 'sentence_patterns', label: '句型' },
  { key: 'grammar', label: '语法' },
  { key: 'phonics', label: '拼读' },
  { key: 'summary', label: '梗概' },
  { key: 'big_task', label: 'Big Task 范文' },
]

// --- AI 修复 / 重新生成（S7）：指令 + diff 确认 ---
const moduleInstruction = ref<Record<string, string>>({})
const kpInstruction = ref<Record<string, string>>({})
const isFixing = ref(false)
const diffDialog = ref(false)
const diffData = ref<{ type: 'module' | 'kp'; key: string; oldText: string; newText: string } | null>(null)

const fmtContent = (c: unknown): string =>
  typeof c === 'string' ? c : JSON.stringify(c ?? null, null, 2)

const handleFixModule = async (moduleKey: string) => {
  isFixing.value = true
  try {
    const res = await fixModule(taskId, {
      module_key: moduleKey,
      instruction: moduleInstruction.value[moduleKey],
    })
    diffData.value = {
      type: 'module',
      key: moduleKey,
      oldText: fmtContent(res.old_content),
      newText: fmtContent(res.new_content),
    }
    diffDialog.value = true
  } catch (e: any) {
    ElMessage.error(`AI 修复失败: ${e?.response?.data?.error ?? e?.message ?? e}`)
  } finally {
    isFixing.value = false
  }
}

const handleRegenerateKp = async (kpKey: string) => {
  isFixing.value = true
  try {
    const res = await regenerateKp(taskId, {
      kp_key: kpKey,
      instruction: kpInstruction.value[kpKey],
    })
    diffData.value = {
      type: 'kp',
      key: kpKey,
      oldText: res.old_content,
      newText: res.new_content,
    }
    diffDialog.value = true
  } catch (e: any) {
    ElMessage.error(`AI 重新生成失败: ${e?.response?.data?.error ?? e?.message ?? e}`)
  } finally {
    isFixing.value = false
  }
}

const confirmDiff = async () => {
  if (!diffData.value) return
  const { type, key, newText } = diffData.value
  try {
    if (type === 'module') {
      const t = await applyModule(taskId, { module_key: key, content: JSON.parse(newText) })
      task.value = t
      modules.value = await getCorpusTaskModules(taskId)
    } else {
      const t = await applyKp(taskId, { kp_key: key, content: newText })
      task.value = t
      kpValues.value = { ...(t.knowledge_points ?? {}) }
    }
    diffDialog.value = false
    ElMessage.success('已应用（原内容未被覆盖，raw 数据不变）')
  } catch (e: any) {
    ElMessage.error(`应用失败: ${e?.response?.data?.error ?? e?.message ?? e}`)
  }
}

const discardDiff = () => {
  diffDialog.value = false
}

// --- 归整 / 轮询 ---
const isBucketing = () =>
  !!task.value && (task.value.bucket_status === 'pending' || task.value.bucket_status === 'running')
const isGeneratingKp = () =>
  !!task.value && (task.value.kp_status === 'pending' || task.value.kp_status === 'running')

const refresh = async () => {
  if (!task.value) return
  try {
    const [t, m] = await Promise.all([getCorpusTask(taskId), getCorpusTaskModules(taskId)])
    const prevBucket = task.value.bucket_status
    const prevKp = task.value.kp_status
    task.value = t
    modules.value = m
    if (t.knowledge_points && prevKp !== 'done' && t.kp_status === 'done') {
      kpValues.value = { ...t.knowledge_points }
      ElMessage.success('AI 已预填 7 大知识点，可编辑后保存')
    }
    if (prevBucket && prevBucket !== t.bucket_status && t.bucket_status === 'done') {
      ElMessage.success('AI 归整完成，左栏已更新为精准模块')
    }
    if (t.bucket_status === 'error') {
      ElMessage.error(`AI 归整失败：${t.bucket_error || '未知错误'}`)
    }
  } catch (e: any) {
    ElMessage.error(`加载失败: ${e?.message ?? e}`)
  }
}

const startBucket = async () => {
  try {
    const t = await triggerBucket(taskId)
    task.value = t
    ElMessage.info('已触发 AI 归整，完成后自动预填知识点')
    ensurePolling()
  } catch (e: any) {
    ElMessage.error(`触发归整失败: ${e?.response?.data?.detail ?? e?.message ?? e}`)
  }
}

const ensurePolling = () => {
  if (pollTimer) return
  pollTimer = setInterval(async () => {
    await refresh()
    if (task.value && !isBucketing() && !isGeneratingKp()) stopPolling()
  }, 5000)
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

// --- 保存 / 完成校订（#28）---
const handleSave = async () => {
  if (!task.value) return
  isSaving.value = true
  try {
    const t = await updateCorpusTask(taskId, { knowledge_points: kpValues.value })
    task.value = t
    ElMessage.success('已保存（导出已解锁）')
  } catch (e: any) {
    ElMessage.error(`保存失败: ${e?.response?.data?.detail ?? e?.message ?? e}`)
  } finally {
    isSaving.value = false
  }
}

const handleComplete = async () => {
  if (!task.value) return
  try {
    const t = await completeCorpusTask(taskId)
    task.value = t
    ElMessage.success('已完成校订')
  } catch (e: any) {
    ElMessage.error(`完成校订失败: ${e?.response?.data?.detail ?? e?.message ?? e}`)
  }
}

onMounted(async () => {
  try {
    task.value = await getCorpusTask(taskId)
    modules.value = await getCorpusTaskModules(taskId)
    if (task.value.knowledge_points) {
      kpValues.value = { ...task.value.knowledge_points }
    }
    if (task.value.bucket_status === 'running') {
      ensurePolling()
    } else if (task.value.bucket_status === 'pending') {
      await startBucket()
    }
  } catch {
    ElMessage.error('任务不存在或已被删除')
    router.push('/corpus/dashboard')
  }
})
onUnmounted(stopPolling)
</script>

<template>
  <div class="p-8 max-w-7xl mx-auto">
    <template v-if="task">
      <!-- 页头 -->
      <div class="mb-6">
        <h1 class="text-2xl font-bold">Stage 3：知识点校准</h1>
        <p class="text-gray-500 mt-1">
          {{ task.name }}
          <el-tag size="small" class="ml-2"
            :type="task.bucket_status === 'done' ? 'success' : task.bucket_status === 'error' ? 'danger' : 'warning'">
            AI 归整：{{ task.bucket_status }}
          </el-tag>
          <el-tag size="small" class="ml-1"
            :type="task.kp_status === 'done' ? 'success' : task.kp_status === 'error' ? 'danger' : 'warning'">
            知识点预填：{{ task.kp_status }}
          </el-tag>
          <el-tag size="small" class="ml-1"
            :type="task.status === 'completed' ? 'success' : task.status === 'proofreading' ? 'primary' : 'info'">
            状态：{{ task.status }}
          </el-tag>
          <el-tag size="small" class="ml-1"
            :type="task.tts_status === 'done' ? 'success' : task.tts_status === 'error' ? 'danger' : 'warning'">
            学习音频：{{ task.tts_status }}
          </el-tag>
        </p>
      </div>

      <!-- 双栏 -->
      <div class="flex gap-6 items-start">
        <!-- 左栏：教材原文（只读 + AI 修复） -->
        <div class="w-[45%]">
          <el-card shadow="never">
            <template #header>
              <div class="flex items-center justify-between">
                <span class="font-semibold">原文（只读）</span>
                <el-button size="small" type="primary" plain :loading="isBucketing()" @click="startBucket">
                  重新归整
                </el-button>
              </div>
            </template>
            <el-tabs v-model="activeModule" tab-position="left" class="module-tabs">
              <el-tab-pane v-for="tab in MODULE_TABS" :key="tab.key" :label="tab.label" :name="tab.key">
                <div class="max-h-[52vh] overflow-auto p-1">
                  <ModuleView v-if="modules[tab.key]" :module="modules[tab.key]" />
                  <el-empty v-else description="（本单元无此模块）" :image-size="50" />
                </div>
                <!-- AI 修复：指令 + 按钮 -->
                <div class="flex items-center gap-2 mt-2 border-t pt-2 border-gray-100">
                  <el-input
                    v-model="moduleInstruction[tab.key]"
                    size="small"
                    placeholder="修复指令（可留空 = 按规则重归整）"
                    clearable
                  />
                  <el-button size="small" type="primary" :loading="isFixing" @click="handleFixModule(tab.key)">
                    AI 修复
                  </el-button>
                </div>
              </el-tab-pane>
            </el-tabs>
          </el-card>
        </div>

        <!-- 右栏：7 大知识点（垂直手风琴 + AI 重新生成） -->
        <div class="w-[55%]">
          <el-card shadow="never">
            <template #header>
              <div class="flex items-center justify-between">
                <span class="font-semibold">知识点（AI 预填 + 人工编辑）</span>
                <span class="text-xs text-gray-400">{{ task.kp_progress }}/7 板块已填写</span>
              </div>
            </template>
            <el-collapse v-model="activeKp" accordion>
              <el-collapse-item v-for="kp in KP_TABS" :key="kp.key" :name="kp.key">
                <template #title>
                  <span class="font-medium">{{ kp.label }}</span>
                </template>
                <div class="flex items-center gap-2 mb-2">
                  <el-input
                    v-model="kpInstruction[kp.key]"
                    size="small"
                    placeholder="重新生成指令（可留空）"
                    clearable
                  />
                  <el-button size="small" type="primary" :loading="isFixing" @click="handleRegenerateKp(kp.key)">
                    AI 重新生成
                  </el-button>
                </div>
                <el-input
                  v-model="kpValues[kp.key]"
                  type="textarea"
                  :rows="8"
                  :placeholder="`${kp.label}（AI 预填或手动输入）`"
                />
              </el-collapse-item>
            </el-collapse>
          </el-card>
        </div>
      </div>

      <!-- 底部操作 -->
      <div class="flex justify-between mt-6">
        <el-button @click="router.push(`/corpus/preview/${task.id}`)">返回脏预览</el-button>
        <div class="flex gap-3">
          <el-button type="primary" :loading="isSaving" @click="handleSave">保存</el-button>
          <el-button type="success" @click="handleComplete">完成校订</el-button>
        </div>
      </div>
    </template>

    <!-- AI 修复 diff 确认弹窗 -->
    <el-dialog v-model="diffDialog" title="AI 修复结果确认" width="70%">
      <div v-if="diffData" class="grid grid-cols-2 gap-4">
        <div>
          <div class="text-sm font-semibold text-gray-500 mb-1">原内容</div>
          <pre class="text-xs bg-gray-50 border border-gray-200 rounded p-3 max-h-[50vh] overflow-auto whitespace-pre-wrap">{{ diffData.oldText }}</pre>
        </div>
        <div>
          <div class="text-sm font-semibold text-green-600 mb-1">新内容（AI 生成）</div>
          <pre class="text-xs bg-green-50 border border-green-200 rounded p-3 max-h-[50vh] overflow-auto whitespace-pre-wrap">{{ diffData.newText }}</pre>
        </div>
      </div>
      <template #footer>
        <el-button @click="discardDiff">丢弃</el-button>
        <el-button type="primary" @click="confirmDiff">应用</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.module-tabs :deep(.el-tabs__item) {
  font-size: 13px;
  padding: 0 12px;
}
</style>
