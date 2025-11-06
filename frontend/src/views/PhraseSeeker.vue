<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import api from '@/api/axios'
import type { TableColumnCtx } from 'element-plus'

// --- 数据类型定义 ---
interface PhraseLog {
  id: number;
  expression_text: string;
  chinese_meaning: string;
  tested: number;
  failed: number;
  failed_radio: number;
  created_at: string;
  remark: string;
}

interface Tag {
  id: number;
  name: string;
}

interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// --- 响应式状态 ---
const tags = ref<Tag[]>([])
const selectedTag = ref<number[]>([]) // 存储选中的标签ID数组
const searchQuery = ref('')
const phraseLogs = ref<PhraseLog[]>([])
const loading = ref(true)

// --- API 调用 ---
const fetchTags = async () => {
  try {
    const response = await api.get<Tag[]>('/v1/tags/')
    tags.value = response.data
  } catch (error) {
    console.error('Failed to fetch tags:', error)
  }
}

const fetchPhraseLogs = async () => {
  loading.value = true
  try {
    // 构建查询参数
    const params: { tag?: string; search?: string } = {}
    if (selectedTag.value && selectedTag.value.length > 0) {
      // 将 ID 数组转换为逗号分隔的字符串
      params.tag = selectedTag.value.join(',')
    }
    if (searchQuery.value) {
      params.search = searchQuery.value
    }

    const response = await api.get<PaginatedResponse<PhraseLog>>('/v1/history/', { params })
    phraseLogs.value = response.data.results
  } catch (error) {
    console.error('Failed to fetch phrase logs:', error)
  } finally {
    loading.value = false
  }
}

// --- 组件挂载 ---
onMounted(() => {
  fetchTags()
  fetchPhraseLogs()
})

// --- 事件处理 ---
const handleSearch = () => {
  console.log('Searching with:', {
    tag: selectedTag.value,
    query: searchQuery.value
  })
  fetchPhraseLogs() // 重新加载数据以应用筛选
}

const handleReset = () => {
  selectedTag.value = [] // 清空数组
  searchQuery.value = ''
  console.log('Filters reset')
  fetchPhraseLogs() // 重新加载数据
}

const handleEdit = (id: number) => {
  console.log('Edit item with ID:', id)
  // 这里可以添加跳转到编辑页面的逻辑
}

const handleDelete = (id: number) => {
  console.log('Delete item with ID:', id)
  // 这里可以添加删除逻辑，例如弹窗确认后调用 API 删除
}

// --- 表格格式化函数 ---
const formatRatio = (row: PhraseLog, column: TableColumnCtx<PhraseLog>) => {
  return `${row.failed_radio} %`
}

const formatDate = (row: PhraseLog, column: TableColumnCtx<PhraseLog>) => {
  return new Date(row.created_at).toLocaleDateString()
}

// --- 计算属性用于面包屑 ---
const breadcrumbItems = computed(() => [
  { path: '/', name: 'Home' },
  { path: '/phrase-seeker', name: 'PhraseSeeker' }
]);
</script>

<template>
  <!-- 面包屑 -->
  <el-breadcrumb separator="/">
    <el-breadcrumb-item v-for="item in breadcrumbItems" :key="item.path" :to="item.path">
      {{ item.name }}
    </el-breadcrumb-item>
  </el-breadcrumb>

  <!-- 筛选/搜索区域 -->
  <div class="flex items-center gap-4 my-4 p-4 bg-white rounded-lg shadow-sm">
    <!-- 标签选择器 -->
    <el-select v-model="selectedTag" multiple collapse-tags collapse-tags-tooltip placeholder="Select tags" clearable style="width: 200px;">
      <el-option v-for="tag in tags" :key="tag.id" :label="tag.name" :value="tag.id" />
    </el-select>

    <!-- 搜索框 -->
    <el-input v-model="searchQuery" placeholder="Search expressions..." clearable style="width: 300px;" @keyup.enter="handleSearch" />

    <!-- 按钮 -->
    <div class="flex items-center">
      <el-button type="primary" @click="handleSearch">Search</el-button>
      <el-button @click="handleReset">Reset</el-button>
    </div>
  </div>

  <!-- 历史记录表格 -->
  <div class="mt-4 p-4 bg-white rounded-lg shadow-sm">
    <el-table :data="phraseLogs" v-loading="loading" style="width: 100%">
      <el-table-column prop="expression_text" label="Expression" width="200" />
      <el-table-column prop="chinese_meaning" label="Meaning" width="200" />
      <el-table-column prop="failed_radio" label="Failure Ratio" :formatter="formatRatio" sortable />
      <el-table-column prop="tested" label="Tested Count" sortable />
      <el-table-column prop="created_at" label="Date Added" :formatter="formatDate" sortable />
      <el-table-column label="Actions" width="150">
        <template #default="scope">
          <el-button size="small" @click="handleEdit(scope.row.id)">Edit</el-button>
          <el-button size="small" type="danger" @click="handleDelete(scope.row.id)">Delete</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<style scoped>
/* 你可以在这里添加自定义样式 */
</style>