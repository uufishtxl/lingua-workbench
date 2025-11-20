<script setup>
import { computed } from 'vue';

const props = defineProps({
    text: {
        type: String,
        default: ""
    },
    highlights: {
        type: Array,
        default: () => [] // ✅ 重点：默认返回一个空数组，防止 undefined
    },
    currentActiveId: {
        type: [String, Number],
        default: null
    }
});

const emit = defineEmits(['click-highlight']);

// 核心算法：把纯文本转换成 Token 数组
const tokens = computed(() => {
    const result = [];
    let currentIndex = 0;

    // 1. 先按 start 位置排序，防止乱序
    const sortedHighlights = [...props.highlights].sort((a, b) => a.start - b.start);

    sortedHighlights.forEach(hl => {
        // A. 推入高亮前的普通文本
        if (hl.start > currentIndex) {
            result.push({
                text: props.text.slice(currentIndex, hl.start),
                isHighlight: false
            });
        }

        // B. 推入高亮文本本身
        result.push({
            text: props.text.slice(hl.start, hl.end),
            isHighlight: true,
            data: hl // 把整个高亮对象带上
        });

        // 更新当前指针
        currentIndex = hl.end;
    });

    // C. 推入剩下的普通文本
    if (currentIndex < props.text.length) {
        result.push({
            text: props.text.slice(currentIndex),
            isHighlight: false
        });
    }
    console.log("Computed tokens are ", result)
    return result;
});
</script>

<template>
    <div class="text-lg font-serif tracking-tight">
        <span v-for="(token, index) in tokens" :key="index" :class="[
            token.isHighlight
                ? 'bg-yellow-100 cursor-pointer hover:bg-yellow-200 rounded px-1 mx-0.5 transition relative'
                : '', 
            token.isHighlight && token.data.id === currentActiveId ? 'text-blue-500' : ''
        ]" @click="token.isHighlight ? emit('click-highlight', token.data) : null"
            >{{ token.text }}<span v-if="token.isHighlight && token.data.id === currentActiveId"
                class="absolute -top-4 left-1/2 -translate-x-1/2 text-xs"
                >▼</span></span>
    </div>
</template>