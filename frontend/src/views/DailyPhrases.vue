<template>
  <div class="page-root">
    <!-- ===== LOADING STATE ===== -->
    <div v-if="isLoading" class="loading-overlay flex flex-col items-center justify-center h-full text-indigo-500">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mb-4"></div>
      <p class="font-semibold tracking-wider">Preparing your daily session...</p>
    </div>

    <!-- ===== DONE (ROCKET) VIEW ===== -->
    <div v-else-if="isGlobalCompleted" class="done-view flex flex-col items-center justify-center h-full bg-indigo-50">
      <div class="text-6xl mb-6">🚀</div>
      <h1 class="text-3xl font-black text-indigo-900 mb-2">
        {{ wordsPracticed === 0 ? "You're All Caught Up!" : "Daily Goal Completed!" }}
      </h1>
      <p class="text-slate-500 mb-8 max-w-md text-center">
        <template v-if="wordsPracticed === 0">
          There are no words due for practice right now. You're doing amazing! Take a break or add some new vocabulary.
        </template>
        <template v-else>
          You've completed your {{ wordsPracticed }} vocabulary practices for today. Outstanding work!
        </template>
      </p>
      
      <div class="stats-card bg-white p-6 rounded-2xl shadow-sm border border-indigo-100 flex gap-12 text-center">
        <div>
          <div class="text-3xl font-bold text-indigo-600 mb-1">{{ wordsPracticed }}</div>
          <div class="text-xs font-bold text-slate-400 uppercase tracking-widest">Words</div>
        </div>
        <div>
          <div class="text-3xl font-bold text-indigo-600 mb-1">{{ focusMinutes }}<span class="text-lg">m</span></div>
          <div class="text-xs font-bold text-slate-400 uppercase tracking-widest">Focus Time</div>
        </div>
      </div>

      <button @click="$router.push('/')" class="mt-10 px-8 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-full transition-transform hover:-translate-y-1 shadow-lg shadow-indigo-200">
        Return to Dashboard
      </button>
    </div>

    <!-- ===== MAIN PRACTICE VIEW ===== -->
    <div v-else class="page-layout">
      
      <!-- ===== LEFT COLUMN ===== -->
      <div class="left-col">
        
        <!-- Word Header -->
        <div class="word-header">
          <span class="progress-badge">PRACTICE EXPRESSION {{ currentWordIndex + 1 }}/{{ dailyPracticeLimit }}</span>
          <h1 class="word-title">{{ currentSessionWord?.word }}</h1>
          <p 
            class="word-subtitle" 
            :class="{ 'scratch-card-hidden': !isMeaningRevealed }"
            @click="isMeaningRevealed = true"
            title="Click to reveal meaning"
          >
            {{ currentSessionWord?.explanation || 'Loading meaning...' }}
          </p>
        </div>

        <!-- Composition Section (COMPOSING / SUBMITTING) -->
        <div class="section flex-1 flex flex-col" v-if="uiStage === 'COMPOSING' || uiStage === 'SUBMITTING'">
          <div class="section-label">
            <span class="section-icon">✏️</span>
            Your Composition
          </div>
          <div class="textarea-wrapper" :class="{'opacity-75 pointer-events-none': uiStage === 'SUBMITTING'}">
            <textarea
              v-model="userInput"
              class="composition-input"
              placeholder="Start typing your unique sentence here..."
              :readonly="uiStage === 'SUBMITTING'"
            ></textarea>
            <div class="textarea-footer">
              <span class="char-count">{{ userInput.length }} / 500 characters</span>
            </div>
          </div>
        </div>

        <!-- Reviewing Section (Diff Viewer) -->
        <div class="section flex-1 flex flex-col" v-if="uiStage === 'REVIEWING'">
          <div class="section-label text-indigo-600">
            <span class="section-icon">✨</span>
            AI Polished Feedback
          </div>
          <div class="bg-white rounded-2xl shadow-sm overflow-hidden flex-1 border border-indigo-50">
            <TextDiffViewer
              :originalText="lastSubmittedText"
              :polishedText="verificationResult?.polished_text || lastSubmittedText"
              theme="light"
              :enableActions="false"
            />

            <!-- Native Version Section -->
            <div v-if="verificationResult?.native_version" class="px-6 pb-2 pt-2">
              <div class="flex items-start gap-4 bg-sky-50/70 border border-sky-100 p-5 rounded-[20px]">
                <div class="shrink-0 text-sky-500 mt-0.5">
                  <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" viewBox="0 0 256 256" fill="currentColor">
                    <path d="M128,24A104,104,0,0,0,36.18,176.88L24.83,210.93a16,16,0,0,0,20.24,20.24l34.05-11.35A104,104,0,1,0,128,24Zm0,192a87.87,87.87,0,0,1-44.06-11.81,8,8,0,0,0-6.54-1.08L46,213.56l10.45-31.35a8,8,0,0,0-1.08-6.54A88,88,0,1,1,128,216ZM84,140a12,12,0,1,1,12-12A12,12,0,0,1,84,140Zm44,0a12,12,0,1,1,12-12A12,12,0,0,1,128,140Zm44,0a12,12,0,1,1,12-12A12,12,0,0,1,172,140Z" />
                  </svg>
                </div>
                <div>
                  <div class="text-[10px] font-black tracking-widest text-sky-600 uppercase mb-1">NATIVE VERSION</div>
                  <div class="text-[15px] font-medium text-sky-900 leading-relaxed">
                    "{{ verificationResult.native_version }}"
                  </div>
                </div>
              </div>
            </div>

            <!-- Community Version Section -->
            <div v-if="verificationResult?.community_version" class="px-6 pb-6 pt-2">
              <div class="flex items-start gap-4 bg-indigo-50/70 border border-indigo-100 p-5 rounded-[20px]">
                <div class="shrink-0 text-indigo-500 mt-0.5">
                  <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="m3 21 1.9-5.7a8.5 8.5 0 1 1 3.8 3.8z"/>
                  </svg>
                </div>
                <div>
                  <div class="text-[10px] font-black tracking-widest text-indigo-600 uppercase mb-1">COMMUNITY VIBE / REDDIT-ISH</div>
                  <div class="text-[15px] font-semibold text-indigo-900 leading-relaxed italic">
                    {{ verificationResult.community_version }}
                  </div>
                </div>
              </div>
            </div>
            
            <div class="px-6 py-6 border-t border-indigo-50 bg-white">
              <div class="bg-slate-100/70 rounded-2xl p-5 flex items-start gap-5">
                <div class="w-12 h-12 bg-white rounded-full flex items-center justify-center shrink-0 shadow-[0_2px_8px_rgba(0,0,0,0.04)]">
                  🪄
                </div>
                <p class="text-[15.5px] text-slate-700 leading-relaxed m-0 mt-2.5 font-medium">
                  "{{ verificationResult?.feedback }}"
                </p>
              </div>
            </div>
          </div>
          
          <!-- Equivalent Expressions Section -->
          <div v-if="verificationResult?.alternatives && verificationResult.alternatives.length > 0" class="mt-2 flex flex-col gap-3 shrink-0">
            <div class="flex items-center gap-2 text-[11px] font-black text-slate-500 uppercase tracking-widest px-2 mb-1">
              <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-indigo-500" viewBox="0 0 256 256" fill="currentColor">
                <path d="M216,40H40A16,16,0,0,0,24,56V200a16,16,0,0,0,16,16H216a16,16,0,0,0,16-16V56A16,16,0,0,0,216,40Zm0,160H40V56H216V200ZM176,80a8,8,0,0,1-8,8H88a8,8,0,0,1,0-16h80A8,8,0,0,1,176,80Zm0,48a8,8,0,0,1-8,8H88a8,8,0,0,1,0-16h80A8,8,0,0,1,176,128Zm-40,48a8,8,0,0,1-8,8H88a8,8,0,0,1,0-16h40A8,8,0,0,1,136,176Z" />
                <path d="M24,192L48,168V192Z" fill="#6366f1" />
              </svg>
              EQUIVALENT EXPRESSIONS
            </div>
            
            <div class="grid gap-4" :style="{ gridTemplateColumns: `repeat(${Math.min(verificationResult.alternatives.length, 3)}, minmax(0, 1fr))` }">
              <div 
                v-for="(alt, i) in verificationResult.alternatives" 
                :key="i"
                class="bg-white rounded-[20px] p-5 shadow-sm border border-slate-100 flex flex-col gap-3"
              >
                <div class="flex items-center gap-2 text-xs font-bold text-slate-500 tracking-wide uppercase">
                  <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5 text-blue-500" viewBox="0 0 256 256" fill="currentColor">
                    <path d="M216,48H40A16,16,0,0,0,24,64V192a16,16,0,0,0,16,16H216a16,16,0,0,0,16-16V64A16,16,0,0,0,216,48Zm0,144H40V64H216V192Z" />
                  </svg>
                  <span>{{ alt.vibe }}</span>
                </div>
                <p class="text-[14.5px] leading-relaxed text-slate-700 m-0" v-html="highlightExpression(alt.example, alt.expression)"></p>
              </div>
            </div>
          </div>
        </div>

        <!-- ===== BOTTOM SUBMIT / ACTION BAR ===== -->
        <div class="submit-bar">
          
          <!-- Submit Button -->
          <button 
            v-if="uiStage === 'COMPOSING' || uiStage === 'SUBMITTING'"
            class="submit-btn" 
            @click="submitAnswer" 
            :disabled="uiStage === 'SUBMITTING' || !userInput.trim()"
          >
            <span>{{ uiStage === 'SUBMITTING' ? 'Submitting...' : '🚀 Submit My Masterpiece' }}</span>
            <svg v-if="uiStage !== 'SUBMITTING'" class="submit-arrow" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </button>

          <!-- Continue Button / Finished Text -->
          <template v-else-if="uiStage === 'REVIEWING'">
            <button 
              v-if="currentWordIndex < dailyPracticeLimit - 1"
              class="submit-btn" 
              @click="nextWord"
            >
              <span>Continue to Next Phrase</span>
              <svg class="submit-arrow" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
              </svg>
            </button>
            <div v-else class="w-full flex items-center justify-between bg-white px-6 py-4 rounded-2xl shadow-[0_4px_20px_rgba(16,185,129,0.08)] border border-emerald-50 mt-2">
              <div class="flex items-center gap-4">
                <div class="w-12 h-12 bg-emerald-500 rounded-full flex items-center justify-center text-white shadow-lg shadow-emerald-200 font-bold shrink-0">
                  <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                  </svg>
                </div>
                <div class="flex flex-col text-left">
                  <h3 class="text-xl font-bold text-slate-800 m-0 leading-tight">Congratulations!</h3>
                  <p class="text-sm text-slate-500 m-0 mt-0.5 font-medium">You've mastered all targeted keywords today.</p>
                </div>
              </div>

              <div class="flex items-center gap-6">
                <div class="flex flex-col items-end gap-1.5">
                  <span class="text-[11px] font-black tracking-widest text-slate-400">PROGRESS <span class="text-emerald-600 ml-1">{{ dailyPracticeLimit }}/{{ dailyPracticeLimit }}</span></span>
                  <div class="w-32 h-2.5 bg-slate-100 rounded-full overflow-hidden">
                    <div class="h-full bg-emerald-400 w-full rounded-full"></div>
                  </div>
                </div>

                <button @click="$router.push('/')" class="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3.5 px-6 rounded-xl shadow-md transition-colors whitespace-nowrap tracking-wide text-sm shrink-0">
                  FINISH SESSION
                </button>
              </div>
            </div>
          </template>

        </div>
      </div>

      <!-- ===== RIGHT COLUMN ===== -->
      <div class="right-col">
        
        <!-- Scenarios Panel -->
        <div class="panel">
          <div class="panel-label">
            <span>💡</span> SCENARIO CONTEXTS
          </div>
          <div class="scenario-list">
            <div 
              v-for="(ctx, i) in currentSessionWord?.scenarios || []" 
              :key="i" 
              class="scenario-card"
            >
              <div class="scenario-index">{{ String(i + 1).padStart(2, '0') }}</div>
              <div class="scenario-body">
                <p class="scenario-text">{{ ctx.description }}</p>
                <span class="scenario-tag">{{ ctx.tag }}</span>
              </div>
            </div>
            <div v-if="!currentSessionWord?.scenarios?.length" class="text-xs text-slate-400 italic">
              No scenarios generated. Make one up!
            </div>
          </div>
        </div>

        <!-- Word Bank -->
        <div class="panel">
          <div class="panel-label flex justify-between items-center">
            <span>🏦 WORD BANK</span>
            <button 
              @click="refreshWordBank" 
              :disabled="uiStage !== 'COMPOSING' || isRefreshing"
              class="text-indigo-600 hover:text-indigo-800 disabled:opacity-30 disabled:cursor-not-allowed"
              title="Refresh Bonus Words"
            >
              <span class="text-lg" :class="{'animate-spin inline-block': isRefreshing}">🔄</span>
            </button>
          </div>
          <div class="word-chips">
            <span 
              v-for="w in currentSessionWord?.bonus_words || []" 
              :key="w.id" 
              class="word-chip"
              :class="{ 'used': userInput.toLowerCase().includes(w.word.toLowerCase()) }"
            >
              {{ w.word }}
            </span>
          </div>
          <p class="word-bank-tip">Tip: Use at least one of these words to earn bonus points.</p>
        </div>

        <!-- Visual Anchor (Static Placeholder for MVP) -->
        <div class="panel visual-panel">
          <div class="visual-image-wrapper bg-slate-200">
            <!-- Using a solid color or gradient as a safe static placeholder since we don't have dynamic images yet -->
            <div class="w-full h-full bg-gradient-to-br from-indigo-300 to-purple-300 relative">
               <div class="absolute inset-0 flex items-center justify-center text-white/40 text-6xl font-black">
                 {{ firstScenarioTag }}
               </div>
            </div>
            <div class="visual-overlay"></div>
          </div>
          <div class="visual-body">
            <h3 class="panel-label" style="margin-bottom: 8px;"><span>🔭</span> Visual Anchor</h3>
            <p class="visual-desc">Context: <em>{{ firstScenarioTag || 'General Setup' }}</em></p>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { dailyPhrasesApi } from '@/api/dailyPhrasesApi';
import type { SessionWord, VerifyResponse } from '@/api/dailyPhrasesApi';
import TextDiffViewer from '@/components/TextDiffViewer.vue';

// State
const dailyPracticeLimit = ref(0);
const isLoading = ref(true);
const isGlobalCompleted = ref(false); // Rocket Screen
const focusMinutes = ref(0);

const isMeaningRevealed = ref(false); // Controls scratch card logic

const uiStage = ref<'COMPOSING' | 'SUBMITTING' | 'REVIEWING'>('COMPOSING');
const currentWordIndex = ref(0);
const wordsPracticed = ref(0);
const sessionWords = ref<SessionWord[]>([]);

const userInput = ref('');
const lastSubmittedText = ref('');
const verificationResult = ref<VerifyResponse['verification'] | null>(null);

const isRefreshing = ref(false);

// Computed
const currentSessionWord = computed(() => {
  if (sessionWords.value.length === 0) return null;
  // Safety bound
  const idx = Math.min(currentWordIndex.value, sessionWords.value.length - 1);
  return sessionWords.value[idx];
});

const firstScenarioTag = computed(() => {
  const scenarios = currentSessionWord.value?.scenarios;
  if (scenarios && scenarios.length > 0) {
    return scenarios[0]?.tag || 'General';
  }
  return 'General';
});

// Initialization
onMounted(async () => {
  try {
    const res = await dailyPhrasesApi.initSession();
    const data = res.data;

    if (data.is_completed) {
      isGlobalCompleted.value = true;
      wordsPracticed.value = data.words_practiced;
      dailyPracticeLimit.value = Math.max(data.words_practiced, 1);
      focusMinutes.value = data.summary?.focus_minutes || 0;
    } else {
      sessionWords.value = data.session_words || [];
      dailyPracticeLimit.value = sessionWords.value.length || 1;
      wordsPracticed.value = data.words_practiced || 0;
      currentWordIndex.value = Math.min(data.words_practiced, Math.max(0, dailyPracticeLimit.value - 1));
      uiStage.value = 'COMPOSING';
    }
  } catch (err) {
    console.error("Failed to initialize Daily Phrases:", err);
    // Handle error (e.g. toast notification)
  } finally {
    isLoading.value = false;
  }
});

// Actions
const submitAnswer = async () => {
  if (!userInput.value.trim() || !currentSessionWord.value) return;

  uiStage.value = 'SUBMITTING';
  lastSubmittedText.value = userInput.value;

  try {
    const res = await dailyPhrasesApi.verifySentence(
      currentSessionWord.value.id,
      userInput.value,
      currentSessionWord.value.bonus_words
    );

    verificationResult.value = res.data.verification;
    if (res.data.session_progress) {
      wordsPracticed.value = res.data.session_progress.words_practiced;
    } else {
      wordsPracticed.value = wordsPracticed.value + 1;
    }

    uiStage.value = 'REVIEWING';
    
    // Normal completion check -> we don't trigger global rocket screen if completed in-session
    // The UI handles showing completion text inline when index == 2
  } catch (err) {
    console.error("Verification failed:", err);
    // Revert state on failure
    uiStage.value = 'COMPOSING';
  }
};

const nextWord = () => {
  if (currentWordIndex.value < dailyPracticeLimit.value - 1) {
    currentWordIndex.value++;
    userInput.value = '';
    verificationResult.value = null;
    uiStage.value = 'COMPOSING';
    isMeaningRevealed.value = false;
  }
};

const refreshWordBank = async () => {
  if (uiStage.value !== 'COMPOSING') return;
  
  // Exclude ALL session words to prevent overlaps
  const excludeIds = sessionWords.value.map(w => w.id);
  
  isRefreshing.value = true;
  try {
    const res = await dailyPhrasesApi.refreshBonus(excludeIds);
    if (currentSessionWord.value) {
      currentSessionWord.value.bonus_words = res.data.bonus_words;
    }
  } catch (err) {
    console.error("Failed to refresh bonus words:", err);
  } finally {
    isRefreshing.value = false;
  }
};

const highlightExpression = (example: string, expression: string) => {
  if (!example || !expression) return example;
  
  if (example.includes('<em>') || example.includes('*')) {
    let formatted = example.replace(/<em>(.*?)<\/em>/gi, '<span class="text-sky-500 font-bold italic">$1</span>');
    formatted = formatted.replace(/\*(.*?)\*/g, '<span class="text-sky-500 font-bold italic">$1</span>');
    return formatted;
  } else {
    // Escape special regex chars from the expression to prevent breaking matching
    const safeExpr = expression.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
    const regex = new RegExp(`(${safeExpr})`, 'gi');
    return example.replace(regex, '<span class="text-sky-500 font-bold italic">$1</span>');
  }
};
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

.page-root {
  /* height: 100vh; /* Using full view height or fill container */
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
  overflow-y: auto;
}
.right-col::-webkit-scrollbar {
  width: 0;
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
  font-size: 2.2rem;
  font-weight: 900;
  color: #1e1b4b;
  margin: 0 0 6px 0;
  letter-spacing: -0.02em;
}

.word-subtitle {
  font-size: 0.9rem;
  color: #64748b;
  font-weight: 500;
  margin: 0;
  display: inline-block;
  padding: 4px 8px;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.scratch-card-hidden {
  color: transparent !important;
  background-color: #e2e8f0;
  cursor: pointer;
  user-select: none;
  background-image: repeating-linear-gradient(
    45deg,
    transparent,
    transparent 10px,
    rgba(159, 215, 17, 0.25) 10px,
    rgba(18, 7, 96, 0.25) 20px
  );
}

.scratch-card-hidden:hover {
  background-color: #cbd5e1;
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
  font-weight: 800;
  color: #94a3b8;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.section-icon {
  font-size: 14px;
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
  color: #475569;
  border-radius: 16px;
  padding: 16px 20px;
  display: flex;
  gap: 16px;
  border: 1px solid rgba(99, 102, 241, 0.05);
  box-shadow: 0 1px 8px rgba(0, 0, 0, 0.02);
}

.scenario-index {
  font-size: 10px;
  font-weight: 800;
  color: #c7d2fe;
  letter-spacing: 0.05em;
  padding-top: 2px;
  flex-shrink: 0;
}

.scenario-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.scenario-text {
  font-size: 0.95rem;
  color: #334155;
  margin: 0;
  line-height: 1.6;
  font-weight: 500;
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
}

/* ═══════════════════════════════
   COMPOSITION
═══════════════════════════════ */
.textarea-wrapper {
  flex: 1;
  background: white;
  border-radius: 20px;
  box-shadow: 0 1px 8px rgba(0, 0, 0, 0.04);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid rgba(0,0,0,0.03);
  transition: opacity 0.3s;
}

.composition-input {
  flex: 1;
  min-height: 180px;
  padding: 24px 28px 12px;
  border: none;
  outline: none;
  font-family: 'Inter', sans-serif;
  font-size: 1.05rem;
  color: #334155;
  line-height: 1.7;
  resize: none;
  background: transparent;
}

.composition-input::placeholder {
  color: #cbd5e1;
  font-style: italic;
}

.textarea-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 12px 24px;
  border-top: 1px solid #f8fafc;
  background: #fdfdfe;
}

.char-count {
  font-size: 11px;
  color: #94a3b8;
  font-weight: 600;
}

/* ═══════════════════════════════
   RIGHT PANELS
═══════════════════════════════ */
.panel {
  background: white;
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 1px 12px rgba(0, 0, 0, 0.04);
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
  margin-bottom: 16px;
}

.word-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 14px;
}

.word-chip {
  background: #f1f5f9;
  color: #475569;
  font-size: 13px;
  font-weight: 600;
  padding: 8px 16px;
  border-radius: 99px;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.word-chip.used {
  background: #d1fae5;
  color: #059669;
  border-color: #a7f3d0;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.15);
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
}

.visual-image-wrapper {
  position: relative;
  height: 180px;
  overflow: hidden;
}

.visual-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to bottom, transparent 30%, rgba(15, 15, 40, 0.3));
}

.visual-body {
  padding: 20px 24px;
}

.visual-desc {
  font-size: 13px;
  color: #64748b;
  line-height: 1.6;
  margin: 0;
}

/* ═══════════════════════════════
   SUBMIT BAR
═══════════════════════════════ */
.submit-bar {
  padding: 24px 0 12px;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 90px;
}

.submit-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  background: linear-gradient(135deg, #6366f1 0%, #818cf8 100%);
  color: white;
  border: none;
  padding: 18px 64px;
  border-radius: 99px;
  font-family: 'Inter', sans-serif;
  font-size: 16px;
  font-weight: 800;
  letter-spacing: 0.02em;
  cursor: pointer;
  box-shadow: 0 8px 30px rgba(99, 102, 241, 0.35);
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 12px 40px rgba(99, 102, 241, 0.45);
}

.submit-btn:active:not(:disabled) {
  transform: scale(0.98);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  background: #9ca3af;
  box-shadow: none;
}

.submit-arrow {
  width: 20px;
  height: 20px;
}
</style>
