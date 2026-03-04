<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { usePomodoroStore } from '@/stores/pomodoroStore';
import { storeToRefs } from 'pinia';

const pomodoroStore = usePomodoroStore();
const { selectedDate, earliestDate } = storeToRefs(pomodoroStore);

const props = defineProps<{ isOpen: boolean }>();
const emit = defineEmits<{ (e: 'close'): void }>();

const todayStr = computed(() => Object.freeze(pomodoroStore.formatDate(new Date())) as string);

function isDateDisabled(dateStr: string) {
  const dateObj = new Date(dateStr + 'T00:00:00');
  const todayObj = new Date(todayStr.value + 'T00:00:00');
  const earliestObj = earliestDate.value ? new Date(earliestDate.value + 'T00:00:00') : null;
  
  if (dateObj > todayObj) return true;
  if (earliestObj && dateObj < earliestObj) return true;
  return false;
}

function handleDateClick(data: { day: string }) {
  if (!isDateDisabled(data.day)) {
    pomodoroStore.selectDateFromCalendar(data.day);
    emit('close');
  }
}

function goToToday() {
  const today = pomodoroStore.formatDate(new Date());
  pomodoroStore.loadHistory(today);
  emit('close');
}

const calendarValue = ref(new Date(selectedDate.value + 'T00:00:00'));

watch(selectedDate, (val) => {
  calendarValue.value = new Date(val + 'T00:00:00');
});

const currentYear = computed({
  get: () => calendarValue.value.getFullYear(),
  set: (val) => {
    const d = new Date(calendarValue.value);
    d.setFullYear(val);
    calendarValue.value = d;
  }
});

const currentMonth = computed({
  get: () => calendarValue.value.getMonth() + 1,
  set: (val) => {
    const d = new Date(calendarValue.value);
    d.setMonth(val - 1);
    calendarValue.value = d;
  }
});

const yearOptions = computed(() => {
  const current = new Date().getFullYear();
  const options = [];
  for (let i = current - 5; i <= current + 1; i++) options.push(i);
  return options;
});
</script>

<template>
  <Transition name="fade">
    <div v-show="isOpen" class="blur-backdrop" @click="emit('close')"></div>
  </Transition>

  <Transition name="slide-up">
    <div v-show="isOpen" class="calendar-overlay neumorphic-panel">
      <div class="calendar-header-row">
        <span class="overlay-title">SELECT DATE</span>
        <button class="icon-btn neumorphic-circle-btn small" @click="emit('close')">✕</button>
      </div>
      
      <div class="calendar-container-inner">
        <el-calendar v-model="calendarValue" class="custom-el-calendar">
          <template #header>
            <div class="select-controller">
              <el-select 
                v-model="currentYear" 
                size="small" 
                class="neu-select year-sel"
                popper-class="neu-popper"
                :teleported="true"
              >
                <el-option v-for="y in yearOptions" :key="y" :label="y + '年'" :value="y" />
              </el-select>
              <el-select 
                v-model="currentMonth" 
                size="small" 
                class="neu-select month-sel"
                popper-class="neu-popper"
                :teleported="true"
              >
                <el-option v-for="m in 12" :key="m" :label="m + '月'" :value="m" />
              </el-select>
              <button class="today-btn" @click.stop="goToToday">今天</button>
            </div>
          </template>
          <template #date-cell="{ data }">
            <div 
              class="neu-date-cell" 
              :class="{ 
                'is-active': data.day === selectedDate, 
                'is-today': data.day === todayStr,
                'is-disabled': isDateDisabled(data.day)
              }" 
              @click="handleDateClick(data)"
            >
              <span class="cell-num">{{ data.day.split('-')[2] }}</span>
            </div>
          </template>
        </el-calendar>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.blur-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(22, 22, 24, 0.4);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  z-index: 900;
  border-radius: 20px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(100%);
}

.calendar-overlay {
  height: 430px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  border-radius: 24px 24px 20px 20px;
  background: #1c1c1e !important;
  box-shadow: 0 -10px 40px rgba(0,0,0,0.8), inset 0 2px 2px rgba(255,255,255,0.05) !important;
  border-top: 1px solid rgba(255,255,255,0.08);
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 1000;
}

.calendar-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  margin-bottom: 12px;
}

.overlay-title {
  font-size: 10px;
  letter-spacing: 3px;
  color: #48484a;
  font-weight: 600;
  text-transform: uppercase;
}

.calendar-container-inner {
  flex: 1;
  width: 100%;
}

.select-controller {
  display: flex;
  gap: 12px;
  width: 100%;
  padding-bottom: 8px;
}

/* Custom el-calendar overrides */
.custom-el-calendar {
  background: transparent !important;
  border: none !important;
}

:deep(.el-calendar__header) {
  padding: 0 0 16px 0 !important;
  border-bottom: 1px solid rgba(255,255,255,0.03) !important;
}

:deep(.el-calendar__body) {
  padding: 0 !important;
}

:deep(.el-calendar-table) {
  width: 100% !important;
}

:deep(.el-calendar-table thead th) {
  padding: 12px 0 !important;
  color: #48484a !important;
  font-size: 10px !important;
  font-weight: 500 !important;
  text-transform: uppercase;
  letter-spacing: 1px;
}

:deep(.el-calendar-table td) {
  border: none !important;
  padding: 0 !important;
}

:deep(.el-calendar-table .el-calendar-day) {
  height: 40px !important;
  padding: 0 !important;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent !important;
}

.neu-date-cell {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  color: #8e8e93;
  font-size: 13px;
  position: relative;
}

.neu-date-cell:hover {
  background: rgba(255,255,255,0.05) !important;
  color: #ffffff;
}

.neu-date-cell.is-today::after {
  content: '';
  position: absolute;
  bottom: 2px;
  width: 4px;
  height: 4px;
  background: #77bf6c;
  border-radius: 50%;
}

.neu-date-cell.is-disabled {
  opacity: 0.2;
  cursor: not-allowed;
}

.neu-date-cell.is-disabled:hover {
  background: transparent !important;
  color: #8e8e93;
}

.neu-date-cell.is-active {
  background: #161618 !important;
  box-shadow: 4px 4px 8px #0c0c0d, -4px -4px 8px #202023;
  color: #ffffff;
  font-weight: 700;
  transform: scale(1.1);
  border: 1px solid rgba(255,255,255,0.05);
}

:deep(.el-calendar-table td.prev), :deep(.el-calendar-table td.next) {
  opacity: 0.15;
}

:deep(.el-calendar-table td.is-selected) {
  background-color: transparent !important;
}

/* Select overrides for neumorphic look */
.neu-select :deep(.el-select__wrapper) {
  background-color: #161618 !important;
  box-shadow: inset 4px 4px 8px #0c0c0d, inset -4px -4px 8px #202023 !important;
  border: none !important;
  border-radius: 12px !important;
  padding: 4px 12px !important;
  height: 36px !important;
}

.neu-select :deep(.el-select__placeholder) {
  color: #ffffff !important;
  font-size: 13px !important;
  font-weight: 500 !important;
}

.neu-select :deep(.el-select__caret) {
  color: #8e8e93 !important;
}

.year-sel { width: 105px; }
.month-sel { width: 85px; }

.today-btn {
  background: #161618;
  border: none;
  box-shadow: 3px 3px 6px #0c0c0d, -3px -3px 6px #202023;
  color: #8ce196;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 500;
  padding: 0 16px;
  cursor: pointer;
  height: 36px;
  flex-shrink: 0;
  margin-left: auto;
  transition: all 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.today-btn:active {
  box-shadow: inset 2px 2px 4px #0c0c0d, inset -2px -2px 4px #202023;
  transform: scale(0.96);
}
</style>
