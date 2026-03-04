<script setup lang="ts">
import { usePomodoroStore } from '@/stores/pomodoroStore';
import { storeToRefs } from 'pinia';

const pomodoroStore = usePomodoroStore();
const { workMinutes } = storeToRefs(pomodoroStore);

defineProps<{ isOpen: boolean }>();
const emit = defineEmits<{ (e: 'close'): void }>();

const rulerOptions = [15, 20, 25, 30, 35, 40, 45, 50, 55, 60];

function selectTime(minutes: number) {
  pomodoroStore.updateWorkMinutes(minutes);
}
</script>

<template>
  <div class="ruler-overlay neumorphic-panel" :class="{ 'open': isOpen }">
    <div class="ruler-header">
      <span>Set Focus Duration</span>
      <button class="close-btn neumorphic-circle-btn" @click="emit('close')">✕</button>
    </div>
    <div class="ruler-viewport">
      <div class="ruler-pointer">▼</div>
      <div class="ruler-track" :style="{ transform: `translateX(-${(rulerOptions.indexOf(workMinutes) * 60) + 30}px)` }">
        <div v-for="time in rulerOptions" :key="time" class="ruler-item" :class="{ 'selected': workMinutes === time }" @click="selectTime(time)">
          <div class="ruler-tick"></div>
          <span class="ruler-label">{{ time }}</span>
        </div>
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
  transition: transform 0.4s;
}
.ruler-overlay.open { transform: translateY(0); }

.ruler-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 28px;
  font-weight: 500;
  color: #8e8e93;
}

.close-btn {
  width: 32px;
  height: 32px;
  font-size: 14px;
}

.ruler-viewport {
  position: relative;
  width: 100%;
  height: 120px;
  display: flex;
  align-items: center;
  overflow: hidden;
  mask-image: linear-gradient(to right, transparent, black 20%, black 80%, transparent);
  -webkit-mask-image: linear-gradient(to right, transparent, black 20%, black 80%, transparent);
}

.ruler-pointer {
  position: absolute;
  left: 50%;
  top: 10px;
  transform: translateX(-50%);
  color: #ffffff;
  z-index: 2;
  font-size: 12px;
}

.ruler-track {
  display: flex;
  position: absolute;
  left: 50%;
  transition: transform 0.3s cubic-bezier(0.25, 1, 0.5, 1);
  align-items: center;
}

.ruler-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 60px;
  flex-shrink: 0;
  cursor: pointer;
  gap: 12px;
}

.ruler-tick {
  width: 2px;
  height: 24px;
  background: #3a3a3c;
  border-radius: 1px;
  transition: all 0.2s;
}

.ruler-item.selected .ruler-tick {
  height: 40px;
  background: #ffffff;
}

.ruler-label {
  font-size: 16px;
  font-weight: 600;
  color: #48484a;
  transition: all 0.2s;
}

.ruler-item.selected .ruler-label {
  color: #ffffff;
  font-size: 20px;
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
