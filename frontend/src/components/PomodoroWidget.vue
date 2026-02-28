<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue';
import { usePomodoroStore } from '@/stores/pomodoroStore';
import { storeToRefs } from 'pinia';

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
  // 🆕 History View State
  isFlipped,
  selectedDate,
  historyRecords,
  calendarOpen,
  earliestDate,
  editingNoteId
} = storeToRefs(pomodoroStore);

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

function selectTime(minutes: number) {
  pomodoroStore.updateWorkMinutes(minutes);
}

function closeRuler() {
  isRulerOpen.value = false;
}

// 🆕 History Helpers
const weekDays = ['日', '一', '二', '三', '四', '五', '六'];
const weekDates = computed(() => pomodoroStore.getWeekDates(selectedDate.value));

function formatTime(dateStr: string) {
  const d = new Date(dateStr);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
}

function getDaySuffix(dateStr: string) {
  const today = pomodoroStore.formatDate(new Date());
  if (dateStr === today) return '今天';
  const yesterday = pomodoroStore.formatDate(new Date(Date.now() - 86400000));
  if (dateStr === yesterday) return '昨天';
  return '';
}

function getDisplayDate(dateStr: string) {
  const d = new Date(dateStr + 'T00:00:00');
  return `${d.getMonth() + 1}月${d.getDate()}日`;
}

function startEditNote(id: number, currentNote: string | null) {
  editingNoteId.value = id;
  noteInput.value = currentNote || '';
}

function saveNote(id: number) {
  pomodoroStore.updateSessionNote(id, noteInput.value);
}

function selectDate(date: string) {
  pomodoroStore.loadHistory(date);
}
</script>

<template>
  <div class="pomodoro-widget" :class="{ 'expanded': isExpanded }">
    <!-- Floating Button (Collapsed) -->
    <button 
      v-if="!isExpanded"
      class="pomodoro-toggle-btn neumorphic-btn"
      @click="toggleWidget"
      title="Pomodoro Timer"
    >
      <div class="timer-text">{{ displayTime }}</div>
    </button>

    <!-- Expanded Panel with 3D Flip -->
    <div v-if="isExpanded" class="card-container">
      <div class="card-inner" :class="{ 'flipped': isFlipped }">
        
        <!-- FRONT: Timer View -->
        <div class="card-face timer-front neumorphic-panel">
          <!-- Header -->
          <div class="panel-header">
            <div class="title" :class="currentState.toLowerCase()">
              <span>{{ currentState === 'WORK' ? 'FOCUS' : currentState === 'REST' ? 'RESTING' : 'READY' }}</span>
            </div>
            <div class="header-actions">
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
                'clickable': currentState === 'IDLE'
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
          <div class="controls">
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
          <div class="ruler-overlay neumorphic-panel" :class="{ 'open': isRulerOpen }">
            <div class="ruler-header">
              <span>Set Focus Duration</span>
              <button class="close-btn neumorphic-circle-btn" @click="closeRuler">✕</button>
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
            <button class="neumorphic-btn-accent done-btn" @click="closeRuler">DONE</button>
          </div>
        </div>

        <!-- BACK: History View -->
        <div class="card-face history-back neumorphic-panel">
          <!-- History Header -->
          <div class="panel-header">
            <div class="date-selector" @click="calendarOpen = !calendarOpen">
              <span class="date-main">{{ getDisplayDate(selectedDate) }}</span>
              <span class="date-sub">{{ getDaySuffix(selectedDate) }}</span>
              <svg class="chevron" :class="{ 'upside': calendarOpen }" xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6"></path></svg>
            </div>
            <div class="header-actions">
              <button class="icon-btn neumorphic-circle-btn small" @click="pomodoroStore.flipToTimer()" title="Back to Timer">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
              </button>
              <button class="icon-btn neumorphic-circle-btn small" @click="toggleWidget" title="Close">
                ✕
              </button>
            </div>
          </div>

          <!-- Week Row -->
          <div class="week-row">
            <div v-for="(day, idx) in weekDays" :key="idx" class="week-day">
              <span class="day-label">{{ day }}</span>
              <button 
                class="day-btn" 
                :class="{ 'active': weekDates[idx] === selectedDate }"
                @click="weekDates[idx] && selectDate(weekDates[idx] as string)"
              >
                {{ weekDates[idx] ? new Date(weekDates[idx] + 'T00:00:00').getDate() : '' }}
              </button>
            </div>
          </div>

          <!-- Timeline List -->
          <div class="history-list neumorphic-inset">
            <div v-if="historyRecords.length === 0" class="empty-state">
              无专注记录
            </div>
            <div v-for="record in historyRecords" :key="record.id" class="history-item">
              <div class="item-time">
                <span>{{ formatTime(record.created_at) }}</span>
                <div class="connector line"></div>
              </div>
              <div class="item-card neumorphic-inset">
                <div class="card-top">
                  <span class="tag-label">{{ record.tag.name }}</span>
                  <span class="duration-label">{{ record.duration }}m</span>
                </div>
                <!-- Note Section -->
                <div class="note-box">
                  <div v-if="editingNoteId === record.id" class="note-edit">
                    <input 
                      v-model="noteInput" 
                      @keyup.enter="saveNote(record.id)"
                      @blur="saveNote(record.id)"
                      placeholder="Add focus detail..." 
                      autoFocus
                    />
                  </div>
                  <div v-else class="note-display" @click="startEditNote(record.id, record.task)">
                    <span v-if="record.task" class="note-text">{{ record.task }}</span>
                    <span v-else class="note-placeholder">+ Add note...</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Calendar Overlay (Simplified for now) -->
          <div v-if="calendarOpen" class="calendar-overlay neumorphic-panel">
            <div class="overlay-msg">Calendar Picker Placeholder</div>
            <button class="neumorphic-btn-small" @click="calendarOpen = false">Close</button>
          </div>
        </div>

      </div>
    </div>

    <!-- Session Recovery Dialog -->
    <div v-if="showRecoveryDialog" class="recovery-overlay">
      <div class="recovery-dialog neumorphic-panel">
        <div class="recovery-title">SESSION RECOVERY</div>
        <p class="recovery-info">
          您有一个 <strong>{{ recoverySession?.duration }}分钟</strong> 的专注正在进行中
          <span v-if="recoverySession?.tag">({{ recoverySession.tag.name }})</span>
        </p>
        <div class="recovery-actions">
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

.history-back {
  transform: rotateY(180deg);
  gap: 16px; 
  padding: 20px 18px; /* Reduced side padding */
}

/* --- Neumorphic Primitives --- */
.neumorphic-panel {
  background: #161618;
  box-shadow: 10px 10px 20px #0c0c0d, -10px -10px 20px #202023;
  color: #d1d1d6;
  border: 1px solid rgba(255, 255, 255, 0.02);
}

.neumorphic-inset {
  background: #161618;
  box-shadow: inset 6px 6px 12px #0c0c0d, inset -6px -6px 12px #202023;
  border-radius: 16px;
}

.neumorphic-circle-btn {
  background: #161618;
  border: none;
  border-radius: 50%;
  box-shadow: 5px 5px 10px #0c0c0d, -5px -5px 10px #202023;
  color: #d1d1d6;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.neumorphic-circle-btn:active {
  box-shadow: inset 3px 3px 6px #0c0c0d, inset -3px -3px 6px #202023;
  transform: scale(0.96);
}

.neumorphic-circle-btn.small {
  width: 32px;
  height: 32px;
  font-size: 12px;
}

.neumorphic-btn-accent {
  background: #1e1e20;
  color: #ffffff;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.neumorphic-btn-small {
  background: #161618;
  border-radius: 10px;
  box-shadow: 3px 3px 6px #0c0c0d, -3px -3px 6px #202023;
  color: #8e8e93;
  border: none;
  cursor: pointer;
  padding: 8px 12px;
}

/* --- Shared Header Style --- */
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

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

.controls {
  display: flex;
  justify-content: center;
  gap: 32px;
  margin-bottom: 32px;
}

.play-btn { width: 60px; height: 60px; }
.stop-btn { width: 44px; height: 44px; color: #8e8e93; }

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

/* --- History View Special Styles --- */
.date-selector {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}

.date-main {
  font-size: 18px;
  font-weight: 600;
  color: #ffffff;
}

.date-sub {
  font-size: 14px;
  color: #8e8e93;
}

.chevron {
  transition: transform 0.3s;
  color: #48484a;
}
.chevron.upside { transform: rotate(180deg); }

.week-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 24px;
}

.week-day {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.day-label {
  font-size: 11px;
  color: #48484a;
}

.day-btn {
  width: 32px;
  height: 32px;
  background: transparent;
  border: none;
  font-weight: 500;
  font-size: 14px;
  color: #8e8e93;
  cursor: pointer;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.day-btn.active {
  background: #1e1e20;
  box-shadow: 2px 2px 5px rgba(0,0,0,0.4);
  color: #ffffff;
  border: 1px solid rgba(255,255,255,0.1);
}

.history-list {
  flex: 1;
  padding: 12px 6px; /* Reduced padding */
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  scrollbar-width: thin;
  scrollbar-color: #242427 transparent;
}

/* Custom Scrollbar for Chrome/Safari */
.history-list::-webkit-scrollbar {
  width: 4px;
}

.history-list::-webkit-scrollbar-track {
  background: transparent;
}

.history-list::-webkit-scrollbar-thumb {
  background: #242427;
  border-radius: 10px;
}

.history-list::-webkit-scrollbar-thumb:hover {
  background: #3a3a3c;
}

.history-item {
  display: flex;
  gap: 8px; /* Tighter gap between time and card */
}

.item-time {
  width: 38px; /* Narrower time column */
  font-size: 10px; /* Smaller time font */
  color: #8e8e93; /* Brightened from #48484a */
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 4px;
}

.connector {
  width: 1px;
  flex: 1;
  background: #3a3a3c; /* Brightened from #242427 */
  margin-top: 8px;
}

.item-card {
  flex: 1;
  padding: 8px 10px; /* Thinner padding */
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.card-top {
  display: flex;
  justify-content: space-between;
  font-size: 11px; /* Smaller font */
}

.tag-label {
  color: #ffffff;
  font-weight: 500;
}

.duration-label {
  color: #8e8e93; /* Brightened from #48484a */
}

.note-box {
  background: rgba(255,255,255,0.02);
  border-radius: 8px;
}

.note-display {
  padding: 8px;
  cursor: pointer;
}

.note-text {
  font-size: 11px;
  color: #d1d1d6; /* Brightened from #8e8e93 */
}

.note-placeholder {
  font-size: 11px;
  color: #636366; /* Brightened from #48484a */
}

.note-edit input {
  width: 100%;
  background: transparent;
  border: none;
  color: #ffffff;
  font-size: 12px;
  padding: 8px;
  outline: none;
}

.empty-state {
  text-align: center;
  color: #48484a;
  padding-top: 40px;
  font-style: italic;
  font-size: 13px;
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
  background: #161618 !important; /* Force dark background */
  color: #d1d1d6 !important;
  border: 1px solid rgba(255, 255, 255, 0.05);
  letter-spacing: 1px;
  box-shadow: 8px 8px 16px #0c0c0d, -8px -8px 16px #202023 !important;
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  cursor: pointer;
  padding: 0;
}

.pomodoro-toggle-btn:hover {
  transform: scale(1.08);
  box-shadow: 10px 10px 20px #0c0c0d, -10px -10px 20px #242427 !important;
  color: #ffffff !important;
}

.timer-text {
  font-family: 'Inter', sans-serif;
  letter-spacing: 0.5px;
}

/* Slide-up Overlays */
.ruler-overlay, .calendar-overlay {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  background: #1c1c1e;
  z-index: 100;
}

.ruler-overlay { height: 280px; transform: translateY(100%); transition: transform 0.4s; }
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
  width: 60px; /* Exact width needed for transform calculations */
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

.calendar-overlay {
  height: 350px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
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

.recovery-info {
  font-size: 13px;
  font-weight: 300;
  color: #8e8e93;
  margin: 0;
  line-height: 1.6;
}

.recovery-info strong {
  color: #d1d1d6;
  font-weight: 400;
}

.recovery-actions {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-top: 12px;
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
