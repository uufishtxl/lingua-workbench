<template>
  <!-- Main Container - matches ReviewBoard -->
  <div class="h-full w-full flex flex-col p-4 bg-slate-50">
    
    <!-- Header -->
    <header class="flex justify-between items-center mb-4 shrink-0 px-4">
      <div>
        <h1 class="text-xl font-bold text-blue-600 tracking-tight">Translation Manager</h1>
        <p class="text-zinc-500 text-sm">Batch translate idioms using DeepSeek</p>
      </div>
      <button 
        @click="$router.push('/')" 
        class="w-10 h-10 rounded-full bg-white shadow-md flex items-center justify-center text-zinc-400 hover:text-zinc-600 hover:shadow-lg transition-all"
      >
        <i class="i-mdi-close text-xl"></i>
      </button>
    </header>

    <!-- Controls Card -->
    <div class="bg-white rounded-2xl shadow-lg p-6 mb-4 mx-4 flex justify-between items-center">
      <div class="flex items-center gap-4">
        <div class="w-16 h-16 rounded-2xl bg-blue-50 flex items-center justify-center">
          <span class="text-3xl font-bold text-blue-600">{{ tasks.length }}</span>
        </div>
        <div class="text-zinc-500 text-sm font-medium">
          Items missing translation
        </div>
      </div>

      <button 
        @click="startBatchTranslation"
        :disabled="loading || tasks.length === 0"
        class="px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white font-semibold rounded-full shadow-lg transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105 active:scale-95"
      >
        <i v-if="loading" class="i-mdi-loading animate-spin text-lg"></i>
        <i v-else class="i-mdi-translate text-lg"></i>
        {{ loading ? 'Translating...' : 'Translate All' }}
      </button>
    </div>

    <!-- Data Table Card -->
    <div class="flex-1 bg-white rounded-2xl shadow-lg mx-4 mb-4 overflow-hidden flex flex-col">
      <table class="w-full text-left">
        <thead class="bg-slate-50 border-b border-zinc-200">
          <tr>
            <th class="px-6 py-4 text-xs font-semibold text-zinc-500 uppercase tracking-wider">Original Text</th>
            <th class="px-6 py-4 text-xs font-semibold text-zinc-500 uppercase tracking-wider text-right">Status</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-zinc-100">
          <tr v-if="tasks.length === 0 && !loading">
            <td colspan="2" class="px-6 py-16 text-center">
              <div class="text-4xl mb-4">✨</div>
              <p class="text-zinc-500 font-medium">No missing translations found.</p>
              <p class="text-zinc-400 text-sm mt-1">You are all set!</p>
            </td>
          </tr>
          <tr 
            v-for="task in tasks" 
            :key="task.id" 
            class="hover:bg-slate-50 transition-colors"
          >
            <td class="px-6 py-4 text-zinc-700 text-lg font-serif">
              {{ task.original_text }}
            </td>
            <td class="px-6 py-4 text-right">
              <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-600 border border-amber-200">
                Pending
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { translationApi, type TranslationTask } from '@/api/translationApi'

const tasks = ref<TranslationTask[]>([])
const loading = ref(false)

const fetchTasks = async () => {
    try {
        const res = await translationApi.getMissingTranslations()
        tasks.value = res.data
    } catch (e) {
        console.error("Failed to fetch tasks", e)
    }
}

const startBatchTranslation = async () => {
    if (tasks.value.length === 0) return
    
    loading.value = true
    const ids = tasks.value.map(t => t.id)
    
    try {
        const res = await translationApi.batchTranslate(ids)
        // Verify changes and refresh list
        // Or simply clear list if successful
        const updatedCount = res.data.translations.length
        
        // Remove translated items from local list
        const completedIds = new Set(res.data.translations.map(t => t.id))
        tasks.value = tasks.value.filter(t => !completedIds.has(t.id))
        
        // Show success notification (could use Element Plus ElMessage if available, currently using console)
        console.log(`Translated ${updatedCount} items`)
        
    } catch (e) {
        console.error("Batch translation failed", e)
        alert("Batch translation failed. Please check console.")
    } finally {
        loading.value = false
    }
}

onMounted(() => {
    fetchTasks()
})
</script>
