<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue';
import type { WordNode } from '@/api/englishCornerApi';
import { tokenizeByVocab } from '@/utils/highlightUtils';

const props = defineProps<{
  text: string;
  vocabs: WordNode[];
}>();

const emit = defineEmits(['select-text', 'click-vocab']);

const containerRef = ref<HTMLElement | null>(null);
const hoveredVocab = ref<WordNode | null>(null);
const tooltipPos = ref({ x: 0, y: 0 });

const tokens = computed(() => tokenizeByVocab(props.text, props.vocabs));

const handleMouseMove = (e: MouseEvent, vocab?: WordNode) => {
  if (vocab) {
    hoveredVocab.value = vocab;
    tooltipPos.value = { x: e.clientX, y: e.clientY };
  } else {
    hoveredVocab.value = null;
  }
};

const handleMouseUp = (e: MouseEvent) => {
  // Ignore if clicking on existing tooltips or buttons
  if ((e.target as HTMLElement).closest('.extract-tooltip, .vocab-tooltip')) {
    return;
  }

  const selection = window.getSelection();
  if (selection && !selection.isCollapsed) {
    const text = selection.toString().trim();
    if (text) {
      const range = selection.getRangeAt(0);
      const rect = range.getBoundingClientRect();
      emit('select-text', { text, rect });
    }
  }
};

onMounted(() => {
  containerRef.value?.addEventListener('mouseup', (e) => handleMouseUp(e));
});

onUnmounted(() => {
  containerRef.value?.removeEventListener('mouseup', handleMouseUp);
});
</script>

<template>
  <div ref="containerRef" class="vocab-rich-text">
    <template v-for="(token, index) in tokens" :key="index">
      <span 
        v-if="token.isVocab && token.vocabData" 
        class="vocab-highlight"
        @mouseenter="handleMouseMove($event, token.vocabData)"
        @mouseleave="handleMouseMove($event)"
        @click="emit('click-vocab', token.vocabData)"
      >
        {{ token.text }}
        <span class="glow-line"></span>
      </span>
      <span v-else>{{ token.text }}</span>
    </template>

    <!-- Floating Global Tooltip (Hover) -->
    <Teleport to="body">
      <div 
        v-if="hoveredVocab" 
        class="vocab-tooltip"
        :style="{ left: tooltipPos.x + 'px', top: tooltipPos.y + 'px' }"
      >
        <div class="tooltip-header">
          <span class="word">{{ hoveredVocab.label }}</span>
          <span class="type">{{ hoveredVocab.node_type }}</span>
        </div>
        <p class="explanation">{{ hoveredVocab.explanation }}</p>
        <div class="stats">
          <span>Mastery: {{ hoveredVocab.mastery }}%</span>
          <span>Box: {{ hoveredVocab.box_level }}</span>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.vocab-rich-text {
  line-height: 1.6;
  position: relative;
  cursor: text;
}

.vocab-highlight {
  position: relative;
  color: #fbbf24;
  font-weight: 600;
  cursor: pointer;
  padding: 0 2px;
  transition: all 0.2s;
}

.vocab-highlight:hover {
  text-shadow: 0 0 8px rgba(251, 191, 36, 0.4);
}

.glow-line {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, transparent, #fbbf24, transparent);
  opacity: 0.6;
  box-shadow: 0 0 10px rgba(251, 191, 36, 0.5);
  animation: breathe 2s infinite ease-in-out;
}

@keyframes breathe {
  0%, 100% { opacity: 0.3; transform: scaleX(0.8); }
  50% { opacity: 0.8; transform: scaleX(1); }
}

.vocab-tooltip {
  position: fixed;
  z-index: 2000;
  background: rgba(15, 23, 42, 0.95);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(251, 191, 36, 0.3);
  padding: 12px;
  border-radius: 12px;
  width: 240px;
  pointer-events: none;
  transform: translate(-50%, -100%) translateY(-20px);
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translate(-50%, -100%) translateY(-10px); }
  to { opacity: 1; transform: translate(-50%, -100%) translateY(-20px); }
}

.tooltip-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.tooltip-header .word {
  font-weight: 800;
  color: #fbbf24;
  font-size: 1rem;
}

.tooltip-header .type {
  font-size: 0.6rem;
  background: #334155;
  color: #94a3b8;
  padding: 2px 6px;
  border-radius: 4px;
  text-transform: uppercase;
}

.explanation {
  font-size: 0.85rem;
  color: #cbd5e1;
  margin: 0 0 10px 0;
  line-height: 1.4;
}

.stats {
  display: flex;
  gap: 12px;
  font-size: 0.7rem;
  color: #64748b;
  font-weight: 700;
}
</style>
