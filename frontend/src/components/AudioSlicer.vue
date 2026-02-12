<template>
    <div class="wave-surfer__wrapper flex flex-col gap-[4px] h-full overflow-hidden">
        <!-- Wave Container -->
        <el-card class="flex-none">
            <p class="text-xs text-gray-400 mb-1">Source: {{ props.title }}</p>

            <BaseWaveSurfer ref="baseWaveSurferRef" :url="props.url" @play="isPlaying = true" @pause="isPlaying = false"
                @region-created="handleRegionCreated" @region-updated="handleRegionUpdated"
                @region-removed="handleRegionRemoved" @region-in="handleRegionIn" @region-out="handleRegionOut"
                @region-clicked="handleRegionClicked" @ready="handleWaveSurferReady" />

            <!-- Controls -->
            <div class="flex justify-around items-center gap-4 mt-2">
                <div class="flex gap-6 items-center">
                    <el-button type="primary" @click="handlePlayPause" size="small" circle>
                        <i-tabler-player-pause-filled v-if="isPlaying" class="text-sm" />
                        <i-tabler-player-play-filled v-else class="text-sm" />
                    </el-button>
                    <el-button :type="loopRegion ? 'success' : ''" @click="loopRegion = !loopRegion" size="small" circle>
                        <i-tabler-repeat class="text-sm" />
                    </el-button>
                    <PlaybackSpeedControl v-model="currentPlaybackRate" :options="speedOptions" theme="light" />
                </div>
            </div>
        </el-card>

        <!-- Region List with Expandable Side Panel -->
        <div class="flex-1 flex flex-row gap-2 overflow-hidden">
            <!-- Main Content: SliceCards -->
            <el-card 
                :class="[
                    'overflow-y-hidden flex flex-col transition-all duration-300', 
                    isPanelExpanded 
                        ? (scriptPanelWidth === 'wide' ? 'w-[45rem] flex-shrink-0' : 'w-[22rem] flex-shrink-0') 
                        : 'flex-1',
                    isTransitioning ? 'transitioning-blur' : ''
                ]"
            >
                <h2 class="font-bold mb-2 border-b-[0.5px] border-blue-100/50 pb-0">Selected Regions</h2>
                
                <div class="flex-1 overflow-y-auto min-h-0">
                    <div v-if="regionsList.length > 0" 
                        class="grid gap-[3px] transition-all duration-300" 
                        :class="{ 'blur-content': isTransitioning }"
                        :style="isPanelExpanded 
                            ? (scriptPanelWidth === 'wide' 
                                ? 'grid-template-columns: repeat(2, 1fr);' 
                                : 'grid-template-columns: 1fr;')
                            : 'grid-template-columns: repeat(auto-fill, minmax(20rem, 1fr));'"
                    >
                        <SliceCard 
                            v-for="(region, index) in sortedRegionsList" 
                            :key="region.id" 
                            :ref="el => setSliceCardRef(index, el)"
                            :url="props.url"
                            :start="Number(region.start)"
                            :end="Number(region.end)"
                            :region="region"
                            :initial-highlights="region.savedHighlights"
                            :initial-pronunciation-hard="region.isPronunciationHard"
                            :initial-idiom="region.isIdiom"
                            @delete="removeRegion"
                            @adjust-start="(delta) => handleAdjustTime(region.id, 'start', delta)"
                            @adjust-end="(delta) => handleAdjustTime(region.id, 'end', delta)"
                            @update-markers="(markers) => handleUpdateMarkers(region.id, markers)"
                        />
                    </div>
                    <div v-else class="flex flex-col items-center justify-center h-full">
                        <p class="text-xs text-gray-600">Click and drag on the waveform to select regions.</p>
                    </div>
                </div>

                <div class="mt-4 w-full text-center flex-shrink-0 flex lg:px-96">
                    <el-button class="flex-1" type="primary" @click="saveRegions" :disabled="!regionsList.length" :loading="isSaving">
                        Save All Changes
                    </el-button>
                </div>
            </el-card>

            <!-- Floating Bubble Toggle Button (lg+ only) -->
            <div class="hidden lg:flex items-center relative">
                <button 
                    @click="togglePanel"
                    class="floating-toggle-btn"
                    :class="{ 'is-expanded': isPanelExpanded }"
                    :title="isPanelExpanded ? 'Collapse Panel' : 'Expand Script Panel'"
                >
                    <i-tabler-chevron-left v-if="isPanelExpanded" class="text-base" />
                    <i-tabler-chevron-right v-else class="text-base" />
                </button>
            </div>

            <!-- Side Panel (lg+ only, with animation) -->
            <Transition
                enter-active-class="transition-all duration-300 ease-out"
                leave-active-class="transition-all duration-300 ease-in"
                enter-from-class="opacity-0 translate-x-4"
                enter-to-class="opacity-100 translate-x-0"
                leave-from-class="opacity-100 translate-x-0"
                leave-to-class="opacity-0 translate-x-4"
            >
                <el-card 
                    v-if="isPanelExpanded" 
                    class="hidden lg:flex flex-1 flex-col overflow-hidden relative"
                >
                    <ScriptPanel
                        :chunk-id="props.chunkId"
                        :next-chunk-id="nextChunkId"
                        :review-mode="props.reviewMode"
                        :current-index="props.currentIndex"
                        :total-chunks="props.totalChunks"
                        :script-panel-width="scriptPanelWidth"
                        @search-slice="handleSearchSlice"
                        @toggle-width="scriptPanelWidth = scriptPanelWidth === 'normal' ? 'wide' : 'normal'"
                    />
                </el-card>
            </Transition>
        </div>

    </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted, onUnmounted, nextTick } from 'vue';
import type { Region } from 'wavesurfer.js/dist/plugins/regions.js'
import BaseWaveSurfer from './BaseWaveSurfer.vue';
import SliceCard from './SliceCard.vue';
import PlaybackSpeedControl from './PlaybackSpeedControl.vue';
import { createBatchSlices, deleteSlice, type CreateSliceRequest, type AudioSliceResponse } from '@/api/slicerApi';
import ScriptPanel from './ScriptPanel.vue';
import { ElMessage } from 'element-plus';

const baseWaveSurferRef = ref<InstanceType<typeof BaseWaveSurfer> | null>(null)
const isPanelExpanded = ref<boolean>(false)
const scriptPanelWidth = ref<'normal' | 'wide'>('normal')  // normal: 22rem, wide: 44rem
const isTransitioning = ref<boolean>(false)  // For blur effect during transition
const loopRegion = ref<boolean>(true)
const isPlaying = ref<boolean>(false)
const isSaving = ref<boolean>(false)
const isDirty = ref<boolean>(false)  // Track if changes were made
const currentPlaybackRate = ref(1);
const speedOptions = [0.2, 0.5, 1];
let activeRegion: Region | null = null;

// Toggle panel with blur transition
const togglePanel = () => {
  isTransitioning.value = true
  isPanelExpanded.value = !isPanelExpanded.value
  // Remove blur after transition completes (300ms matches CSS duration)
  setTimeout(() => {
    isTransitioning.value = false
  }, 350)
}

// ↓↓↓↓↓↓↓↓↓ Depreciated! Replaced by watch mechanism
// const handleSpeedChange = (rate: number) => {
//     currentPlaybackRate.value = rate;
//     baseWaveSurferRef.value?.setPlaybackRate(rate);
// };

const props = defineProps<{ 
    url: string; 
    title: string | null; 
    chunkId: number;
    initialSlices?: AudioSliceResponse[];
    // Review mode props
    nextChunkId?: number | null;
    currentIndex?: number;
    totalChunks?: number;
    reviewMode?: boolean;
}>()

// Watch for review mode changes to adjust defaults
watch(
  () => props.reviewMode,
  (isReviewMode) => {
    if (isReviewMode) {
      // In review mode: turn off loop, open side panel
      loopRegion.value = false
      isPanelExpanded.value = true
    }
  },
  { immediate: true }
)

// type audio_type = 'Link' | 'H-Del' | 'Th-Del' | 'Flap-T'

interface RegionInfo {
    id: string;  // WaveSurfer region ID
    dbId?: number;  // Database ID for updates
    start: string;
    end: string;
    originalText: string;
    // tags: audio_type[];
    // note: string;
    isTranscribing?: boolean;
    isPronunciationHard?: boolean;  // Mark as pronunciation hard
    isIdiom?: boolean;  // Mark as idiom/new word
    // Link to saved slice data for restoring analysis/dictionary
    savedHighlights?: AudioSliceResponse['highlights'];
}

const regionsList = ref<RegionInfo[]>([])

// Sorted regions for display
const sortedRegionsList = computed(() => 
    [...regionsList.value].sort((a, b) => Number(a.start) - Number(b.start))
)

// Next chunk ID for script panel (placeholder - should be passed as prop or computed)
const nextChunkId = computed(() => {
    // TODO: This should be computed based on source audio chunks
    // For now, return chunkId + 1 as placeholder
    return props.chunkId ? props.chunkId + 1 : undefined
})

// Handle search request from ScriptPanel
const handleSearchSlice = (text: string) => {
    // Find SliceCard that contains this text
    const matchIndex = sortedRegionsList.value.findIndex(region => {
        const sliceCard = sliceCardRefs.value.get(sortedRegionsList.value.indexOf(region))
        const sliceData = sliceCard?.getSliceData?.()
        return sliceData?.original_text?.toLowerCase().includes(text.toLowerCase())
    })
    
    if (matchIndex >= 0) {
        // Scroll to and highlight the matching card
        const sliceCard = sliceCardRefs.value.get(matchIndex)
        if (sliceCard?.$el) {
            sliceCard.$el.scrollIntoView({ behavior: 'smooth', block: 'center' })
            sliceCard.$el.classList.add('ring-2', 'ring-blue-500')
            setTimeout(() => {
                sliceCard.$el.classList.remove('ring-2', 'ring-blue-500')
            }, 2000)
        }
        ElMessage.success('Found matching slice')
    } else {
        ElMessage.warning('No matching audio slice found')
    }
}

// Store refs to SliceCard components
const sliceCardRefs = ref<Map<number, InstanceType<typeof SliceCard>>>(new Map())

const setSliceCardRef = (index: number, el: any) => {
    if (el) {
        sliceCardRefs.value.set(index, el)
    } else {
        sliceCardRefs.value.delete(index)
    }
}

// Flag to prevent dirty state during initialization
const isInitialized = ref(false)
const isWaveSurferReady = ref(false)

const syncRegionsToWaveSurfer = () => {
    if (!isWaveSurferReady.value || !regionsList.value.length) return
    
    regionsList.value.forEach(region => {
        // Check if region already exists in WaveSurfer to avoid duplicates
        const existingRegions = baseWaveSurferRef.value?.getRegions()
        const exists = existingRegions && Object.values(existingRegions).some(r => r.id === region.id)
        
        if (!exists) {
            baseWaveSurferRef.value?.addRegion({
                id: region.id,
                start: parseFloat(region.start),
                end: parseFloat(region.end),
                color: 'rgba(64, 158, 255, 0.1)',
                drag: true,
                resize: true
            })
        }
    })
}

const handleWaveSurferReady = () => {
    isWaveSurferReady.value = true
    syncRegionsToWaveSurfer()
}

// Listen for global save-before-expiration event (from TokenExpirationWarning)
const handleSaveBeforeExpiration = () => {
    if (isDirty.value && regionsList.value.length > 0) {
        console.log('Auto-saving before token expiration...')
        saveRegions()
    }
}

// Warn user before leaving page with unsaved changes
const handleBeforeUnload = (e: BeforeUnloadEvent) => {
    if (isDirty.value && regionsList.value.length > 0) {
        e.preventDefault()
        e.returnValue = ''
        return ''
    }
}

onMounted(() => {
    // Listen for save-before-expiration event
    window.addEventListener('save-before-expiration', handleSaveBeforeExpiration)
    // Warn before page unload
    window.addEventListener('beforeunload', handleBeforeUnload)
})

onUnmounted(() => {
    window.removeEventListener('save-before-expiration', handleSaveBeforeExpiration)
    window.removeEventListener('beforeunload', handleBeforeUnload)
})

watch(currentPlaybackRate, (rate) => {
    baseWaveSurferRef.value?.setPlaybackRate(rate)
})

// Initialize from saved slices when prop becomes available
watch(() => props.initialSlices, (newSlices) => {
    if (newSlices?.length && regionsList.value.length === 0) {
        console.log('Initializing from saved slices:', newSlices.length)
        regionsList.value = newSlices.map((slice) => ({
            id: `saved-${slice.id}`,
            dbId: slice.id,  // Store database ID for updates
            start: slice.start_time.toFixed(2),
            end: slice.end_time.toFixed(2),
            originalText: slice.original_text,
            // tags: [],
            // note: '',
            isTranscribing: false,
            isPronunciationHard: slice.is_pronunciation_hard,
            isIdiom: slice.is_idiom,
            savedHighlights: slice.highlights
        }))
        
        // Try to sync to WaveSurfer if it's already ready
        nextTick(() => {
            syncRegionsToWaveSurfer()
        })
    }
    // Mark as initialized after first load attempt
    nextTick(() => {
        isInitialized.value = true
        isDirty.value = false
    })
}, { immediate: true })

// Mark as dirty when changes are made (only after initialization)
watch(regionsList, () => {
    if (isInitialized.value) {
        isDirty.value = true
    }
}, { deep: true });

const handleRegionCreated = (newRegion: Region) => {
    if (!regionsList.value.some(r => r.id === newRegion.id)) {
        regionsList.value.push({
            id: newRegion.id,
            start: newRegion.start.toFixed(2),
            end: newRegion.end.toFixed(2),
            originalText: '',
            // tags: [],
            // note: '',
            isTranscribing: false,
        });
    }
}

const handleRegionUpdated = (updatedRegion: Region) => {
    const regionInList = regionsList.value.find(r => r.id === updatedRegion.id);
    if (regionInList) {
        regionInList.start = updatedRegion.start.toFixed(2);
        regionInList.end = updatedRegion.end.toFixed(2);
    }
}

const handleRegionRemoved = (removedRegion: Region) => {
    regionsList.value = regionsList.value.filter(r => r.id !== removedRegion.id);
}

const handlePlayPause = () => {
    baseWaveSurferRef.value?.playPause()
}

const handleRegionIn = (region: Region) => {
    activeRegion = region
}

const handleRegionOut = (region: Region) => {
    if (activeRegion === region) {
        if (loopRegion.value) region.play()
        else activeRegion = null
    }
}

const handleRegionClicked = (region: Region, e: MouseEvent) => {
    e.stopPropagation()
    activeRegion = region
    region.play()
}

const removeRegion = async (id: string) => {
    // Check if this is a saved slice (has dbId)
    const regionInList = regionsList.value.find(r => r.id === id)
    if (regionInList?.dbId) {
        try {
            await deleteSlice(regionInList.dbId)
            ElMessage.success('Slice deleted')
        } catch (error) {
            console.error('Failed to delete slice:', error)
            ElMessage.error('Failed to delete slice')
            return  // Don't remove from UI if API failed
        }
    }
    
    // Remove from WaveSurfer
    const regions = baseWaveSurferRef.value?.getRegions()
    if (regions) {
        const region_to_del = Object.values(regions).find(r => r.id === id)
        if (region_to_del) {
            region_to_del.remove()
        }
    }
}

// Handle time adjustment from SliceCard arrows
const handleAdjustTime = (regionId: string, type: 'start' | 'end', delta: number) => {
    // Update in regionsList
    const regionInList = regionsList.value.find(r => r.id === regionId)
    if (!regionInList) return
    
    if (type === 'start') {
        const newStart = Math.max(0, Number(regionInList.start) + delta)
        regionInList.start = newStart.toFixed(2)
    } else {
        const newEnd = Number(regionInList.end) + delta
        regionInList.end = newEnd.toFixed(2)
    }
    
    // Sync to WaveSurfer region
    const regions = baseWaveSurferRef.value?.getRegions()
    if (regions) {
        const wsRegion = Object.values(regions).find(r => r.id === regionId)
        if (wsRegion) {
            wsRegion.setOptions({
                start: Number(regionInList.start),
                end: Number(regionInList.end)
            })
        }
    }
}

// Handle marker updates from SliceCard
const handleUpdateMarkers = (regionId: string, markers: { isPronunciationHard: boolean; isIdiom: boolean }) => {
    const regionInList = regionsList.value.find(r => r.id === regionId)
    if (regionInList) {
        regionInList.isPronunciationHard = markers.isPronunciationHard
        regionInList.isIdiom = markers.isIdiom
        // console.log(regionInList.isPronunciationHard, regionInList.isIdiom, regionsList.value[0])
    }
}

const saveRegions = async () => {
    if (isSaving.value) return
    
    isSaving.value = true
    
    try {
        // Collect data from all SliceCard components
        const slicesData: CreateSliceRequest[] = []
        
        // Iterate through sorted regions to match with sliceCardRefs
        sortedRegionsList.value.forEach((region, index) => {
            const sliceCard = sliceCardRefs.value.get(index)
            if (sliceCard?.getSliceData) {
                const data = sliceCard.getSliceData()
                slicesData.push({
                    id: region.dbId,  // Include database ID for updates
                    audio_chunk: props.chunkId,
                    ...data
                })
            }
        })
        
        if (slicesData.length === 0) {
            ElMessage.warning('No data to save')
            return
        }
        
        console.log('Saving slices:', slicesData)
        const result = await createBatchSlices(slicesData)
        console.log('Save result:', result)
        ElMessage.success(`Saved ${result.length} slices successfully!`)
        isDirty.value = false  // Reset dirty after successful save
    } catch (error) {
        console.error('Failed to save slices:', error)
        ElMessage.error('Failed to save slices')
    } finally {
        isSaving.value = false
    }
};
</script>

<style scoped>
/* Floating Bubble Toggle Button */
.floating-toggle-btn {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
  transition: all 0.3s ease;
  cursor: pointer;
  border: none;
}

.floating-toggle-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.5);
}

.floating-toggle-btn.is-expanded {
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
}

.floating-toggle-btn.is-expanded:hover {
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5);
}

/* Blur Content During Transition */
.blur-content {
  filter: blur(4px);
  opacity: 0.7;
  pointer-events: none;
}

/* Optional: Add skeleton shimmer effect */
.transitioning-blur .blur-content {
  position: relative;
}

.transitioning-blur .blur-content::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.4) 50%,
    transparent 100%
  );
  animation: shimmer 0.4s ease-out;
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}
</style>