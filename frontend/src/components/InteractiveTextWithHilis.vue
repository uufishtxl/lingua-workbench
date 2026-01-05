<script setup lang="ts">
import { computed } from 'vue';
import type { SoundScriptResponse, ScriptSegment } from '@/api/aiAnalysisApi';

interface Hili {
  id: string;
  start: number;
  end: number;
  content: string;
  tags: string[];
  note: string;
}

const props = defineProps<{
  text: string;
  highlights: Hili[];
  currentActiveId: string | null;
  analysisResults?: Map<string, SoundScriptResponse>;
}>();

const emit = defineEmits(['click-highlight']);

// Helper: Get script_segments for a highlight
const getScriptSegments = (highlightId: string): ScriptSegment[] | null => {
  if (!props.analysisResults) return null;
  const result = props.analysisResults.get(highlightId);
  if (!result?.script_segments?.length) return null;
  return result.script_segments;
};

// 核心算法：把纯文本转换成 Token 数组
const tokens = computed(() => {
  const result: Array<{
    text: string;
    isHighlight: boolean;
    data?: Hili;
    segments?: ScriptSegment[] | null;
  }> = [];
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
      data: hl,
      segments: getScriptSegments(hl.id)
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
  return result;
});
</script>

<template>
  <div class="font-serif tracking-tight interactive-text">
    <template v-for="(token, index) in tokens" :key="index">
      <!-- Highlight with Ruby Text segments -->
      <span
        v-if="token.isHighlight && token.segments?.length"
        class="highlight-group"
        :class="{ 'is-active': token.data?.id === currentActiveId }"
        @click="emit('click-highlight', token.data)"
      >
        <ruby 
          v-for="(seg, si) in token.segments" 
          :key="si"
          :class="['ruby-segment', seg.is_stressed ? 'stressed' : 'unstressed']"
        >
          {{ seg.original }}
          <rt>{{ seg.sound_display }}</rt>
        </ruby>
      </span>
      
      <!-- Highlight without Ruby Text -->
      <span
        v-else-if="token.isHighlight"
        class="highlight-span"
        :class="{ 'is-active': token.data?.id === currentActiveId }"
        @click="emit('click-highlight', token.data)"
      >{{ token.text }}</span>
      
      <!-- Normal text -->
      <span v-else>{{ token.text }}</span>
    </template>
  </div>
</template>

<style scoped>
.interactive-text {
  line-height: 2.2;
}

.highlight-group {
  cursor: pointer;
  padding: 2px 0;
}

.highlight-span {
  background: #fef3c7;
  cursor: pointer;
  border-radius: 4px;
  padding: 2px 4px;
  margin: 0 2px;
  transition: background 0.2s;
}

.highlight-span:hover {
  background: #fde68a;
}

.highlight-span.is-active,
.highlight-group.is-active {
  background: #e0f2fe;
}

/* Ruby segment styling */
.ruby-segment {
  margin: 0 1px;
}

/* 非重读：灰色 */
.ruby-segment.unstressed rt {
  font-size: 0.6em;
  color: #9ca3af;
  font-weight: 400;
}

/* 重读：红色粗体 */
.ruby-segment.stressed rt {
  font-size: 0.6em;
  color: #dc2626;
  font-weight: 700;
}
</style>