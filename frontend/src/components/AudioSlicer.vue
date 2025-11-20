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
            
            <div class="flex-1 overflow-y-auto min-h-0">
                <div v-if="regionsList.length > 0" class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 p-1">
                    <RegionEditor 
                        v-for="region in regionsList" 
                        :key="region.id" 
                        :region="region" 
                        @delete="removeRegion"
                        @edit="openEditDialog"
                    />
                </div>
                <div v-else class="flex flex-col items-center justify-center h-full">
                    <p class="text-xs text-gray-600">Click and drag on the waveform to select regions.</p>
                    <SliceCard />
                </div>
            </div>

            <div class="mt-4 w-full text-center flex-shrink-0 flex lg:px-96">
                <el-button class="flex-1" type="primary" @click="saveRegions" :disabled="!regionsList.length">Save All Changes</el-button>
            </div>
        </el-card>

        <!-- Edit Dialog -->
        <el-dialog v-model="isDialogVisible" :title="`Edit Region: ${currentEditingRegion?.id}`">
            <div v-if="currentEditingRegion">
                <el-form label-position="top">
                    <el-form-item label="Original Text">
                        <el-input v-model="currentEditingRegion.originalText" type="textarea" :rows="3" placeholder="Type the sentence here..." />
                    </el-form-item>
                    <el-form-item label="Annotated Preview">
                        <AnnotatedText :annotatedText="parsedAnnotatedText" />
                    </el-form-item>
                    <el-form-item label="Note">
                        <el-input v-model="currentEditingRegion.note" type="textarea" :rows="2" />
                    </el-form-item>
                    <el-form-item label="Tags">
                        <el-checkbox-group v-model="currentEditingRegion.tags">
                            <el-checkbox v-for="tag in allTags" :key="tag" :label="tag" :value="tag" />
                        </el-checkbox-group>
                    </el-form-item>
                </el-form>
            </div>
            <template #footer>
                <span class="dialog-footer">
                    <el-button @click="isDialogVisible = false">Cancel</el-button>
                    <el-button type="primary" @click="isDialogVisible = false">Confirm</el-button>
                </span>
            </template>
        </el-dialog>
    </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import type { Region } from 'wavesurfer.js/dist/plugins/regions.js'
import BaseWaveSurfer from './BaseWaveSurfer.vue';
import RegionEditor from './RegionEditor.vue';
import AnnotatedText from './AnnotatedText.vue';
import SliceCard from './SliceCard.vue';

const baseWaveSurferRef = ref<InstanceType<typeof BaseWaveSurfer> | null>(null)
const loopRegion = ref<boolean>(true)
const isPlaying = ref<boolean>(false)
let activeRegion: Region | null = null;

const props = defineProps<{ url: string; title: string | null }>()

type audio_type = 'Link' | 'H-Del' | 'Th-Del' | 'Flap-T'
const allTags: audio_type[] = ['Link', 'H-Del', 'Th-Del', 'Flap-T'];

interface RegionInfo {
    id: string;
    start: string;
    end: string;
    originalText: string;
    tags: audio_type[];
    note: string;
}

const regionsList = ref<RegionInfo[]>([])
const isDialogVisible = ref(false)
const currentEditingRegion = ref<RegionInfo | null>(null)

const parsedAnnotatedText = computed(() => {
    if (!currentEditingRegion.value?.originalText) return [];
    const words = currentEditingRegion.value.originalText.split(/(\s+)/); // Split by spaces, keeping spaces
    return words.map(wordText => {
        if (wordText.trim() === '') { // If it's just whitespace
            return { text: wordText };
        }
        // Example: Apply 'Flap-T' tag to 'matter' if region has 'Flap-T'
        const tagsForWord: audio_type[] = [];
        if (currentEditingRegion.value?.tags.includes('Flap-T') && wordText.toLowerCase().includes('matter')) {
            tagsForWord.push('Flap-T');
        }
        // Add other tags based on some logic if needed
        return { text: wordText, tags: tagsForWord.length > 0 ? tagsForWord : undefined };
    });
});

watch(regionsList, (list) => {
    list.sort((a, b) => parseFloat(a.start) - parseFloat(b.start));
}, { deep: true });

const openEditDialog = (regionId: string) => {
    const regionToEdit = regionsList.value.find(r => r.id === regionId);
    if (regionToEdit) {
        currentEditingRegion.value = regionToEdit;
        isDialogVisible.value = true;
    }
}

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