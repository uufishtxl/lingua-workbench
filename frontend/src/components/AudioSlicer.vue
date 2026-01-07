<template>
    <div class="wave-surfer__wrapper flex flex-col gap-4 h-full overflow-hidden">
        <!-- Wave Container -->
        <el-card class="flex-none">
            <p class="text-xs text-gray-400 mb-2">Source: {{ props.title }}</p>

            <BaseWaveSurfer ref="baseWaveSurferRef" :url="props.url" @play="isPlaying = true" @pause="isPlaying = false"
                @region-created="handleRegionCreated" @region-updated="handleRegionUpdated"
                @region-removed="handleRegionRemoved" @region-in="handleRegionIn" @region-out="handleRegionOut"
                @region-clicked="handleRegionClicked" />

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
                </div>
            </div>
        </el-card>

        <!-- Region List -->
        <el-card class="flex-1 overflow-y-hidden flex flex-col">
            <h2 class="font-bold mb-4 border-b-[0.5px] border-blue-100/50 pb-2">Selected Regions</h2>
            
            <div class="flex-1 overflow-y-auto min-h-0">
                <div v-if="regionsList.length > 0" class="grid gap-1" style="grid-template-columns: repeat(auto-fill, minmax(20rem, 1fr));">
                    <SliceCard 
                        v-for="(region, index) in regionsList" 
                        :key="region.id" 
                        :ref="el => setSliceCardRef(index, el)"
                        :url="props.url"
                        :start="Number(region.start)"
                        :end="Number(region.end)"
                        :region="region"
                        @delete="removeRegion"
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

    </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import type { Region } from 'wavesurfer.js/dist/plugins/regions.js'
import BaseWaveSurfer from './BaseWaveSurfer.vue';
import SliceCard from './SliceCard.vue';
import { createBatchSlices, type CreateSliceRequest } from '@/api/slicerApi';
import { ElMessage } from 'element-plus';

const baseWaveSurferRef = ref<InstanceType<typeof BaseWaveSurfer> | null>(null)
const loopRegion = ref<boolean>(true)
const isPlaying = ref<boolean>(false)
const isSaving = ref<boolean>(false)
let activeRegion: Region | null = null;

const props = defineProps<{ url: string; title: string | null; chunkId: number }>()

type audio_type = 'Link' | 'H-Del' | 'Th-Del' | 'Flap-T'

interface RegionInfo {
    id: string;
    start: string;
    end: string;
    originalText: string;
    tags: audio_type[];
    note: string;
    isTranscribing?: boolean;
}

const regionsList = ref<RegionInfo[]>([])

// Store refs to SliceCard components
const sliceCardRefs = ref<Map<number, InstanceType<typeof SliceCard>>>(new Map())

const setSliceCardRef = (index: number, el: any) => {
    if (el) {
        sliceCardRefs.value.set(index, el)
    } else {
        sliceCardRefs.value.delete(index)
    }
}

watch(regionsList, (list) => {
    list.sort((a, b) => parseFloat(a.start) - parseFloat(b.start));
}, { deep: true });

const handleRegionCreated = (newRegion: Region) => {
    if (!regionsList.value.some(r => r.id === newRegion.id)) {
        regionsList.value.push({
            id: newRegion.id,
            start: newRegion.start.toFixed(2),
            end: newRegion.end.toFixed(2),
            originalText: '',
            tags: [],
            note: '',
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

const removeRegion = (id: string) => {
    const regions = baseWaveSurferRef.value?.getRegions()
    if (regions) {
        const region_to_del = Object.values(regions).find(r => r.id === id)
        if (region_to_del) {
            region_to_del.remove()
        }
    }
}

const saveRegions = async () => {
    if (isSaving.value) return
    
    isSaving.value = true
    
    try {
        // Collect data from all SliceCard components
        const slicesData: CreateSliceRequest[] = []
        
        sliceCardRefs.value.forEach((sliceCard) => {
            if (sliceCard?.getSliceData) {
                const data = sliceCard.getSliceData()
                slicesData.push({
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
    } catch (error) {
        console.error('Failed to save slices:', error)
        ElMessage.error('Failed to save slices')
    } finally {
        isSaving.value = false
    }
};
</script>