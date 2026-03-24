<script setup lang="ts">
import type { Scenario } from '@/api/englishCornerApi';

defineProps<{
  activeId?: number;
  scenarios: Scenario[];
}>();

const emit = defineEmits(['select', 'add-request']);

const handleSelect = (scenario: Scenario) => {
  emit('select', scenario);
};
</script>

<template>
  <div class="scenario-selector-overlay">
    <div class="carousel-container">
      <!-- Ghost Card for New Scenario -->
      <div class="scenario-card ghost-card" @click="emit('add-request')">
        <div class="ghost-content">
          <div class="plus-icon">+</div>
          <div class="label">New Scenario</div>
        </div>
      </div>

      <div 
        v-for="s in (scenarios || []).filter(i => !!i)" 
        :key="s.id" 
        :class="['scenario-card', { active: activeId === s.id }]"
        @click="handleSelect(s)"
      >
        <div class="icon">{{ s.icon }}</div>
        <div class="content">
          <div class="title">{{ s.title }}</div>
          <div class="desc">{{ s.description }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.scenario-selector-overlay {
  width: 100%;
  padding: 40px 60px;
  background: linear-gradient(to top, rgba(15, 23, 42, 0.9), transparent);
  backdrop-filter: blur(10px);
  display: flex;
  justify-content: center;
}

.carousel-container {
  display: flex;
  gap: 20px;
  max-width: 1200px;
  overflow-x: auto;
  padding: 20px;
  scrollbar-width: none;
}

.carousel-container::-webkit-scrollbar {
  display: none;
}

.scenario-card {
  flex-shrink: 0;
  width: 350px;
  background: rgba(30, 41, 59, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 24px;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.scenario-card:hover {
  background: rgba(30, 41, 59, 0.8);
  border-color: rgba(59, 130, 246, 0.5);
  transform: translateY(-10px) scale(1.02);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
}

.ghost-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px dashed rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.ghost-card:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: #fbbf24;
  box-shadow: 0 0 20px rgba(251, 191, 36, 0.2);
  transform: translateY(-10px);
}

.ghost-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: #64748b;
  transition: color 0.3s;
}

.ghost-card:hover .ghost-content {
  color: #fbbf24;
}

.plus-icon {
  font-size: 2.5rem;
  font-weight: 200;
  line-height: 1;
}

.ghost-content .label {
  font-size: 0.75rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.scenario-card.active {
  background: rgba(37, 99, 235, 0.2);
  border-color: #3b82f6;
  box-shadow: 0 0 30px rgba(59, 130, 246, 0.3);
}

.icon {
  font-size: 2.5rem;
  margin-bottom: 4px;
}

.title {
  font-size: 1.1rem;
  font-weight: 800;
  color: white;
  letter-spacing: -0.01em;
}

.desc {
  font-size: 0.85rem;
  color: #94a3b8;
  line-height: 1.5;
  max-height: 33vh;
  overflow: hidden;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 10; /* Clamp to 10 lines to ensure ellipsis within reasonable height */
  line-clamp: 10;
  text-align: justify;
}
</style>
