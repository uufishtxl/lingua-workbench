<script setup lang="ts">
import { ref, computed } from 'vue';
import { usePomodoroStore } from '@/stores/pomodoroStore';
import { storeToRefs } from 'pinia';
import PomodoroCalendar from './PomodoroCalendar.vue';

const pomodoroStore = usePomodoroStore();
const {
  selectedDate,
  historyRecords,
  calendarOpen,
  earliestDate,
  editingNoteId
} = storeToRefs(pomodoroStore);

const emit = defineEmits<{ (e: 'close'): void }>();

// Note editing temp state
const noteInput = ref('');

// 🆕 History Helpers
const weekDays = ['日', '一', '二', '三', '四', '五', '六'];
const weekDates = computed(() => pomodoroStore.getWeekDates(selectedDate.value));

const todayStr = computed(() => Object.freeze(pomodoroStore.formatDate(new Date())) as string);

function formatTime(dateStr: string) {
  const d = new Date(dateStr);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
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

function goToToday() {
  const today = pomodoroStore.formatDate(new Date());
  selectDate(today);
  calendarOpen.value = false;
}

// 🆕 Week Nav / Calendar Logic
function isDateDisabled(dateStr: string) {
  const dateObj = new Date(dateStr + 'T00:00:00');
  const todayObj = new Date(todayStr.value + 'T00:00:00');
  const earliestObj = earliestDate.value ? new Date(earliestDate.value + 'T00:00:00') : null;
  
  if (dateObj > todayObj) return true;
  if (earliestObj && dateObj < earliestObj) return true;
  return false;
}

const canPrevWeek = computed(() => {
  if (!earliestDate.value || !weekDates.value[0]) return true;
  const currentWeekStart = new Date(weekDates.value[0] + 'T00:00:00');
  const earliestD = new Date(earliestDate.value + 'T00:00:00');
  return currentWeekStart > earliestD;
});

const canNextWeek = computed(() => {
  if (!weekDates.value[6]) return true;
  const currentWeekEnd = new Date(weekDates.value[6] + 'T00:00:00');
  const todayD = new Date(todayStr.value + 'T00:00:00');
  return currentWeekEnd < todayD; 
});

function prevWeek() {
  if (!canPrevWeek.value) return;
  const newDate = new Date(selectedDate.value + 'T00:00:00');
  newDate.setDate(newDate.getDate() - 7);
  selectDate(pomodoroStore.formatDate(newDate));
}

function nextWeek() {
  if (!canNextWeek.value) return;
  const newDate = new Date(selectedDate.value + 'T00:00:00');
  newDate.setDate(newDate.getDate() + 7);
  
  const todayObj = new Date(todayStr.value + 'T00:00:00');
  if (newDate > todayObj) {
    selectDate(todayStr.value);
  } else {
    selectDate(pomodoroStore.formatDate(newDate));
  }
}
</script>

<template>
  <div class="card-face history-back neumorphic-panel">
    <!-- History Header -->
    <div class="panel-header">
      <div class="date-selector" @click="calendarOpen = !calendarOpen">
        <span class="date-main">{{ getDisplayDate(selectedDate) }}</span>
        <button 
          v-if="selectedDate !== todayStr" 
          class="shortcut-today-btn" 
          @click.stop="goToToday"
        >
          回到今天
        </button>
        <svg class="chevron" :class="{ 'upside': calendarOpen }" xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6"></path></svg>
      </div>
      <div class="header-actions">
        <button class="icon-btn neumorphic-circle-btn small" @click="pomodoroStore.flipToTimer()" title="Back to Timer">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
        </button>
        <button class="icon-btn neumorphic-circle-btn small" @click="emit('close')" title="Close">
          ✕
        </button>
      </div>
    </div>

    <!-- Week Row Nav -->
    <div class="week-nav-row">
      <button class="nav-arrow" :disabled="!canPrevWeek" @click="prevWeek">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
      </button>
      <div class="week-row">
        <div v-for="(day, idx) in weekDays" :key="idx" class="week-day">
          <span class="day-label">{{ day }}</span>
          <button 
            class="day-btn" 
            :class="{ 'active': weekDates[idx] === selectedDate }"
            :disabled="isDateDisabled(weekDates[idx] as string)"
            @click="weekDates[idx] && !isDateDisabled(weekDates[idx] as string) && selectDate(weekDates[idx] as string)"
          >
            {{ weekDates[idx] ? new Date(weekDates[idx] + 'T00:00:00').getDate() : '' }}
          </button>
        </div>
      </div>
      <button class="nav-arrow" :disabled="!canNextWeek" @click="nextWeek">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
      </button>
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

    <!-- Calendar Overlay & Blur -->
    <PomodoroCalendar :isOpen="calendarOpen" @close="calendarOpen = false" />
  </div>
</template>

<style scoped>
/* Card Face Setup */
.card-face {
  position: absolute;
  width: 100%;
  height: 100%;
  backface-visibility: hidden;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  overflow: hidden; 
}
.history-back {
  transform: rotateY(180deg);
  gap: 16px; 
  padding: 20px 18px; 
  border-radius: 20px;
}

/* --- Shared Header Style --- */
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px; /* Adjusted to fit gap */
}

.header-actions {
  display: flex;
  gap: 12px;
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

.shortcut-today-btn {
  background: #1e1e20;
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: 8px;
  color: #8e8e93;
  font-size: 11px;
  padding: 4px 8px;
  margin-left: 4px;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 2px 2px 4px #0c0c0d, -2px -2px 4px #202023;
}

.shortcut-today-btn:active {
  box-shadow: inset 1px 1px 2px #0c0c0d, inset -1px -1px 2px #202023;
  transform: scale(0.96);
}

.chevron {
  transition: transform 0.3s;
  color: #48484a;
}
.chevron.upside { transform: rotate(180deg); }

.week-nav-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.nav-arrow {
  background: transparent;
  border: none;
  color: #48484a;
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s;
}

.nav-arrow:hover:not(:disabled) {
  background: #1e1e20;
  color: #ffffff;
  box-shadow: 2px 2px 5px rgba(0,0,0,0.4);
}

.nav-arrow:disabled {
  opacity: 0.2;
  cursor: not-allowed;
}

.week-row {
  display: flex;
  flex: 1;
  justify-content: space-evenly;
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

.day-btn:disabled {
  opacity: 0.2;
  cursor: not-allowed;
  pointer-events: none;
}

.history-list {
  flex: 1;
  padding: 12px 6px; 
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
  gap: 8px; 
}

.item-time {
  width: 38px; 
  font-size: 10px; 
  color: #8e8e93; 
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 4px;
}

.connector {
  width: 1px;
  flex: 1;
  background: #3a3a3c; 
  margin-top: 8px;
}

.item-card {
  flex: 1;
  padding: 8px 10px; 
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.card-top {
  display: flex;
  justify-content: space-between;
  font-size: 11px; 
}

.tag-label {
  color: #ffffff;
  font-weight: 500;
}

.duration-label {
  color: #8e8e93; 
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
  color: #d1d1d6; 
}

.note-placeholder {
  font-size: 11px;
  color: #636366; 
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
</style>
