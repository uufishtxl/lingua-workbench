<template>
    <div class="slice-list-view">
        <div class="flex justify-between items-center mb-4">
            <h2 class="text-lg font-bold">Saved Slices</h2>
            <el-button type="primary" @click="$emit('switch-to-edit')">
                <i-tabler-edit class="mr-1" /> Edit Mode
            </el-button>
        </div>

        <el-table :data="slices" stripe style="width: 100%" @row-click="handleRowClick">
            <el-table-column prop="start_time" label="Time" width="120">
                <template #default="{ row }">
                    {{ formatTime(row.start_time) }} - {{ formatTime(row.end_time) }}
                </template>
            </el-table-column>
            <el-table-column prop="original_text" label="Text" show-overflow-tooltip>
                <template #default="{ row }">
                    <span class="text-sm">{{ row.original_text }}</span>
                </template>
            </el-table-column>
            <el-table-column label="Highlights" width="100" align="center">
                <template #default="{ row }">
                    <el-tag v-if="row.highlights?.length" size="small" type="success">
                        {{ row.highlights.length }}
                    </el-tag>
                    <span v-else class="text-gray-400">-</span>
                </template>
            </el-table-column>
        </el-table>

        <!-- Expanded Slice Detail -->
        <el-dialog v-model="dialogVisible" title="Slice Detail" width="600px">
            <div v-if="selectedSlice" class="slice-detail">
                <p class="text-sm text-gray-500 mb-2">
                    {{ formatTime(selectedSlice.start_time) }} - {{ formatTime(selectedSlice.end_time) }}
                </p>
                <p class="text-lg mb-4 font-serif">{{ selectedSlice.original_text }}</p>
                
                <div v-if="selectedSlice.highlights?.length" class="space-y-3">
                    <div v-for="hl in selectedSlice.highlights" :key="hl.id" 
                         class="p-3 bg-amber-50 rounded-lg">
                        <p class="font-semibold text-amber-800">{{ hl.focus_segment }}</p>
                        <!-- Analysis data -->
                        <div v-if="hl.analysis?.phonetic_tags?.length" class="mt-2 space-y-1">
                            <div v-for="(tag, idx) in hl.analysis.phonetic_tags" :key="idx" 
                                 class="text-sm text-gray-600">
                                <el-tag size="small" type="info">{{ tag }}</el-tag>
                                <span class="ml-2">{{ hl.analysis.phonetic_tag_notes?.[idx] }}</span>
                            </div>
                        </div>
                        <!-- Dictionary data -->
                        <p v-if="hl.dictionary?.definition_cn" class="mt-2 text-sm">
                            📖 {{ hl.dictionary.definition_cn }}
                        </p>
                        <div v-if="hl.dictionary?.examples?.length" class="mt-2 text-sm text-gray-500">
                            <p>{{ hl.dictionary.examples[0].english }}</p>
                            <p>{{ hl.dictionary.examples[0].chinese }}</p>
                        </div>
                    </div>
                </div>
                <p v-else class="text-gray-400 text-center py-4">No highlights</p>
            </div>
        </el-dialog>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import type { AudioSliceResponse } from '@/api/slicerApi';

defineProps<{
    slices: AudioSliceResponse[]
}>();

defineEmits(['switch-to-edit']);

const dialogVisible = ref(false);
const selectedSlice = ref<AudioSliceResponse | null>(null);

const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
};

const handleRowClick = (row: AudioSliceResponse) => {
    selectedSlice.value = row;
    dialogVisible.value = true;
};
</script>

<style scoped>
.slice-list-view {
    padding: 16px;
}
</style>
