<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue';
import { usePomodoroStore } from '@/stores/pomodoroStore';
import { storeToRefs } from 'pinia';

const pomodoroStore = usePomodoroStore();
const { workMinutes } = storeToRefs(pomodoroStore);

const props = defineProps<{ isOpen: boolean }>();
const emit = defineEmits<{ (e: 'close'): void }>();

const rulerViewport = ref<HTMLElement | null>(null);
const rulerTrack = ref<HTMLElement | null>(null);

const rulerOptions = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 90, 120];
const ITEM_WIDTH = 60;

// Update store based on scroll position
function handleScroll() {
  if (!rulerViewport.value) return;
  const scrollLeft = rulerViewport.value.scrollLeft;
  const index = Math.round(scrollLeft / ITEM_WIDTH);
  if (index >= 0 && index < rulerOptions.length) {
    const newVal = rulerOptions[index];
    if (newVal !== workMinutes.value) {
      pomodoroStore.updateWorkMinutes(newVal);
    }
  }
}

// Sync scroll position when workMinutes changes externally or on open
function syncScroll(behavior: ScrollBehavior = 'smooth') {
  if (!rulerViewport.value) return;
  const index = rulerOptions.indexOf(workMinutes.value);
  if (index !== -1) {
    rulerViewport.value.scrollTo({
      left: index * ITEM_WIDTH,
      behavior
    });
  }
}

watch(() => props.isOpen, (open) => {
  if (open) {
    nextTick(() => syncScroll('auto'));
  }
});

function selectTime(minutes: number) {
  pomodoroStore.updateWorkMinutes(minutes);
  syncScroll();
}
</script>

<template>
  <div class="ruler-overlay neumorphic-panel" :class="{ 'open': isOpen }">
    <div class="ruler-header">
      <span>Duration (min)</span>
      <button class="close-btn neumorphic-circle-btn" @click="emit('close')">✕</button>
    </div>

    <div class="ruler-viewport-container">
      <div class="ruler-pointer">▼</div>
      <div 
        ref="rulerViewport" 
        class="ruler-viewport" 
        @scroll="handleScroll"
      >
        <div class="ruler-spacer"></div>
        <div class="ruler-track">
          <div 
            v-for="time in rulerOptions" 
            :key="time" 
            class="ruler-item" 
            :class="{ 'selected': workMinutes === time }" 
            @click="selectTime(time)"
          >
            <div class="ruler-tick"></div>
            <span class="ruler-label">{{ time }}</span>
          </div>
        </div>
        <div class="ruler-spacer"></div>
      </div>
    </div>

    <button class="neumorphic-btn-accent done-btn" @click="emit('close')">DONE</button>
  </div>
</template>

<style scoped>
.ruler-overlay {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  background: #1c1c1e;
  z-index: 100;
  height: 280px; 
  transform: translateY(100%); 
  transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 -10px 40px rgba(0,0,0,0.6);
}
.ruler-overlay.open { transform: translateY(0); }

.ruler-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 28px 12px 28px;
  font-size: 13px;
  font-weight: 500;
  color: #8e8e93;
  letter-spacing: 2px;
  text-transform: uppercase;
}

.close-btn {
  width: 32px;
  height: 32px;
  font-size: 14px;
}

.ruler-viewport-container {
  position: relative;
  width: 100%;
  height: 140px;
  margin-top: 10px;
}

.ruler-pointer {
  position: absolute;
  left: 50%;
  top: -5px;
  transform: translateX(-50%);
  color: #ffffff;
  z-index: 10;
  font-size: 10px;
  pointer-events: none;
}

.ruler-viewport {
  width: 100%;
  height: 100%;
  overflow-x: auto;
  overflow-y: hidden;
  display: flex;
  align-items: center;
  scroll-snap-type: x mandatory;
  scroll-behavior: smooth;
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE/Edge */
}

.ruler-viewport::-webkit-scrollbar {
  display: none; /* Chrome/Safari */
}

.ruler-spacer {
  width: 50%;
  flex-shrink: 0;
}

.ruler-track {
  display: flex;
  height: 100%;
  align-items: center;
  flex-shrink: 0;
}

.ruler-item {
  scroll-snap-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 60px;
  height: 100%;
  flex-shrink: 0;
  cursor: pointer;
  gap: 12px;
  user-select: none;
}

.ruler-tick {
  width: 2px;
  height: 20px;
  background: #3a3a3c;
  border-radius: 1px;
  transition: all 0.2s;
}

.ruler-item.selected .ruler-tick {
  height: 40px;
  background: var(--accent-color, #ffd60a);
}

.ruler-label {
  font-size: 14px;
  font-weight: 600;
  color: #48484a;
  transition: all 0.2s;
}

.ruler-item.selected .ruler-label {
  color: #ffffff;
  font-size: 22px;
  transform: translateY(-2px);
}

.done-btn {
  width: calc(100% - 56px);
  margin: 0 28px 24px 28px;
  padding: 16px 0;
  border-radius: 12px;
  font-weight: 600;
  letter-spacing: 2px;
  font-size: 14px;
  position: absolute;
  bottom: 0;
  cursor: pointer;
}
</style>
