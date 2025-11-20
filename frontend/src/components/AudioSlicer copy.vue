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
            <div class="flex justify-around items-center gap-4 mt-4">
                <div class="flex gap-6 items-center">
                    <el-button type="primary" @click="handlePlayPause" circle>
                        <i-tabler-player-pause-filled v-if="isPlaying" class="text-sm" />
                        <i-tabler-player-play-filled v-else class="text-sm" />
                    </el-button>
                    <el-button :type="loopRegion ? 'success' : ''" @click="loopRegion = !loopRegion" circle>
                        <i-tabler-repeat class="text-sm" />
                    </el-button>
                </div>
            </div>
        </el-card>

        <!-- Region List -->
        <el-card class="flex-1 overflow-y-hidden flex flex-col">
            <h2 class="font-bold mb-4 border-b-[0.5px] border-blue-100/50 pb-2">Selected Regions</h2>
            
            <!-- Header Row -->
            <el-row :gutter="24" class="text-sm text-gray-500 font-semibold mb-2 px-2">
                <el-col :span="3" class="text-center">Time</el-col>
                <el-col :span="7" class="text-center">Original Text</el-col>
                <el-col :span="7" class="text-center">Note</el-col>
                <el-col :span="3" class="text-center">Tags</el-col>
                <el-col :span="2" class="text-center">Actions</el-col>
            </el-row>

            <div class="flex-1 overflow-y-auto min-h-0 flex flex-col">
                <div v-if="regionsList.length > 0">
                    <RegionEditor v-for="region in regionsList" :key="region.id" :region="region" @delete="removeRegion"
                        @update:tags="handleUpdateTags" @update:field="handleUpdateRegion" />
                </div>
                <div v-else class="flex-grow flex items-center justify-center">
                    <p class="text-xs text-gray-600">Click and drag on the waveform to select regions.</p>
                </div>
            </div>

            <div class="mt-4 w-full text-center flex-shrink-0 flex lg:px-96">
                <el-button class="flex-1" type="primary" @click="saveRegions" :disabled="!regionsList.length">Save All Changes</el-button>
            </div>

        </el-card>
    </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import type { Region } from 'wavesurfer.js/dist/plugins/regions.js'
import BaseWaveSurfer from './BaseWaveSurfer.vue';
import RegionEditor from './RegionEditor.vue';

const baseWaveSurferRef = ref<InstanceType<typeof BaseWaveSurfer> | null>(null)
const loopRegion = ref<boolean>(true)
const isPlaying = ref<boolean>(false)
let activeRegion: Region | null = null;

const props = defineProps<{ url: string; title: string | null }>()

type audio_type = 'Link' | 'H-Del' | 'Th-Del' | 'Flap-T'

interface RegionInfo {
    id: string;
    start: string;
    end: string;
    originalText: string;
    tags: audio_type[];
    note: string;
}

const regionsList = ref<RegionInfo[]>([])

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

const handleUpdateTags = (payload: { id: string, tags: audio_type[] }) => {
    const region = regionsList.value.find(r => r.id === payload.id);
    if (region) {
        region.tags = payload.tags;
    }
}

const handleUpdateRegion = (payload: { id: string, key: keyof RegionInfo, value: any }) => {
    const region = regionsList.value.find(r => r.id === payload.id);
    if (region) {
        (region[payload.key] as any) = payload.value;
    }
}

const saveRegions = () => {
    console.log('Saving regions to server:', regionsList.value);
};
</script>