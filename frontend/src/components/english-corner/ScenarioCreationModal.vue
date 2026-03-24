<script setup lang="ts">
import { ref } from 'vue';

const emit = defineEmits(['close', 'create']);

const icons = ['☕', '💻', '🎤', '✈️', '🏠', '🍕', '🎨', '🏥', '🛒', '💬'];
const selectedIcon = ref(icons[0]);
const title = ref('');
const description = ref('');
const isSubmitting = ref(false);

const handleSubmit = () => {
  if (!title.value.trim()) return;
  
  isSubmitting.value = true;
  
  // Mock "Black Magic" - Simulating AI Prompt Generation
  setTimeout(() => {
    emit('create', {
      icon: selectedIcon.value,
      title: title.value,
      description: description.value
    });
    isSubmitting.value = false;
  }, 1500);
};
</script>

<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="creation-modal">
      <div class="modal-header">
        <span class="step-label">New Scenario</span>
        <button class="close-btn" @click="emit('close')">✕</button>
      </div>

      <div class="form-content">
        <!-- Icon Section -->
        <div class="section">
          <label>Pick an Icon</label>
          <div class="icon-grid">
            <button 
              v-for="icon in icons" 
              :key="icon"
              :class="['icon-btn', { active: selectedIcon === icon }]"
              @click="selectedIcon = icon"
            >
              {{ icon }}
            </button>
          </div>
        </div>

        <!-- Title Section -->
        <div class="section">
          <input 
            v-model="title"
            type="text" 
            class="line-input title-input" 
            placeholder="Arena Title (e.g. Secret Coffee Shop)"
            autofocus
          />
        </div>

        <!-- Description Section -->
        <div class="section">
          <textarea 
            v-model="description"
            class="line-input desc-input" 
            placeholder="What's the vibe? (e.g. Casual talk with a stranger...)"
            rows="2"
          ></textarea>
        </div>
      </div>

      <div class="modal-footer">
        <button 
          class="create-btn" 
          :disabled="!title || isSubmitting"
          @click="handleSubmit"
        >
          <span v-if="!isSubmitting">✨ Manifest Scenario</span>
          <span v-else class="loading">
            <span class="dot">.</span><span class="dot">.</span><span class="dot">.</span>
            Generating AI Logic
          </span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(20px);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.4s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.creation-modal {
  width: 500px;
  background: rgba(30, 41, 59, 0.7);
  backdrop-filter: blur(40px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 32px;
  padding: 40px;
  box-shadow: 0 40px 100px rgba(0, 0, 0, 0.5);
  animation: slideIn 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes slideIn {
  from { opacity: 0; transform: translateY(40px) scale(0.95); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 40px;
}

.step-label {
  font-size: 0.7rem;
  font-weight: 900;
  color: #3b82f6;
  text-transform: uppercase;
  letter-spacing: 0.2em;
}

.close-btn {
  background: none;
  border: none;
  color: #64748b;
  font-size: 1.2rem;
  cursor: pointer;
  transition: color 0.2s;
}

.close-btn:hover { color: white; }

.section {
  margin-bottom: 24px;
}

.section label {
  display: block;
  font-size: 0.75rem;
  font-weight: 700;
  color: #94a3b8;
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.icon-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
}

.icon-btn {
  aspect-ratio: 1;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  font-size: 1.5rem;
  cursor: pointer;
  transition: all 0.2s;
}

.icon-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: translateY(-2px);
}

.icon-btn.active {
  background: rgba(59, 130, 246, 0.2);
  border-color: #3b82f6;
  box-shadow: 0 0 20px rgba(59, 130, 246, 0.2);
}

.line-input {
  width: 100%;
  background: transparent;
  border: none;
  border-bottom: 2px solid rgba(255, 255, 255, 0.1);
  padding: 12px 0;
  color: white;
  outline: none;
  transition: border-color 0.3s;
}

.line-input:focus {
  border-color: #3b82f6;
}

.title-input {
  font-size: 1.4rem;
  font-weight: 800;
}

.desc-input {
  font-size: 1rem;
  resize: none;
  color: #94a3b8;
}

.modal-footer {
  margin-top: 40px;
}

.create-btn {
  width: 100%;
  background: #3b82f6;
  color: white;
  border: none;
  padding: 16px;
  border-radius: 16px;
  font-weight: 800;
  font-size: 1rem;
  cursor: pointer;
  box-shadow: 0 10px 20px rgba(59, 130, 246, 0.3);
  transition: all 0.3s;
}

.create-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 15px 30px rgba(59, 130, 246, 0.4);
  background: #2563eb;
}

.create-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading .dot {
  animation: blink 1.4s infinite;
  opacity: 0;
}

.loading .dot:nth-child(2) { animation-delay: 0.2s; }
.loading .dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes blink {
  0% { opacity: 0; }
  50% { opacity: 1; }
  100% { opacity: 0; }
}
</style>
