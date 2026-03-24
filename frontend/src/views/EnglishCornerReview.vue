<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { englishCornerApi, type Flashcard } from '@/api/englishCornerApi';

const router = useRouter();
const loading = ref(true);
const cards = ref<Flashcard[]>([]);
const currentIndex = ref(0);
const showAnswer = ref(false);
const isSubmitting = ref(false);

const currentCard = computed(() => cards.value[currentIndex.value]);
const progressPercent = computed(() => {
  if (cards.value.length === 0) return 0;
  return Math.round((currentIndex.value / cards.value.length) * 100);
});

const fetchReviews = async () => {
  loading.value = true;
  try {
    const res = await englishCornerApi.getReviewToday();
    cards.value = res.data;
  } catch (err) {
    console.error('Failed to fetch reviews:', err);
  } finally {
    loading.value = false;
  }
};

const submitReview = async (success: boolean) => {
  if (!currentCard.value || isSubmitting.value) return;
  
  isSubmitting.value = true;
  try {
    await englishCornerApi.submitReview(currentCard.value.id, success);
    
    // Move to next or finish
    if (currentIndex.value < cards.value.length - 1) {
      currentIndex.value++;
      showAnswer.value = false;
    } else {
      // Completed!
      currentIndex.value = cards.value.length; // Trigger finished state
    }
  } catch (err) {
    console.error('Submission failed:', err);
  } finally {
    isSubmitting.value = false;
  }
};

onMounted(() => {
  fetchReviews();
});

const goBack = () => router.back();
</script>

<template>
  <div class="review-page">
    <!-- Header -->
    <header class="review-header">
      <button class="back-btn" @click="goBack">
        <span class="icon">✕</span>
      </button>
      <div class="progress-container">
        <div class="progress-bar" :style="{ width: progressPercent + '%' }"></div>
      </div>
      <div class="count-display">
        {{ currentIndex }} / {{ cards.length }}
      </div>
    </header>

    <!-- Main Content -->
    <main class="review-main">
      <div v-if="loading" class="state-container">
        <div class="loader"></div>
        <p>Seeking pending flashcards...</p>
      </div>

      <div v-else-if="cards.length === 0" class="state-container finished">
        <span class="emoji">🎉</span>
        <h2>All Clear!</h2>
        <p>You've reviewed all pending items for today.</p>
        <button class="action-btn primary" @click="goBack">Back to Corner</button>
      </div>

      <div v-else-if="currentIndex >= cards.length" class="state-container finished">
        <span class="emoji">🏆</span>
        <h2>Daily Goal Met</h2>
        <p>You finished today's review session.</p>
        <button class="action-btn primary" @click="goBack">Finish</button>
      </div>

      <Transition v-else name="card-flip" mode="out-in">
        <div v-if="currentCard" :key="currentCard.id" class="flashcard">
          <div class="card-inner" :class="{ 'is-flipped': showAnswer }">
            <!-- Front: Question -->
            <div class="card-face front">
              <div class="label">QUESTION</div>
              <div class="question-text">{{ currentCard?.prompt_question }}</div>
              <div class="hint">Try to recall the target phrase...</div>
              <button class="reveal-btn" @click="showAnswer = true">SHOW ANSWER</button>
            </div>

            <!-- Back: Answer -->
            <div class="card-face back">
              <div class="label">ANSWER</div>
              <div class="answer-text">{{ currentCard?.answer }}</div>
              
              <div class="context-box">
                <div class="label">CONTEXT</div>
                <div class="context-text">"{{ currentCard?.example_context }}"</div>
              </div>

              <div class="feedback-actions">
                <button 
                  class="fb-btn forgot" 
                  :disabled="isSubmitting"
                  @click="submitReview(false)"
                >
                  <span class="icon">×</span>
                  FORGOT
                </button>
                <button 
                  class="fb-btn got-it" 
                  :disabled="isSubmitting"
                  @click="submitReview(true)"
                >
                  <span class="icon">✔</span>
                  GOT IT
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </main>

    <!-- Footer Stats -->
    <footer v-if="currentCard && !loading" class="review-footer">
      <div class="card-info">
        <span>Level: {{ currentCard?.box_level }}</span>
        <span class="dot">·</span>
        <span>Word: {{ currentCard?.target_phrase }}</span>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.review-page {
  position: fixed;
  inset: 0;
  background: radial-gradient(circle at top, #1e293b 0%, #0f172a 100%);
  color: #f8fafc;
  display: flex;
  flex-direction: column;
  z-index: 2000;
  font-family: 'Inter', sans-serif;
}

.review-header {
  padding: 20px 40px;
  display: flex;
  align-items: center;
  gap: 32px;
}

.back-btn {
  background: none;
  border: none;
  color: #64748b;
  cursor: pointer;
  font-size: 24px;
}

.progress-container {
  flex: 1;
  height: 6px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: #3b82f6;
  transition: width 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
}

.count-display {
  font-size: 0.8rem;
  font-weight: 700;
  color: #94a3b8;
  letter-spacing: 0.1em;
}

.review-main {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

/* Card Styling */
.flashcard {
  width: 100%;
  max-width: 500px;
  height: 600px;
  perspective: 1000px;
}

.card-inner {
  position: relative;
  width: 100%;
  height: 100%;
  transform-style: preserve-3d;
  transition: transform 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}

.card-inner.is-flipped {
  transform: rotateY(180deg);
}

.card-face {
  position: absolute;
  width: 100%;
  height: 100%;
  backface-visibility: hidden;
  background: #1e293b;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 32px;
  padding: 40px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
}

.card-face.back {
  transform: rotateY(180deg);
}

.label {
  font-size: 0.7rem;
  font-weight: 800;
  color: #3b82f6;
  letter-spacing: 0.2em;
  margin-bottom: 24px;
  text-transform: uppercase;
}

.question-text {
  font-size: 1.8rem;
  font-weight: 700;
  line-height: 1.4;
  text-align: center;
  color: #f8fafc;
  margin-bottom: 32px;
}

.hint {
  font-size: 0.9rem;
  color: #64748b;
  margin-bottom: 40px;
}

.reveal-btn {
  background: white;
  color: #0f172a;
  border: none;
  padding: 16px 48px;
  border-radius: 99px;
  font-weight: 800;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s;
  letter-spacing: 0.1em;
}

.reveal-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 10px 20px rgba(255, 255, 255, 0.2);
}

.answer-text {
  font-size: 2rem;
  font-weight: 900;
  color: #fbbf24;
  text-align: center;
  margin-bottom: 40px;
}

.context-box {
  width: 100%;
  background: rgba(15, 23, 42, 0.5);
  border-radius: 20px;
  padding: 24px;
  margin-bottom: 48px;
}

.context-box .label {
  color: #64748b;
  margin-bottom: 12px;
}

.context-text {
  font-style: italic;
  font-size: 1rem;
  line-height: 1.6;
  color: #cbd5e1;
}

.feedback-actions {
  display: flex;
  gap: 20px;
  width: 100%;
}

.fb-btn {
  flex: 1;
  padding: 16px;
  border-radius: 16px;
  border: none;
  font-weight: 800;
  font-size: 0.8rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.2s;
}

.fb-btn.forgot {
  background: rgba(244, 63, 94, 0.1);
  color: #f43f5e;
  border: 1px solid rgba(244, 63, 94, 0.2);
}

.fb-btn.forgot:hover {
  background: #f43f5e;
  color: white;
}

.fb-btn.got-it {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.fb-btn.got-it:hover {
  background: #10b981;
  color: white;
}

.fb-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* States */
.state-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.state-container .emoji {
  font-size: 64px;
  margin-bottom: 24px;
}

.state-container h2 {
  font-size: 2rem;
  font-weight: 800;
  margin-bottom: 12px;
}

.state-container p {
  color: #94a3b8;
  margin-bottom: 32px;
}

.action-btn {
  padding: 12px 32px;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
}

.action-btn.primary {
  background: #3b82f6;
  color: white;
  border: none;
}

/* Footer */
.review-footer {
  padding: 24px;
  text-align: center;
}

.card-info {
  font-size: 0.75rem;
  color: #475569;
  letter-spacing: 0.05em;
}

.dot {
  margin: 0 12px;
  opacity: 0.5;
}

.loader {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(59, 130, 246, 0.2);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Transitions */
.card-flip-enter-active,
.card-flip-leave-active {
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.card-flip-enter-from {
  opacity: 0;
  transform: scale(0.9) translateY(20px);
}

.card-flip-leave-to {
  opacity: 0;
  transform: scale(1.1) translateY(-20px);
}
</style>
