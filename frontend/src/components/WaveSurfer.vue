<template>
    <div class="wave-surfer__wrapper flex flex-col gap-4">
        <el-card>
            <p class="text-xs text-gray-400 mb-2">Source: {{ props.title }}</p>

            <BaseWaveSurfer ref="baseWaveSurferRef" :url="props.url" @play="isPlaying = true" @pause="isPlaying = false"
                @region-created="updateRegionsList" @region-updated="updateRegionsList"
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

        <el-card>
            <h2 class="font-bold">Selected Regions</h2>
            <!-- This is where you would list and edit the regionsList -->

            <div v-if="regionsList.length > 0">
                <RegionEditor v-for="region in regionsList" :key="region.id" :region="region" @delete="removeRegion"
                    @update:tags="handleUpdateTags" @update:field="handleUpdateRegion" />
            </div>
            <div v-else>
                <p class="text-sm text-gray-600">Click and drag on the waveform to select regions.</p>
            </div>
            <div class="mt-4 text-right">
                <el-button type="success" @click="saveRegions">Save All Changes</el-button>
            </div>

        </el-card>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
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

const updateRegionsList = () => {
    const regions = baseWaveSurferRef.value?.getRegions()
    if (!regions) return;

    const newRegionsMap = new Map<string, RegionInfo>();

    for (const region of Object.values(regions)) {
        const existingRegion = regionsList.value.find(r => r.id === region.id);

        if (existingRegion) {
            newRegionsMap.set(region.id, {
                ...existingRegion,
                start: region.start.toFixed(2),
                end: region.end.toFixed(2),
            });
        } else {
            newRegionsMap.set(region.id, {
                id: region.id,
                start: region.start.toFixed(2),
                end: region.end.toFixed(2),
                originalText: '',
                tags: [],
                note: '',
            });
        }
    }
    regionsList.value = Array.from(newRegionsMap.values());
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
            // Directly filter the list to ensure UI updates reliably
            regionsList.value = regionsList.value.filter(r => r.id !== id)
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