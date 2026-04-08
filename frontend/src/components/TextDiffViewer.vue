<template>
  <div 
    :class="['diff-container outline-none', theme === 'dark' ? 'theme-dark' : 'theme-light']" 
    tabindex="0" 
    @keydown="handleKeydown"
  >
    <TransitionGroup name="diff-shift" tag="div" class="diff-viewer p-4 leading-relaxed relative">
      <span
        v-for="part in interactiveDiffs"
        :key="part.id"
        v-show="isVisible(part)"
        :class="[
          getClass(part), 
          { 'ring-2 ring-blue-400 z-10': activeTokenId === part.id }
        ]"
        @click.stop="setActiveToken(part)"
        @mouseenter="enableActions ? hoveredTokenId = part.id : null"
        @mouseleave="enableActions ? hoveredTokenId = null : null"
      >
        {{ part.value }}

        <div
          v-if="enableActions && part.resolution === 'pending' && (part.added || part.removed) && (hoveredTokenId === part.id || activeTokenId === part.id)"
          class="action-popup"
        >
          <button @click.stop="handleInteraction(part, true)" class="btn-accept" title="Accept (Y)">✓</button>
          <button @click.stop="handleInteraction(part, false)" class="btn-reject" title="Reject (N)">✕</button>
        </div>
      </span>
    </TransitionGroup>

    <p v-if="enableActions" class="text-xs tip-text mt-4 px-4 select-none">
      💡 Tip: Hover to use buttons, or click a highlighted word and press <b>Y</b> to accept / <b>N</b> to reject.
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount } from 'vue';
import * as Diff from 'diff';

interface Props {
  originalText?: string;
  polishedText?: string;
  theme?: 'light' | 'dark';
  enableActions?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  originalText: "",
  polishedText: "",
  theme: "light",
  enableActions: false
});

const interactiveDiffs = ref<any[]>([]);
const activeTokenId = ref<string | null>(null);
const hoveredTokenId = ref<string | null>(null);

watch(() => [props.originalText, props.polishedText], () => {
  if (!props.originalText || !props.polishedText) {
    interactiveDiffs.value = [];
    return;
  }
  
  const rawDiffs = Diff.diffWordsWithSpace(props.originalText, props.polishedText);
  
  interactiveDiffs.value = rawDiffs.map((part, index) => ({
    ...part,
    id: `diff_${index}_${Date.now()}`,
    resolution: 'pending' // 'pending' | 'accepted' | 'rejected'
  }));
}, { immediate: true });

const setActiveToken = (part: any) => {
  if (!props.enableActions) return;
  
  if (part.resolution === 'pending' && (part.added || part.removed)) {
    activeTokenId.value = part.id;
  } else {
    activeTokenId.value = null;
  }
};

const handleKeydown = (e: KeyboardEvent) => {
  if (!props.enableActions || !activeTokenId.value) return;

  const part = interactiveDiffs.value.find(p => p.id === activeTokenId.value);
  if (!part) return;

  if (e.key.toLowerCase() === 'y' || e.key === 'Enter') {
    handleInteraction(part, true);
  } else if (e.key.toLowerCase() === 'n' || e.key === 'Backspace' || e.key === 'Delete') {
    handleInteraction(part, false);
  }
};

const handleClickOutside = () => {
  activeTokenId.value = null;
};

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
});

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside);
});

const handleInteraction = (part: any, accept: boolean) => {
  if (!props.enableActions) return;
  if (!part.added && !part.removed) return;
  if (part.resolution !== 'pending') return;

  part.resolution = accept ? 'accepted' : 'rejected';
  
  if (activeTokenId.value === part.id) {
    activeTokenId.value = null;
    hoveredTokenId.value = null;
  }
};

const isVisible = (part: any) => {
  if (!props.enableActions) return true; // Show all if actions disabled (e.g., Daily Phrases)
  if (part.resolution === 'pending') return true;
  if (part.added) return part.resolution === 'accepted';
  if (part.removed) return part.resolution === 'rejected';
  return true;
};

const getClass = (part: any) => {
  if (!part.added && !part.removed) return 'unchanged-text';
  if (props.enableActions && part.resolution !== 'pending') {
    return 'unchanged-text transition-colors duration-300';
  }

  return part.added 
    ? 'added-text relative inline-block' 
    : 'removed-text relative inline-block text-decoration-line-through';
};
</script>

<style scoped>
/* --- Theme Variables --- */
.theme-light {
  --color-unchanged: #334155;
  --bg-added: #d1fae5;
  --color-added: #059669;
  --bg-removed: #fee2e2;
  --color-removed: #ef4444;
  --bg-popup: #1e293b;
  --color-popup-icon: #94a3b8;
  --color-tip: #94a3b8;
}

.theme-dark {
  --color-unchanged: #d1d5db;
  --bg-added: rgba(34, 197, 94, 0.2);
  --color-added: #4ade80;
  --bg-removed: rgba(239, 68, 68, 0.2);
  --color-removed: #f87171;
  --bg-popup: #334155;
  --color-popup-icon: #cbd5e1;
  --color-tip: #64748b;
}

/* --- Base Styles --- */
.diff-container {
  width: 100%;
  border-radius: 12px;
}

.diff-viewer {
  font-family: 'Inter', sans-serif;
  white-space: pre-wrap;
  font-size: 1rem;
}

.tip-text {
  color: var(--color-tip);
}

.added-text {
  background-color: var(--bg-added);
  color: var(--color-added);
  border-radius: 3px;
  padding: 2px 4px;
  margin: 0 2px;
  font-weight: 500;
}

.removed-text {
  background-color: var(--bg-removed);
  color: var(--color-removed);
  text-decoration: line-through;
  border-radius: 3px;
  padding: 2px 4px;
  margin: 0 2px;
  opacity: 0.8;
}

.unchanged-text {
  color: var(--color-unchanged);
}

.text-decoration-line-through {
  text-decoration: line-through;
}

/* --- Floating Action Menu --- */
.action-popup {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 4px;
  background: var(--bg-popup);
  padding: 4px 6px;
  border-radius: 6px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  z-index: 50;
  margin-bottom: 6px;
}

.action-popup::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  margin-left: -5px;
  border-width: 5px;
  border-style: solid;
  border-color: var(--bg-popup) transparent transparent transparent;
}

.btn-accept, .btn-reject {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 14px;
  color: var(--color-popup-icon);
  transition: all 0.2s ease;
}

.btn-accept:hover {
  background: #22c55e;
  color: white;
}

.btn-reject:hover {
  background: #ef4444;
  color: white;
}

/* --- Vue TransitionGroup CSS --- */
.diff-shift-move,
.diff-shift-enter-active,
.diff-shift-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.diff-shift-enter-from,
.diff-shift-leave-to {
  opacity: 0;
  transform: scaleY(0.8);
  padding: 0; 
  margin: 0;
}

.diff-shift-leave-active {
  position: absolute; 
}
</style>
