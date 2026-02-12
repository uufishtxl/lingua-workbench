<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import FluentEmojiFlatMilitaryMedal from '~icons/fluent-emoji-flat/military-medal'
import { fetchBlitzCards, fetchBlitzStats, type BlitzCard, type BlitzFilters, type BlitzStats } from '@/api/blitzApi'
import FlipCard from '@/components/blitz/FlipCard.vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import StatsDisplay from '@/components/dashboard/StatsDisplay.vue'
import { getSpeakerAttributes } from '@/utils/speakerAssets'

const dashboardStore = useDashboardStore()
const { stats: dashStats } = storeToRefs(dashboardStore)

// State
const cards = ref<BlitzCard[]>([])
const stats = ref<BlitzStats[]>([])
const loading = ref(false)
const filters = ref<BlitzFilters>({
  mode: 'normal',
  status: 'learning',
  character: 'All',
  page: 1,
  limit: 12
})
const hasNext = ref(true)

// DOM Refs
const sentinelRef = ref<HTMLElement | null>(null)
let observer: IntersectionObserver | null = null

// Fetch Stats for Dock
const loadStats = async () => {
  try {
    const res = await fetchBlitzStats()
    stats.value = res.data
    dashboardStore.fetchStats()
  } catch (e) {
    console.error('Failed to load stats', e)
  }
}

// Fetch Cards
const loadCards = async (reset = false) => {
  if (loading.value || (!hasNext.value && !reset)) return
  
  loading.value = true
  if (reset) {
    filters.value.page = 1
    cards.value = []
    hasNext.value = true
  }

  try {
    const res = await fetchBlitzCards(filters.value)
    const data = res.data

    if (reset) {
      cards.value = data.results
    } else {
      cards.value.push(...data.results)
    }
    
    // Unified pagination: DRF returns `next` (URL or null)
    // Use it for both shuffle and normal modes
    hasNext.value = !!data.next
    
    if (hasNext.value) {
      filters.value.page++
    }
  } catch (e) {
    console.error('Failed to load cards', e)
  } finally {
    loading.value = false
  }
}

// Actions
const setCharacter = (char: string) => {
  if (filters.value.character === char) return
  filters.value.character = char
  loadCards(true)
}

const toggleShuffle = () => {
  filters.value.mode = filters.value.mode === 'shuffle' ? 'normal' : 'shuffle'
  loadCards(true)
}

// Infinite Scroll Observer
const setupObserver = () => {
  observer = new IntersectionObserver((entries) => {
    if (entries[0]?.isIntersecting && !loading.value && hasNext.value) {
      loadCards()
    }
  }, { root: null, rootMargin: '200px' })
  
  if (sentinelRef.value && observer) observer.observe(sentinelRef.value)
}

onMounted(() => {
  loadStats()
  loadCards(true)
  setTimeout(setupObserver, 500)
})

onUnmounted(() => {
  if (observer) observer.disconnect()
})
</script>

<template>
  <div class="blitz-container flex flex-col h-full dark:bg-gray-900 overflow-hidden">
    
    <!-- Sticky Top Bar -->
    <header class="sticky top-0 z-20 h-14 flex-none bg-white dark:bg-gray-800 flex items-center justify-between px-6">
      <h1 class="text-lg font-bold text-gray-800 dark:text-white flex items-center gap-2 select-none">
        <FluentEmojiFlatMilitaryMedal />
        <span class="bg-gradient-to-r from-gray-800 to-gray-600 dark:from-white dark:to-gray-400 bg-clip-text text-transparent">突击训练营</span>
        
        <!-- Stats Display -->
        <div class="ml-2">
          <StatsDisplay 
            variant="blitz-header"
            :hardCount="dashStats?.hard_sentences ?? 0"
            :reviewCount="dashStats?.review_sentences ?? 0"
            @filter-status="(s) => { filters.status = s; loadCards(true) }"
          />
        </div>
      </h1>

      <div class="flex items-center gap-4">

        <!-- Shuffle Toggle -->
        <button 
          class="flex items-center gap-2 px-3 py-1.5 rounded-lg border transition-all active:scale-95"
          :class="filters.mode === 'shuffle' 
            ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-400' 
            : 'border-gray-300 dark:border-gray-600 text-gray-500 hover:border-gray-400'"
          @click="toggleShuffle"
          title="Toggle Shuffle Mode"
        >
          <i-tabler-arrows-shuffle class="text-lg" />
          <span class="text-sm font-medium">Shuffle</span>
          <span v-if="filters.mode === 'shuffle'" class="flex h-2 w-2 relative">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
          </span>
        </button>
      </div>
    </header>

    <!-- Sticky Avatar Dock -->
    <div class="sticky top-14 z-10 h-20 flex-none flex items-center gap-1 bg-white/90 dark:bg-gray-900/90 backdrop-blur-sm overflow-x-auto overflow-y-hidden px-4 py-2 border-b border-gray-200 dark:border-gray-800 dock-container">
      <!-- All -->
      <button 
        class="group relative w-12 h-12 rounded-full flex items-center justify-center text-[10px] font-bold shadow-sm transition-all duration-200 ease-out hover:-translate-y-2 hover:mx-2 hover:scale-125 hover:shadow-lg z-10 p-0.5"
        :class="filters.character === 'All' ? 'bg-primary-600 shadow-md scale-110 ring-2 ring-primary-300 ring-offset-2 dark:ring-offset-gray-900' : 'bg-white dark:bg-gray-700'"
        @click="setCharacter('All')"
      >
        <img :src="getSpeakerAttributes('All').avatarUrl" alt="All" class="w-full h-full object-cover rounded-full" />
      </button>

      <!-- Characters -->
      <button 
        v-for="stat in stats" 
        :key="stat.speaker || 'unknown'"
        class="group relative w-12 h-12 rounded-full bg-white dark:bg-gray-700 transition-all duration-200 ease-out hover:-translate-y-2 hover:mx-2 hover:scale-125 hover:shadow-lg overflow-visible border-2 z-10 p-0.5"
        :class="filters.character === stat.speaker 
          ? 'border-primary-500 scale-110 shadow-md ring-2 ring-primary-500/20 z-0' 
          : 'border-white dark:border-gray-600 hover:border-primary-300'"
        @click="setCharacter(stat.speaker || '')"
      >
        <!-- Avatar Img -->
        <div class="w-full h-full rounded-full overflow-hidden flex items-center justify-center bg-gray-50 dark:bg-gray-800">
          <img :src="getSpeakerAttributes(stat.speaker).avatarUrl" :alt="stat.speaker" class="w-full h-full object-cover" />
        </div>
        
        <!-- Count badge -->
        <span class="absolute -top-1 -right-1 min-w-[1.25rem] h-5 rounded-full bg-gray-800 text-white text-[10px] flex items-center justify-center border-2 border-white dark:border-gray-800 z-20 shadow-sm pointer-events-none">
          {{ stat.count > 99 ? '99+' : stat.count }}
        </span>


      </button>
    </div>

    <!-- Main Grid (Scrollable) -->
    <main class="flex-1 overflow-y-auto min-h-0 bg-white dark:bg-gray-900/50 p-4 sm:p-6" id="blitz-scroll-container">
      
      <!-- Card Grid -->
      <div 
        v-if="cards.length > 0"
        class="max-w-8xl mx-auto flex flex-wrap gap-0 pb-8 perspective-container -m-3"
      >
        <div 
          v-for="card in cards" 
          :key="card.id" 
          class="p-3 w-full md:w-1/4 min-[1150px]:w-1/3 2xl:w-1/5"
        >
          <FlipCard :card="card" />
        </div>
      </div>

      <!-- Empty State -->
      <div v-else-if="!loading" class="h-full flex flex-col items-center justify-center text-gray-400">
        <div class="w-24 h-24 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mb-6">
          <i-tabler-cards class="text-4xl opacity-50" />
        </div>
        <p class="text-lg font-medium text-gray-500">No cards found</p>
        <p class="text-sm opacity-60 mt-1">Try adjusting the filters above</p>
        <button @click="loadCards(true)" class="mt-6 px-4 py-2 bg-primary-50 text-primary-600 rounded-lg text-sm font-medium hover:bg-primary-100 transition-colors">
          Refresh Data
        </button>
      </div>

      <!-- Loading Sentinel (Always outside card grid so it's always visible) -->
      <div ref="sentinelRef" class="w-full h-20 flex items-center justify-center">
        <svg v-if="loading" class="animate-spin h-6 w-6 text-primary-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <div v-else-if="!hasNext && cards.length > 0" class="flex flex-col items-center gap-2 text-gray-400">
          <div class="h-1 w-12 bg-gray-200 rounded-full"></div>
          <span class="text-xs font-medium uppercase tracking-widest opacity-60">End of List</span>
        </div>
      </div>
    </main>

  </div>
</template>

<style scoped>
.perspective-container {
  perspective: 2000px;
}

/* Dock Hover Interaction */
.dock-container:hover button {
  opacity: 0.7;
}
.dock-container button:hover {
  opacity: 1;
  z-index: 20;
}
/* Siblings next to hovered */
.dock-container button:hover + button,
.dock-container button:has(+ button:hover) {
  transform: scale(1.15) translateY(-4px);
  margin-left: 2px;
  margin-right: 2px;
  opacity: 0.9;
}
</style>
