<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue';
import { usePomodoroStore } from '@/stores/pomodoroStore';
import { useChatStore } from '@/stores/chatStore';
import { storeToRefs } from 'pinia';
import PomodoroRuler from './PomodoroRuler.vue';
import PomodoroHistory from './PomodoroHistory.vue';

const pomodoroStore = usePomodoroStore();
const { 
  isExpanded, 
  currentState, 
  isRunning, 
  displayTime, 
  progress, 
  currentCategoryId, 
  categories,
  isSuperFlow,
  workMinutes,
  showRecoveryDialog,
  recoverySession,
  isFlipped
} = storeToRefs(pomodoroStore);

const chatStore = useChatStore();
const { position: chatPosition } = storeToRefs(chatStore);

// Ruler state
const isRulerOpen = ref(false);
const rulerOptions = [15, 20, 25, 30, 35, 40, 45, 50, 55, 60];

// Note editing temp state
const noteInput = ref('');

onMounted(() => {
  pomodoroStore.loadCategories();
  pomodoroStore.checkOngoingSession();
});

function toggleWidget() {
  pomodoroStore.toggle();
}

function openRuler() {
  if (currentState.value === 'IDLE') {
    isRulerOpen.value = true;
  }
}

function closeRuler() {
  isRulerOpen.value = false;
}

</script>

<template>
  <div class="pomodoro-widget" :class="{ 'expanded': isExpanded, 'pomodoro-widget-right': chatPosition === 'left' }">
    <!-- Floating Button (Collapsed) -->
    <button 
      v-if="!isExpanded"
      class="pomodoro-toggle-btn neumorphic-btn"
      :class="{ 'super-flow-active': isSuperFlow }"
      @click="toggleWidget"
      title="Pomodoro Timer"
    >
      <div v-if="isSuperFlow" class="super-flow-ring">
        <div class="super-flow-ring-inner"></div>
      </div>
      <div class="timer-text">{{ displayTime }}</div>
    </button>

    <!-- Expanded Panel with 3D Flip -->
    <div v-if="isExpanded" class="card-container">
      <div class="card-inner" :class="{ 'flipped': isFlipped }">
        
        <!-- FRONT: Timer View -->
        <div class="card-face timer-front neumorphic-panel">
          <!-- Header -->
          <div class="flex justify-between items-center mb-6">
            <div class="title" :class="currentState.toLowerCase()">
              <span>{{ currentState === 'WORK' ? 'FOCUS' : currentState === 'REST' ? 'RESTING' : 'READY' }}</span>
            </div>
            <div class="flex gap-3">
              <button class="icon-btn neumorphic-circle-btn small" @click="pomodoroStore.flipToHistory()" title="History">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
              </button>
              <button class="icon-btn neumorphic-circle-btn small" @click="toggleWidget" title="Close">
                ✕
              </button>
            </div>
          </div>

          <!-- Main Display -->
          <div class="timer-display neumorphic-inset">
            <h1 
              class="time-main" 
              :class="{ 
                'blinking': isRunning && pomodoroStore.timeLeft === 0,
                'is-rest': currentState === 'REST',
                'clickable': currentState === 'IDLE',
                'text-super-flow': isSuperFlow && currentState !== 'REST'
              }"
              @click="openRuler"
            >
              {{ displayTime }}
            </h1>
            
            <!-- Super Flow Toggle -->
            <button 
              class="super-flow-toggle" 
              :class="{ 'active': isSuperFlow }"
              @click="pomodoroStore.toggleSuperFlow()"
              title="Super Flow Mode (Skip IDLE)"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
              </svg>
            </button>

            <div class="progress-bar-container neumorphic-inset">
              <div class="progress-bar" :class="{ 'rest-bar': currentState === 'REST' }" :style="{ width: `${progress}%` }"></div>
            </div>
          </div>

          <!-- Controls -->
          <div class="flex justify-center gap-8 mb-8">
            <button v-if="!isRunning && currentState !== 'REST'" class="neumorphic-circle-btn play-btn neumorphic-btn-accent" @click="pomodoroStore.startTimer()">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" stroke="none">
                <polygon points="5 3 19 12 5 21 5 3"></polygon>
              </svg>
            </button>
            <button v-else-if="isRunning" class="neumorphic-circle-btn pause-btn" @click="pomodoroStore.pauseTimer()">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                <rect x="6" y="4" width="4" height="16"></rect>
                <rect x="14" y="4" width="4" height="16"></rect>
              </svg>
            </button>
            <button class="neumorphic-circle-btn stop-btn" @click="pomodoroStore.forceStop()">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor" stroke="none">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
              </svg>
            </button>
          </div>

          <!-- Categories -->
          <div class="categories">
            <div class="chip-container grid-matrix">
              <button 
                v-for="cat in categories" 
                :key="cat.id"
                class="chip neumorphic-btn-small"
                :class="{ 'active': currentCategoryId === cat.id, 'disabled': currentState !== 'IDLE' }"
                @click="currentState === 'IDLE' && pomodoroStore.setCategory(cat.id)"
              >
                {{ cat.name }}
              </button>
            </div>
          </div>

          <!-- Ruler Overlay -->
          <PomodoroRuler :isOpen="isRulerOpen" @close="closeRuler" />
        </div>

        <!-- BACK: History View -->
        <PomodoroHistory @close="toggleWidget" />

      </div>
    </div>

    <!-- Session Recovery Dialog -->
    <div v-if="showRecoveryDialog" class="recovery-overlay">
      <div class="recovery-dialog neumorphic-panel">
        <div class="recovery-title">SESSION RECOVERY</div>
        <p class="text-[13px] font-light text-[#8e8e93] m-0 leading-relaxed">
          您有一个 <strong class="text-[#d1d1d6] font-normal">{{ recoverySession?.duration }}分钟</strong> 的专注正在进行中
          <span v-if="recoverySession?.tag">({{ recoverySession.tag.name }})</span>
        </p>
        <div class="flex justify-between gap-4 mt-3">
          <button class="neumorphic-btn-accent recovery-btn" @click="pomodoroStore.resumeSession()">
            继续计时
          </button>
          <button class="neumorphic-btn-small recovery-btn discard" @click="pomodoroStore.discardSession()">
            放弃
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Base App Styling */
.pomodoro-widget {
  position: fixed;
  bottom: 24px;
  left: 24px;
  z-index: 9998;
  font-family: 'Inter', 'SF Pro Text', -apple-system, BlinkMacSystemFont, sans-serif;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.pomodoro-widget-right {
  left: auto;
  right: 24px;
}

/* --- 3D Flip Container --- */
.card-container {
  width: 330px;
  height: 560px; /* Increased to accommodate content without cutting */
  perspective: 1200px;
}

.card-inner {
  position: relative;
  width: 100%;
  height: 100%;
  transition: transform 0.7s cubic-bezier(0.16, 1, 0.3, 1);
  transform-style: preserve-3d;
}

.card-inner.flipped {
  transform: rotateY(180deg);
}

.card-face {
  position: absolute;
  width: 100%;
  height: 100%;
  backface-visibility: hidden;
  display: flex;
  flex-direction: column;
  padding: 24px 28px;
  border-radius: 20px;
  box-sizing: border-box;
  overflow: hidden; /* CRITICAL: Clips the ruler and calendar overlays */
  gap: 28px; /* Restore the original rhythm */
}

/* Removed local Neumorphic Primitives - imported globally */

/* --- Shared Header Style --- */
.title {
  font-size: 12px;
  font-weight: 500;
  color: #8e8e93;
  letter-spacing: 4px;
}

/* --- Timer View Special Styles --- */
.timer-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 36px 0 28px 0;
  position: relative;
}

.time-main {
  font-size: 64px;
  font-weight: 200;
  letter-spacing: 6px;
  margin: 0;
}

.time-main.is-rest { color: #8ce196; }

.time-main.text-super-flow {
  color: #ffd60a;
  text-shadow: 0 0 15px rgba(255, 214, 10, 0.2);
}

.super-flow-toggle {
  background: transparent;
  border: none;
  color: #48484a;
  cursor: pointer;
  margin-bottom: 20px;
}

.super-flow-toggle.active { color: #ffd60a; }

.progress-bar-container {
  width: 80%;
  height: 3px;
  background: #0c0c0d;
}

.progress-bar {
  height: 100%;
  background: #ffffff;
}

.play-btn, .pause-btn { 
  width: 60px; 
  height: 60px; 
  flex-shrink: 0;
}
.stop-btn { 
  width: 44px; 
  height: 44px; 
  color: #8e8e93; 
  flex-shrink: 0;
}

.grid-matrix {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  width: 100%;
}

.chip {
  padding: 8px 4px;
  font-size: 11px;
  letter-spacing: 0.5px;
  width: 100%;
  text-align: center;
  border-radius: 10px;
  background: #161618;
  border: none;
  box-shadow: 3px 3px 6px #0c0c0d, -3px -3px 6px #202023;
  color: #8e8e93;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chip.active {
  background: #1e1e20;
  box-shadow: inset 2px 2px 4px rgba(0,0,0,0.5), 1px 1px 2px rgba(255,255,255,0.05);
  color: #ffffff;
  font-weight: 500;
}

.chip.disabled {
  opacity: 0.4;
  cursor: not-allowed;
  box-shadow: none;
}

/* Animations */
.blinking { animation: blink 1.5s infinite; }
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

/* Floating Button (Collapsed) */
.pomodoro-toggle-btn {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 300;
  font-size: 14px;
  background: #161618 !important;
  color: #d1d1d6 !important;
  border: 1px solid rgba(255, 255, 255, 0.05);
  letter-spacing: 1px;
  box-shadow: 8px 8px 16px #0c0c0d, -8px -8px 16px #202023 !important;
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  cursor: pointer;
  padding: 0;
  position: relative;
}

.pomodoro-toggle-btn:hover {
  transform: scale(1.08);
  box-shadow: 10px 10px 20px #0c0c0d, -10px -10px 20px #242427 !important;
  color: #ffffff !important;
}

.pomodoro-toggle-btn.super-flow-active {
  border-color: transparent;
}

.pomodoro-toggle-btn.super-flow-active .timer-text {
  color: #ffd60a !important;
  text-shadow: 0 0 10px rgba(255, 214, 10, 0.4);
  z-index: 2;
  position: relative;
}

.super-flow-ring {
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  border-radius: 50%;
  background: conic-gradient(from 0deg, transparent 0%, transparent 50%, rgba(255, 214, 10, 0.8) 100%);
  animation: spin 2.5s linear infinite;
  z-index: 1;
  pointer-events: none;
}

.super-flow-ring-inner {
  position: absolute;
  top: 2px;
  left: 2px;
  right: 2px;
  bottom: 2px;
  border-radius: 50%;
  background: #161618;
}

@keyframes spin {
  100% { transform: rotate(360deg); }
}

.timer-text {
  font-family: 'Inter', sans-serif;
  letter-spacing: 0.5px;
}


.recovery-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
}

.recovery-dialog {
  width: 330px;
  padding: 32px 28px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  text-align: center;
}

.recovery-title {
  font-size: 12px;
  font-weight: 500;
  color: #8e8e93;
  letter-spacing: 3px;
}

.recovery-btn {
  flex: 1;
  padding: 14px 0;
  font-size: 12px;
  font-weight: 400;
  letter-spacing: 1px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.recovery-btn.discard {
  color: #ff453a;
}
</style>

<style>
/* 
  Global Styles (Unscoped) 
  Required for Element Plus Popper which gets teleported to <body>
*/
.neu-popper.el-popper {
  z-index: 10000 !important; /* Force to show over Pomodoro widget */
  background: #1c1c1e !important;
  border: 1px solid rgba(255,255,255,0.05) !important;
  border-radius: 16px !important;
  box-shadow: 10px 10px 30px rgba(0,0,0,0.5) !important;
}

.neu-popper .el-select-dropdown__item {
  color: #8e8e93 !important;
  font-size: 13px !important;
}

.neu-popper .el-select-dropdown__item.is-selected {
  color: #ffffff !important;
  background: rgba(255,255,255,0.05) !important;
  font-weight: 600 !important;
}

.neu-popper .el-select-dropdown__item.is-hovering,
.neu-popper .el-select-dropdown__item:hover {
  background: rgba(255,255,255,0.03) !important;
}

.neu-popper .el-popper__arrow::before {
  background: #1c1c1e !important;
  border-color: rgba(255,255,255,0.05) !important;
}
</style>
