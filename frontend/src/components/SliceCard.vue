<template>
    <el-card class="w-80">
        <!-- Time Stamp -->
         <div class="w-full flex justify-between items-center text-xs">
            <p class="bg-sky-100 text-blue-400 px-2 py-1 rounded">00:00-00:23</p>
            <el-button text type="danger" :icon="Delete" class="is-del" circle />
         </div>
        <!-- Original Text 浏览/编辑区域 -->
         <div class="font-semibold relative h-24">
            <div class="original-text__wrapper rounded relative h-full" v-if="isEditingOriginal">
                <el-input v-model="editingText" :auto-size="false" type="textarea" :rows="3"/>
                <div class="absolute right-2 bottom-2 input__icons">
                    <el-button text circle size="small" @click="saveEditing">
                        <i-tabler-device-floppy class="text-sm text-green-600" />
                    </el-button>
                    <el-button text circle size="small" @click="cancelEditing">
                         <i-tabler-x class="text-sm text-red-400" />
                    </el-button>
                </div>
            </div>
            <InteractiveTextWithHilis  v-else :highlights="currentSlice.highlights" :text="currentSlice.text"
            :current-active-id="activeHighlightId" @click-highlight="handleHighlightClick" />
            <el-button v-if="!isEditingOriginal" text class="absolute bottom-2 right-2 is-edit" :icon="Edit" size="small" circle @click="startEditing" />
         </div>

         <!-- Wave -->
          <BaseWaveSurfer :height="50" url="http://192.168.31.192:8000/media/audio_slicer/chunks/chunk_002.mp3" />
    </el-card>

</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Delete, Edit } from '@element-plus/icons-vue'
import InteractiveTextWithHilis from './InteractiveTextWithHilis.vue';
import BaseWaveSurfer from './BaseWaveSurfer.vue';

type TagType = 'Flap T' | 'Reduction' | 'Linking' | 'Resyllabification'

interface Hili {
    id: string;
    start: number;
    end: number;
    content: string;
    tags: TagType[];
    note: string;
}

const mockData = {
    // 1. 原文文本
    text: "Just not enough to put us in the original wedding party.",

    // 2. 高亮数组 (注意 start 和 end 的位置)
    highlights: [
        {
            id: 'uuid-001',          // 唯一ID，用于 key
            start: 4,                // "not enough" 开始的索引
            end: 15,                 // 结束索引
            content: "not enough",   // 对应文本(可选，方便调试)
            tags: ["Flap-T", "Reduction"], // 标签
            note: "这里 not 的 t 被浊化成了 d，enough 的 gh 发 f 音。" // 笔记
        },
        {
            id: 'uuid-002',
            start: 16,               // "put us in" 开始的索引
            end: 25,                 // 结束索引
            content: "put us in",
            tags: ["Linking", "Resyllabification"],
            note: "典型的连读：Pu-du-sin"
        }
    ]
};

const currentSlice = ref(mockData);
const activeHighlightId = ref(null);

const isEditingOriginal = ref(false)
const editingText = ref('')

// 开始编辑
const startEditing = () => {
    // 把当前文本复制到临时变量
    editingText.value = currentSlice.value.text
    // 切换模式
    isEditingOriginal.value = true
    // 关闭底下可能打开的 Note 面板，防止混乱
    activeHighlightId.value = null
}

// 保存编辑
const saveEditing = () => {
    const newText = editingText.value
    // @Todo：这里要执行“索引重算”或“清除失效高亮”逻辑
    // clearUpHighlights(currentSlice.value.text, newText, currentSlice.value.highlights)

    // 更新数据
    currentSlice.value.text = newText;
    isEditingOriginal.value = false;
}

// 取消编辑
const cancelEditing = () => {
    isEditingOriginal.value = false;
    editingText.value = '';
}

// 点击 InteractiveTextWithHilis 高亮文字后触发的逻辑
const handleHighlightClick = (highlightData) => {
    // 如果点的就是当前这个，就关闭 (toggle)
    if (activeHighlightId.value === highlightData.id) {
        activeHighlightId.value = null;
    } else {
        // 否则切换到新的
        activeHighlightId.value = highlightData.id;
    }
};
</script>

<style scoped>
:deep(.el-card__body) {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

:deep(.el-button.is-text.is-disabled) {
    color: #888;
}

:deep(.is-del.el-button.is-text) {
    color: oklch(70.4% 0.191 22.216);
}

:deep(.is-edit.el-button.is-text) {
    color: #3AA2E8;
}

:deep(.original-text__wrapper .input__icons .el-button.is-text:hover),
:deep(.original-text__wrapper .input__icons .el-button.is-text:focus) {
    background-color: #302849;
}

.original-text__wrapper {
    background: #1C1338;
    padding: 8px;
}

/* :deep(.el-textarea) {
    background: #1C1338;
} */

:deep(.el-textarea__inner) {
    background: transparent;
    color: white;
    border: none;
    box-shadow: none;
    font-size: 12px;
    font-weight: 400;
    resize: none;
    /* For Firefox */
    scrollbar-width: none;
}

/* For Webkit browsers (Chrome, Safari) */
:deep(.el-textarea__inner::-webkit-scrollbar) {
    display: none;
}

:deep(.el-textarea__inner:focus) {
    box-shadow: none;
}

:deep(.el-button+.el-button) {
    margin-left: 2px;
}
</style>