<template>
  <div class="max-w-6xl mx-auto p-6">
    <header class="flex justify-between items-center mb-8">
      <div>
        <h1 class="text-2xl font-bold text-white">Translation Manager</h1>
        <p class="text-zinc-400 mt-1">
          Batch translate idioms using DeepSeek
        </p>
      </div>
      <button @click="$router.push('/')" class="text-zinc-400 hover:text-white transition-colors">
        <i class="i-mdi-close text-2xl"></i>
      </button>
    </header>

    <!-- Controls -->
    <div class="bg-zinc-900 rounded-xl p-6 border border-zinc-800 mb-8 flex justify-between items-center">
        <div class="flex items-center gap-4">
            <div class="text-4xl font-bold text-blue-400">{{ tasks.length }}</div>
            <div class="text-zinc-400">
                Items missing translation
            </div>
        </div>

        <button 
            @click="startBatchTranslation"
            :disabled="loading || tasks.length === 0"
            class="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-lg shadow-lg shadow-blue-900/20 transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
            <i v-if="loading" class="i-mdi-loading animate-spin text-xl"></i>
            <i v-else class="i-mdi-translate text-xl"></i>
            {{ loading ? 'Translating...' : 'Translate All with DeepSeek' }}
        </button>
    </div>

    <!-- Data Table -->
    <div class="bg-zinc-900 rounded-xl border border-zinc-800 overflow-hidden">
        <table class="w-full text-left">
            <thead class="bg-zinc-950 text-zinc-400 uppercase text-xs">
                <tr>
                    <th class="px-6 py-4 font-medium">Original Text</th>
                    <th class="px-6 py-4 font-medium">Status</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-zinc-800">
                <tr v-if="tasks.length === 0 && !loading" class="text-center">
                    <td colspan="2" class="px-6 py-12 text-zinc-500">
                        No missing translations found. You are all set!
                    </td>
                </tr>
                <tr v-for="task in tasks" :key="task.id" class="hover:bg-zinc-800/50 transition-colors group">
                    <td class="px-6 py-4 text-zinc-200 text-lg font-serif">
                        {{ task.original_text }}
                    </td>
                    <td class="px-6 py-4">
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-900/30 text-yellow-500 border border-yellow-500/20">
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
