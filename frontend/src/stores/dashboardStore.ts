import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getDashboardStats, type DashboardStats } from '@/api/dashboardApi'

export const useDashboardStore = defineStore('dashboard', () => {
    const stats = ref<DashboardStats | null>(null)
    const isLoading = ref(false)
    const error = ref<string | null>(null)

    async function fetchStats() {
        isLoading.value = true
        error.value = null
        try {
            stats.value = await getDashboardStats()
            // console.log('dashboard stats', stats.value)
        } catch (e: any) {
            error.value = e.message || 'Failed to fetch dashboard stats'
            console.error(e)
        } finally {
            isLoading.value = false
        }
    }

    // Pre-load if empty
    async function ensureStats() {
        if (!stats.value) {
            await fetchStats()
        }
    }

    return {
        stats,
        isLoading,
        error,
        fetchStats,
        ensureStats
    }
})
