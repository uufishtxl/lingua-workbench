<template>
    <div class="page-root">

        <div class="page-layout">

            <!-- ===== LEFT COLUMN ===== -->
            <div class="left-col">

                <!-- Word Header -->
                <div class="word-header">
                    <span class="progress-badge">PRACTICE EXPRESSION 1/3</span>
                    <h1 class="word-title">cookie-cutter</h1>
                    <p class="word-subtitle">千篇一律的，缺乏个性的</p>
                </div>

                <!-- Scenario Section -->
                <!-- <div class="section">
          <div class="section-label">
            <span class="section-icon">💡</span>
            Scenario Contexts
            <span class="section-count">SCENARIOS</span>
          </div>

          <div class="scenario-list">
            <div
              v-for="(ctx, i) in contexts"
              :key="i"
              class="scenario-card"
              :class="{ active: activeScenario === i }"
              @click="activeScenario = i"
            >
              <div class="scenario-index">{{ String(i + 1).padStart(2, '0') }}</div>
              <div class="scenario-body">
                <p class="scenario-text">{{ ctx.text }}</p>
                <span class="scenario-tag">{{ ctx.tag }}</span>
              </div>
            </div>
          </div>
        </div> -->

                <!-- Composition Section -->
                <div class="section composition-section">
                    <div class="section-label">
                        <span class="section-icon">✏️</span>
                        Your Composition
                    </div>
                    <div class="textarea-wrapper">
                        <textarea v-model="userInput" class="composition-input"
                            placeholder="Start typing your unique sentence here..."></textarea>
                        <div class="textarea-footer">
                            <div class="textarea-tools">
                                <button class="tool-btn" title="Voice Input">🎤</button>
                                <button class="tool-btn" title="Insert Image">🖼</button>
                            </div>
                            <span class="char-count">{{ userInput.length }} / 500 characters</span>
                        </div>
                    </div>
                </div>

                <!-- <div class="section composition-section">
          <div class="section-label">
            <span class="section-icon">✏️</span>
            AI Suggestion
          </div>
          <div class="textarea-wrapper">
            <textarea
              v-model="userInput"
              class="composition-input"
              placeholder="Start typing your unique sentence here..."
            ></textarea>
            <div class="textarea-footer">
              <div class="textarea-tools">
                <button class="tool-btn" title="Voice Input">🎤</button>
                <button class="tool-btn" title="Insert Image">🖼</button>
              </div>
              <span class="char-count">{{ userInput.length }} / 500 characters</span>
            </div>
          </div>
        </div> -->

                <!-- ===== BOTTOM SUBMIT ===== -->
                <div class="submit-bar">
                    <button class="submit-btn" @click="submitAnswer" :disabled="isSubmitting">
                        <span>{{ isSubmitting ? 'Correcting...' : '🚀 Submit My Masterpiece' }}</span>
                        <svg v-if="!isSubmitting" class="submit-arrow" fill="none" viewBox="0 0 24 24"
                            stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5"
                                d="M13 7l5 5m0 0l-5 5m5-5H6" />
                        </svg>
                    </button>
                </div>


            </div>

            <!-- ===== RIGHT COLUMN ===== -->
            <div class="right-col">
                <div class="panel">
                    <div class="panel-label">
                        <span>🏦</span> SCENARIO Contexts
                    </div>

                    <div class="scenario-list">
                        <div v-for="(ctx, i) in contexts" :key="i" class="scenario-card"
                            :class="{ active: activeScenario === i }" @click="activeScenario = i">
                            <div class="scenario-index">{{ String(i + 1).padStart(2, '0') }}</div>
                            <div class="scenario-body">
                                <p class="scenario-text">{{ ctx.text }}</p>
                                <span class="scenario-tag">{{ ctx.tag }}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Word Bank -->
                <div class="panel">
                    <div class="panel-label">
                        <span>🏦</span> Word Bank
                    </div>
                    <div class="word-chips">
                        <span v-for="w in bonusWords" :key="w" class="word-chip"
                            :class="{ used: userInput.toLowerCase().includes(w.split(' ')[0].toLowerCase()) }">{{ w
                            }}</span>
                    </div>
                    <p class="word-bank-tip">Tip: Use at least one of these words to earn bonus points.</p>
                </div>

                <!-- Visual Anchor -->
                <div class="panel visual-panel">
                    <div class="visual-image-wrapper">
                        <img src="/scenario_office.jpg" alt="Visual Anchor" class="visual-image" />
                        <div class="visual-overlay"></div>
                    </div>
                    <div class="visual-body">
                        <h3 class="panel-label" style="margin-bottom: 8px;"><span>🔭</span> Visual Anchor</h3>
                        <p class="visual-desc">"Imagine a production line of identical houses or offices. This is the
                            visual essence of <em>cookie-cutter.</em>"</p>
                    </div>
                </div>





            </div>
        </div>


    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';

const userInput = ref('');
const isSubmitting = ref(false);
const activeScenario = ref < number | null > (null);
const timerCount = ref(40);
const timerRunning = ref(true);
let timerInterval: ReturnType<typeof setInterval> | null = null;

const bonusWords = ['homogenized', 'mindset', 'vent their anger'];

const contexts = [
    { tag: 'Professional', text: '在评估一个外包团队提交的 UI 设计稿时，发现全是套用模板的设计。' },
    { tag: 'Daily Life', text: '辅导四年级儿子写作业时，发现市面上的教辅材料全是一个模子。' },
    { tag: 'Entertainment', text: '和朋友吐槽最近看的一部流水线网剧，人设极度模式化。' },
];

const submitAnswer = () => {
    isSubmitting.value = true;
    setTimeout(() => (isSubmitting.value = false), 1500);
};

const toggleTimer = () => {
    timerRunning.value = !timerRunning.value;
};

onMounted(() => {
    timerInterval = setInterval(() => {
        if (timerRunning.value && timerCount.value > 0) {
            timerCount.value--;
        }
    }, 1000);
});

onUnmounted(() => {
    if (timerInterval) clearInterval(timerInterval);
});
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

* {
    box-sizing: border-box;
}

.page-root {
    height: 100%;
    background: #eeeffc;
    display: flex;
    flex-direction: column;
    font-family: 'Inter', sans-serif;
    overflow: hidden;
}

/* ═══════════════════════════════
   LAYOUT
═══════════════════════════════ */
.page-layout {
    flex: 1;
    display: flex;
    gap: 24px;
    padding: 32px 40px 16px;
    overflow: hidden;
}

.left-col {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 20px;
    overflow-y: auto;
    padding-right: 4px;
}

.left-col::-webkit-scrollbar {
    width: 0;
}

.right-col {
    width: 500px;
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    gap: 16px;
}

/* ═══════════════════════════════
   WORD HEADER
═══════════════════════════════ */
.word-header {
    background: white;
    border-radius: 20px;
    padding: 24px 28px;
    box-shadow: 0 2px 12px rgba(99, 102, 241, 0.06);
}

.progress-badge {
    display: inline-block;
    background: #ede9fe;
    color: #6366f1;
    font-size: 9px;
    font-weight: 800;
    letter-spacing: 0.15em;
    padding: 4px 10px;
    border-radius: 99px;
    margin-bottom: 12px;
    text-transform: uppercase;
}

.word-title {
    font-size: 2rem;
    font-weight: 900;
    color: #1e1b4b;
    margin: 0 0 6px 0;
    letter-spacing: -0.02em;
}

.word-subtitle {
    font-size: 0.82rem;
    color: #94a3b8;
    font-weight: 500;
    margin: 0;
}

/* ═══════════════════════════════
   SECTION LABELS
═══════════════════════════════ */
.section {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.section-label {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 11px;
    font-weight: 700;
    color: #94a3b8;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

.section-icon {
    font-size: 14px;
}

.section-count {
    margin-left: auto;
    background: #e0e7ff;
    color: #6366f1;
    font-size: 9px;
    padding: 2px 8px;
    border-radius: 99px;
}

/* ═══════════════════════════════
   SCENARIO CARDS
═══════════════════════════════ */
.scenario-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.scenario-card {
    background: #fafafe;
    color: #6366f1;
    /* background: white; */
    border-radius: 16px;
    padding: 16px 20px;
    display: flex;
    gap: 16px;
    cursor: pointer;
    border: 2px solid transparent;
    box-shadow: 0 1px 8px rgba(0, 0, 0, 0.04);
    transition: all 0.2s ease;
}

.scenario-card:hover {
    box-shadow: 0 4px 20px rgba(99, 102, 241, 0.1);
    border-color: rgba(99, 102, 241, 0.2);
}

.scenario-card.active {
    border-color: #6366f1;
    background: #fafafe;
    box-shadow: 0 4px 20px rgba(99, 102, 241, 0.15);
}

.scenario-index {
    font-size: 10px;
    font-weight: 800;
    color: #c7d2fe;
    letter-spacing: 0.05em;
    padding-top: 2px;
    flex-shrink: 0;
}

.scenario-card.active .scenario-index {
    color: #6366f1;
}

.scenario-body {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.scenario-text {
    font-size: 0.9rem;
    color: #475569;
    margin: 0;
    line-height: 1.6;
}

.scenario-card.active .scenario-text {
    color: #1e1b4b;
}

.scenario-tag {
    display: inline-block;
    background: #f1f5f9;
    color: #64748b;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 3px 10px;
    border-radius: 6px;
    align-self: flex-start;
    transition: all 0.2s;
}

.scenario-card.active .scenario-tag {
    background: #ede9fe;
    color: #6366f1;
}

/* ═══════════════════════════════
   COMPOSITION
═══════════════════════════════ */
.composition-section {
    flex: 1;
    min-height: 160px;
}

.textarea-wrapper {
    flex: 1;
    background: white;
    border-radius: 20px;
    box-shadow: 0 1px 8px rgba(0, 0, 0, 0.04);
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

.composition-input {
    flex: 1;
    min-height: 140px;
    padding: 20px 24px 12px;
    border: none;
    outline: none;
    font-family: 'Inter', sans-serif;
    font-size: 1rem;
    color: #334155;
    line-height: 1.7;
    resize: none;
    background: transparent;
    placeholder-color: #cbd5e1;
}

.composition-input::placeholder {
    color: #cbd5e1;
    font-style: italic;
}

.textarea-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 20px;
    border-top: 1px solid #f1f5f9;
}

.textarea-tools {
    display: flex;
    gap: 8px;
}

.tool-btn {
    background: none;
    border: none;
    font-size: 16px;
    cursor: pointer;
    opacity: 0.4;
    transition: opacity 0.2s;
    padding: 4px;
}

.tool-btn:hover {
    opacity: 0.9;
}

.char-count {
    font-size: 11px;
    color: #94a3b8;
    font-weight: 500;
}

/* ═══════════════════════════════
   RIGHT PANELS
═══════════════════════════════ */
.panel {
    background: white;
    border-radius: 20px;
    padding: 20px;
    box-shadow: 0 1px 8px rgba(0, 0, 0, 0.05);
}

.panel-label {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 11px;
    font-weight: 800;
    color: #64748b;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 14px;
}

.word-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 12px;
}

.word-chip {
    background: #ede9fe;
    color: #6366f1;
    font-size: 12px;
    font-weight: 600;
    padding: 6px 14px;
    border-radius: 99px;
    cursor: pointer;
    transition: all 0.2s;
}

.word-chip:hover {
    background: #c7d2fe;
}

.word-chip.used {
    background: #d1fae5;
    color: #10b981;
}

.word-bank-tip {
    font-size: 11px;
    color: #94a3b8;
    line-height: 1.5;
    margin: 0;
}

/* VISUAL PANEL */
.visual-panel {
    padding: 0;
    overflow: hidden;
    flex: 1;
}

.visual-image-wrapper {
    position: relative;
    height: 160px;
    overflow: hidden;
}

.visual-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.7s ease;
}

.visual-panel:hover .visual-image {
    transform: scale(1.06);
}

.visual-overlay {
    position: absolute;
    inset: 0;
    background: linear-gradient(to bottom, transparent 40%, rgba(15, 15, 40, 0.4));
}

.visual-body {
    padding: 18px 20px;
}

.visual-desc {
    font-size: 12px;
    color: #64748b;
    line-height: 1.6;
    margin: 0;
    font-style: italic;
}

/* TIMER */
.timer-pill {
    display: flex;
    align-items: center;
    gap: 14px;
    background: #1e1b4b;
    border-radius: 16px;
    padding: 14px 18px;
}

.timer-display {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    width: 44px;
    height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.timer-num {
    font-size: 1.2rem;
    font-weight: 900;
    color: white;
    font-variant-numeric: tabular-nums;
}

.timer-info {
    flex: 1;
}

.timer-label {
    font-size: 9px;
    font-weight: 800;
    color: rgba(255, 255, 255, 0.4);
    letter-spacing: 0.15em;
    margin-bottom: 2px;
}

.timer-mode {
    font-size: 12px;
    font-weight: 700;
    color: white;
}

.timer-ctrl {
    background: rgba(255, 255, 255, 0.1);
    border: none;
    color: white;
    width: 34px;
    height: 34px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    transition: background 0.2s;
    flex-shrink: 0;
}

.timer-ctrl:hover {
    background: rgba(255, 255, 255, 0.2);
}

/* ═══════════════════════════════
   SUBMIT BAR
═══════════════════════════════ */
.submit-bar {
    padding: 16px 40px 28px;
    display: flex;
    justify-content: center;
}

.submit-btn {
    display: flex;
    align-items: center;
    gap: 10px;
    background: linear-gradient(135deg, #6366f1 0%, #818cf8 100%);
    color: white;
    border: none;
    padding: 16px 60px;
    border-radius: 99px;
    font-family: 'Inter', sans-serif;
    font-size: 15px;
    font-weight: 800;
    letter-spacing: 0.02em;
    cursor: pointer;
    box-shadow: 0 8px 30px rgba(99, 102, 241, 0.35);
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.submit-btn:hover {
    transform: translateY(-2px) scale(1.02);
    box-shadow: 0 16px 40px rgba(99, 102, 241, 0.45);
}

.submit-btn:active {
    transform: scale(0.98);
}

.submit-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
}

.submit-arrow {
    width: 18px;
    height: 18px;
}
</style>