<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted } from 'vue'
import api from '@/api/axios'
import type { TableColumnCtx } from 'element-plus'

import {
  Edit,
  Delete,
} from '@element-plus/icons-vue'

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
const totalItems = ref(0)
const currentPage = ref(1)
const pageSize = ref(10) // 假设每页10条

const LG_BREAKPOINT = 1024; // Tailwind CSS 'lg' breakpoint
const isLargeScreen = ref(window.innerWidth >= LG_BREAKPOINT);

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
    const params: { tag?: string; search?: string; page?: number } = {}
    if (selectedTag.value && selectedTag.value.length > 0) {
      params.tag = selectedTag.value.join(',')
    }
    if (searchQuery.value) {
      params.search = searchQuery.value
    }
    params.page = currentPage.value

    const response = await api.get<PaginatedResponse<PhraseLog>>('/v1/history/', { params })
    phraseLogs.value = response.data.results
    totalItems.value = response.data.count
  } catch (error) {
    console.error('Failed to fetch phrase logs:', error)
  } finally {
    loading.value = false
  }
}

// --- 组件挂载与卸载 ---
const handleResize = () => {
  isLargeScreen.value = window.innerWidth >= LG_BREAKPOINT;
};

onMounted(() => {
  fetchTags()
  fetchPhraseLogs()
  window.addEventListener('resize', handleResize);
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
});

// --- 事件处理 ---
const handleSearch = () => {
  currentPage.value = 1 // 每次新搜索都回到第一页
  fetchPhraseLogs() // 重新加载数据以应用筛选
}

const handleReset = () => {
  currentPage.value = 1 // 重置时也回到第一页
  selectedTag.value = [] // 清空数组
  searchQuery.value = ''
  fetchPhraseLogs() // 重新加载数据
}

const handlePageChange = (newPage: number) => {
  currentPage.value = newPage
  fetchPhraseLogs()
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
  <div class="flex flex-col h-full">
    <!-- 面包屑 -->
    <el-breadcrumb separator="/">
      <el-breadcrumb-item v-for="item in breadcrumbItems" :key="item.path" :to="item.path">
        {{ item.name }}
      </el-breadcrumb-item>
    </el-breadcrumb>

  <!-- 筛选/搜索区域 -->
  <div class="w-full flex justify-between items-center gap-4 my-4 p-4 bg-white rounded-lg shadow-sm">
    <!-- 标签选择器 -->
    <el-select v-model="selectedTag" multiple :collapse-tags="!isLargeScreen" collapse-tags-tooltip placeholder="Select tags" clearable class="flex-grow">
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
    <div class="flex-grow overflow-y-auto bg-white rounded-lg shadow-sm p-4 pretty-scrollbar">
      <el-table :data="phraseLogs" v-loading="loading" style="width: 100%">
              <el-table-column prop="expression_text" label="Expression" min-width="80" show-overflow-tooltip />
              <el-table-column prop="chinese_meaning" label="Meaning" min-width="280" show-overflow-tooltip />
              <el-table-column prop="failed_radio" label="Failure Ratio" :formatter="formatRatio" sortable />
              <el-table-column prop="tested" label="Tested Count" sortable />
              <el-table-column label="Actions" width="100">
                <template #default="scope">
                  <el-button type="primary" :icon="Edit" circle @click="handleEdit(scope.row.id)" />
                  <el-button type="danger" :icon="Delete" circle @click="handleDelete(scope.row.id)" />
                </template>
              </el-table-column>
            </el-table>    </div>

    <!-- 分页控件 -->
    <div class="flex justify-center mt-4">
      <el-pagination
        background
        layout="total, prev, pager, next, jumper"
        :total="totalItems"
        v-model:current-page="currentPage"
        :page-size="pageSize"
        @current-change="handlePageChange"
      />
    </div>
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
</style>