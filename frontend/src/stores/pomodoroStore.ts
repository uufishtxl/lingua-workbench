import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { timerApi, type PomodoroTag, type Pomodoro } from '../api/timerApi';

export type PomodoroState = 'IDLE' | 'WORK' | 'REST';

export const usePomodoroStore = defineStore('pomodoro', () => {
    // UI State
    const isExpanded = ref(false);

    // Core State Machine
    const currentState = ref<PomodoroState>('IDLE');
    const isRunning = ref(false); // Indicates if the timer is actively counting down

    // Settings
    const workMinutes = ref(40);
    const restMinutes = ref(5);
    const timeLeft = ref(workMinutes.value * 60);
    const isSuperFlow = ref(false); // Skip IDLE mode after REST

    // Categories
    const categories = ref<PomodoroTag[]>([
        // Fallback or Initial Categories
        { id: 1, name: '未分类', order: 0 }
    ]);
    const currentCategoryId = ref(categories.value[0]?.id ?? 1);

    // Sessions history (in-memory for now)
    const sessions = ref<{ categoryId: number, duration: number, date: Date }[]>([]);

    // Timer ID for setInterval
    const timerId = ref<number | null>(null);

    // 🆕 Real-time Sync: 当前活跃会话的后端 ID
    const activeSessionId = ref<number | null>(null);

    // 🆕 Session Recovery: 弹窗控制
    const showRecoveryDialog = ref(false);
    const recoverySession = ref<Pomodoro | null>(null);

    // 🆕 History View State
    const isFlipped = ref(false);
    const selectedDate = ref(formatDate(new Date()));
    const historyRecords = ref<Pomodoro[]>([]);
    const calendarOpen = ref(false);
    const earliestDate = ref<string | null>(null);
    const editingNoteId = ref<number | null>(null);

    // Computed
    const displayTime = computed(() => {
        const minutes = Math.floor(timeLeft.value / 60);
        const seconds = timeLeft.value % 60;
        return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    });

    const progress = computed(() => {
        const totalMinutes = currentState.value === 'REST' ? restMinutes.value : workMinutes.value;
        const totalSeconds = totalMinutes * 60;
        return ((totalSeconds - timeLeft.value) / totalSeconds) * 100;
    });

    // Audio Helpers
    function playAudioTone(frequency = 440, type: OscillatorType = 'sine', duration = 0.5) {
        try {
            const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
            if (!AudioContext) return;
            const ctx = new AudioContext();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();

            osc.type = type;
            osc.frequency.setValueAtTime(frequency, ctx.currentTime);

            gain.gain.setValueAtTime(0.1, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);

            osc.connect(gain);
            gain.connect(ctx.destination);

            osc.start();
            osc.stop(ctx.currentTime + duration);
        } catch (e) { /* ignore audio errors in unsupported environments */ }
    }

    // Actions
    async function loadCategories() {
        try {
            const tags: PomodoroTag[] = await timerApi.getTags();
            if (tags && tags.length > 0) {
                categories.value = tags;

                // If the currentCategoryId isn't in the new list, reset it
                if (!tags.find(t => t.id === currentCategoryId.value) && tags.length > 0) {
                    currentCategoryId.value = tags[0]?.id ?? currentCategoryId.value;
                }
            }
        } catch (error) {
            console.error('Failed to load Pomodoro Categories:', error);
        }
    }

    /**
     * 🆕 页面加载时调用：检查是否有未完成的会话
     * 如果有，弹出恢复对话框让用户选择继续或放弃
     */
    async function checkOngoingSession() {
        try {
            const ongoing = await timerApi.getOngoing();
            if (ongoing) {
                recoverySession.value = ongoing;
                showRecoveryDialog.value = true;
            }
        } catch (error) {
            console.error('Failed to check ongoing session:', error);
        }
    }

    /**
     * 🆕 用户选择恢复进行中的会话
     * 根据后端记录的 created_at 和 duration 计算剩余时间
     */
    function resumeSession() {
        const session = recoverySession.value;
        if (!session) return;

        activeSessionId.value = session.id;
        workMinutes.value = session.duration;
        currentCategoryId.value = session.tag.id;

        // 计算已经过了多少秒
        const startTime = new Date(session.created_at).getTime();
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        const totalSeconds = session.duration * 60;
        const remaining = Math.max(0, totalSeconds - elapsed);

        if (remaining > 0) {
            timeLeft.value = remaining;
            currentState.value = 'WORK';
            isExpanded.value = true;
            startTimer();
        } else {
            // 时间已经过了，直接标记为完成
            completeCurrentSession();
        }

        showRecoveryDialog.value = false;
        recoverySession.value = null;
    }

    /**
     * 🆕 用户选择放弃进行中的会话
     */
    async function discardSession() {
        const session = recoverySession.value;
        if (session) {
            try {
                await timerApi.interruptPomodoro(session.id);
            } catch (error) {
                console.error('Failed to interrupt stale session:', error);
            }
        }
        showRecoveryDialog.value = false;
        recoverySession.value = null;
    }

    function toggle() {
        isExpanded.value = !isExpanded.value;
    }

    function toggleSuperFlow() {
        isSuperFlow.value = !isSuperFlow.value;
    }

    function updateWorkMinutes(minutes: number) {
        if (currentState.value === 'IDLE') {
            workMinutes.value = minutes;
            timeLeft.value = minutes * 60;
        }
    }

    /**
     * 🔄 改造：按下开始键时，先向后端发 POST 创建记录
     */
    async function startTimer() {
        if (isRunning.value) return;

        if (currentState.value === 'IDLE') {
            currentState.value = 'WORK';
            timeLeft.value = workMinutes.value * 60;

            // 🆕 向后端发 POST，拿到 session ID
            try {
                const session = await timerApi.startPomodoro({
                    tag_id: currentCategoryId.value,
                    duration: workMinutes.value
                });
                activeSessionId.value = session.id;
            } catch (error) {
                console.error('Failed to start Pomodoro session on backend:', error);
                // 后端失败也不阻塞前端计时（降级为本地模式）
            }
        }

        const expectedEndTime = Date.now() + timeLeft.value * 1000;
        isRunning.value = true;

        // Use 200ms interval for smoother UI tracking, calculate absolute remaining time
        timerId.value = window.setInterval(() => {
            const now = Date.now();
            const remaining = Math.max(0, Math.round((expectedEndTime - now) / 1000));

            if (remaining <= 0) {
                timeLeft.value = 0;
                pauseTimer(); // Fix: prevent multiple triggers during edge cases
                handleTimerComplete();
            } else {
                if (timeLeft.value !== remaining) {
                    timeLeft.value = remaining;
                }
            }
        }, 200);
    }

    function pauseTimer() {
        isRunning.value = false;
        if (timerId.value) {
            clearInterval(timerId.value);
            timerId.value = null;
        }
    }

    /**
     * 🔄 改造：强制停止时，向后端发 PATCH 标记为中断
     */
    async function forceStop() {
        pauseTimer();

        // 🆕 如果有活跃会话且在 WORK 状态，通知后端中断
        if (activeSessionId.value && currentState.value === 'WORK') {
            try {
                await timerApi.interruptPomodoro(activeSessionId.value);
            } catch (error) {
                console.error('Failed to interrupt Pomodoro on backend:', error);
            }
        }

        activeSessionId.value = null;
        currentState.value = 'IDLE';
        timeLeft.value = workMinutes.value * 60;
    }

    /**
     * 🆕 内部方法：完成当前会话
     */
    async function completeCurrentSession() {
        if (activeSessionId.value) {
            try {
                const saved = await timerApi.completePomodoro(activeSessionId.value);
                sessions.value.push({
                    categoryId: saved.tag.id,
                    duration: saved.duration,
                    date: new Date(saved.created_at || Date.now())
                });
            } catch (err) {
                console.error("Failed to sync Pomodoro completion to backend", err);
            }
            activeSessionId.value = null;
        }
    }

    function handleTimerComplete() {
        pauseTimer();

        if (currentState.value === 'WORK') {
            // 🔄 改造：发 PATCH 完成会话（异步，不阻塞 UI）
            completeCurrentSession();

            // Transition to REST immediately
            currentState.value = 'REST';
            timeLeft.value = restMinutes.value * 60;
            playAudioTone(880, 'sine', 1.0); // Gentle chime for rest start
            startTimer(); // auto-start rest

        } else if (currentState.value === 'REST') {
            playAudioTone(440, 'triangle', 1.5); // End of rest tune

            if (isSuperFlow.value) {
                // Skip IDLE, dive straight back to WORK
                currentState.value = 'WORK';
                timeLeft.value = workMinutes.value * 60;
                startTimer();
            } else {
                // Normal flow: Transition back to IDLE
                currentState.value = 'IDLE';
                timeLeft.value = workMinutes.value * 60;
            }
        }
    }

    function setCategory(categoryId: number) {
        currentCategoryId.value = categoryId;
    }

    // 🆕 History View Actions
    function formatDate(d: Date): string {
        const y = d.getFullYear();
        const m = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${y}-${m}-${day}`;
    }

    function flipToHistory() {
        isFlipped.value = true;
        loadHistory(selectedDate.value);
        loadEarliestDate();
    }

    function flipToTimer() {
        isFlipped.value = false;
    }

    async function loadHistory(date: string) {
        selectedDate.value = date;
        try {
            historyRecords.value = await timerApi.getHistory(date);
        } catch (error) {
            console.error('Failed to load history:', error);
            historyRecords.value = [];
        }
    }

    async function loadEarliestDate() {
        try {
            earliestDate.value = await timerApi.getEarliestDate();
        } catch (error) {
            console.error('Failed to load earliest date:', error);
        }
    }

    async function updateSessionNote(id: number, task: string) {
        try {
            const updated = await timerApi.updateNote(id, task);
            const idx = historyRecords.value.findIndex(r => r.id === id);
            if (idx !== -1) {
                historyRecords.value[idx] = updated;
            }
        } catch (error) {
            console.error('Failed to update note:', error);
        }
        editingNoteId.value = null;
    }

    function selectDateFromCalendar(date: string) {
        calendarOpen.value = false;
        loadHistory(date);
    }

    function getWeekDates(dateStr: string): string[] {
        const d = new Date(dateStr + 'T00:00:00');
        const day = d.getDay(); // 0=Sun
        const dates: string[] = [];
        for (let i = 0; i < 7; i++) {
            const dd = new Date(d);
            dd.setDate(d.getDate() - day + i);
            dates.push(formatDate(dd));
        }
        return dates;
    }

    return {
        isExpanded,
        currentState,
        isRunning,
        timeLeft,
        workMinutes,
        restMinutes,
        isSuperFlow,
        categories,
        currentCategoryId,
        sessions,
        displayTime,
        progress,
        // Session Recovery
        showRecoveryDialog,
        recoverySession,
        activeSessionId,
        // History View
        isFlipped,
        selectedDate,
        historyRecords,
        calendarOpen,
        earliestDate,
        editingNoteId,
        loadCategories,
        checkOngoingSession,
        resumeSession,
        discardSession,
        toggle,
        toggleSuperFlow,
        updateWorkMinutes,
        startTimer,
        pauseTimer,
        forceStop,
        setCategory,
        // History Actions
        flipToHistory,
        flipToTimer,
        loadHistory,
        loadEarliestDate,
        updateSessionNote,
        selectDateFromCalendar,
        getWeekDates,
        formatDate
    };
});
