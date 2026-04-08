<template>
  <div class="vocab-container">
    <button @click="toggleCard" class="fab-bubble" :class="{ 'is-active': showCard }">
      <span v-if="!showCard">💡</span>
      <span v-else>×</span>
    </button>

    <transition name="pop">
      <div v-if="showCard" class="vocab-card">
        <div class="card-header">
          <h3>{{ currentWord.word }}</h3>
          <span class="phonetic">/{{ currentWord.phonetic }}/</span>
        </div>

        <div class="card-content">
          <div class="sentence-group">
            <label>You said:</label>
            <p class="original">{{ currentWord.user_sentence }}</p>
          </div>
          
          <div class="sentence-group">
            <label>AI Suggested:</label>
            <p class="polished">{{ currentWord.polished_text }}</p>
          </div>
        </div>

        <div class="card-footer">
          <button @click="nextWord" class="btn-next">Next One</button>
          <button @click="markAsMastered" class="btn-master">I got this!</button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref } from 'vue';

// 模拟从你的 Wordbook 数据库取出的数据
const mockVocabList = [
  {
    word: 'mitigate',
    phonetic: 'ˈmɪtɪɡeɪt',
    user_sentence: 'We need to reduce the risk of the project.',
    polished_text: 'We must implement strategies to mitigate project risks effectively.'
  },
  {
    word: 'bandwidth',
    phonetic: 'ˈbændwɪdθ',
    user_sentence: 'I am very busy and have no time for this.',
    polished_text: 'I currently don\'t have the bandwidth to take on additional tasks.'
  }
];

const showCard = ref(false);
const currentWord = ref(mockVocabList[0]);

const toggleCard = () => {
  showCard.value = !showCard.value;
};

const nextWord = () => {
  // 随机切一个词，模拟复习
  const randomIndex = Math.floor(Math.random() * mockVocabList.length);
  currentWord.value = mockVocabList[randomIndex];
};

const markAsMastered = () => {
  console.log('Update SRS in Django...');
  showCard.value = false;
};
</script>

<style scoped>
.vocab-container {
  position: fixed;
  bottom: 2rem;
  right: 8rem;
  z-index: 9999;
  font-family: sans-serif;
}

.fab-bubble {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: #4f46e5;
  color: white;
  border: none;
  font-size: 24px;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  transition: transform 0.3s;
}

.fab-bubble:hover { transform: scale(1.1); }

.vocab-card {
  position: absolute;
  bottom: 70px;
  right: 0;
  width: 320px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.2);
  padding: 1.5rem;
  border: 1px solid #e5e7eb;
}

.card-header h3 { margin: 0; color: #111827; font-size: 1.25rem; }
.phonetic { color: #6b7280; font-size: 0.875rem; }

.card-content { margin: 1.5rem 0; }
.sentence-group { margin-bottom: 1rem; }
.sentence-group label { font-size: 0.75rem; font-weight: bold; color: #9ca3af; text-transform: uppercase; }

.original { color: #ef4444; font-size: 0.95rem; margin: 4px 0; text-decoration: line-through; opacity: 0.7; }
.polished { color: #10b981; font-size: 0.95rem; margin: 4px 0; font-weight: 500; }

.card-footer { display: flex; gap: 10px; }
.btn-next, .btn-master {
  flex: 1; padding: 8px; border-radius: 8px; border: none; cursor: pointer; font-size: 0.875rem;
}
.btn-next { background: #f3f4f6; color: #374151; }
.btn-master { background: #4f46e5; color: white; }

/* 简单的弹出动画 */
.pop-enter-active, .pop-leave-active { transition: all 0.3s ease; }
.pop-enter-from, .pop-leave-to { opacity: 0; transform: translateY(20px) scale(0.9); }
</style>