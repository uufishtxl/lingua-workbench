<script setup lang="ts">
import { computed, ref } from 'vue';
import type { Scenario } from '@/api/englishCornerApi';

const props = defineProps<{
  activeId?: number;
  scenarios: Scenario[];
}>();

const emit = defineEmits(['select', 'add-request']);

const handleSelect = (scenario: Scenario) => {
  emit('select', scenario);
};

const allItems = computed(() => {
  const items: any[] = [];
  
  // The very first item is ALWAYS the Add Scenario block
  items.push({ type: 'add' });
  
  // Followed by valid scenarios
  const validScenarios = (props.scenarios || []).filter(i => !!i);
  validScenarios.forEach(s => {
    items.push({ type: 'scenario', data: s });
  });
  
  // Pad with ghost placeholders until length is a multiple of 3
  while (items.length % 3 !== 0) {
    items.push({ type: 'placeholder' });
  }
  
  // Chunk into arrays of length 3
  const chunks = [];
  for (let i = 0; i < items.length; i += 3) {
    chunks.push(items.slice(i, i + 3));
  }
  return chunks;
});

const carouselRef = ref<any>(null);
let wheelTimeout: ReturnType<typeof setTimeout> | null = null;

const handleWheel = (e: WheelEvent) => {
  if (wheelTimeout || !carouselRef.value) return;

  if (e.deltaY > 0) {
    carouselRef.value.next();
  } else if (e.deltaY < 0) {
    carouselRef.value.prev();
  }

  wheelTimeout = setTimeout(() => {
    wheelTimeout = null;
  }, 400); // 400ms throttle to prevent hyperscrolling
};
</script>

<template>
  <div class="scenario-selector-overlay">
    <div class="carousel-wrapper">
      <el-carousel 
        ref="carouselRef"
        :autoplay="false" 
        arrow="never" 
        trigger="click" 
        height="400px"
        class="scenario-carousel"
      >
        <el-carousel-item v-for="(chunk, pageIndex) in allItems" :key="pageIndex">
          <div class="carousel-slide-content" @wheel.prevent="handleWheel">
            <template v-for="(item, i) in chunk" :key="i">
              
              <!-- 1. Add New Scenario Card -->
              <div v-if="item.type === 'add'" class="scenario-card ghost-card add-card" @click="emit('add-request')">
                <div class="ghost-content">
                  <div class="plus-icon">+</div>
                  <div class="label">New Scenario</div>
                </div>
              </div>

              <!-- 2. Existing Scenario Card -->
              <div 
                v-else-if="item.type === 'scenario'" 
                :class="['scenario-card', { active: activeId === item.data.id }]"
                @click="handleSelect(item.data)"
              >
                <div class="icon">{{ item.data.icon }}</div>
                <div class="content">
                  <div class="title">{{ item.data.title }}</div>
                  <div class="desc">{{ item.data.description || 'No description found...' }}</div>
                  <div class="dialogue-rounds">
                    Dialogues: <span>{{ item.data.dialogue_rounds || 0 }}</span> rounds
                  </div>
                </div>
              </div>

              <!-- 3. Empty Placeholder Card (Padding) -->
              <div v-else-if="item.type === 'placeholder'" class="scenario-card placeholder-card">
              </div>

            </template>
          </div>
        </el-carousel-item>
      </el-carousel>
    </div>
  </div>
</template>

<style scoped>
.scenario-selector-overlay {
  width: 100%;
  padding: 40px 60px;
  background: linear-gradient(to top, rgba(15, 23, 42, 0.95), rgba(15, 23, 42, 0.7));
  backdrop-filter: blur(12px);
  display: flex;
  justify-content: center;
}

.carousel-wrapper {
  width: 100%;
  max-width: 1200px;
}

.scenario-carousel {
  width: 100%;
}

.carousel-slide-content {
  display: flex;
  justify-content: center;
  align-items: stretch;
  gap: 24px;
  height: 100%;
  padding: 10px 20px 30px;
}

:deep(.el-carousel__indicators--horizontal) {
  bottom: 0px;
}

:deep(.el-carousel__indicator .el-carousel__button) {
  background-color: rgba(255, 255, 255, 0.2);
  height: 4px;
  width: 24px;
  border-radius: 2px;
  transition: all 0.3s;
}

:deep(.el-carousel__indicator.is-active .el-carousel__button) {
  background-color: #3b82f6;
  width: 40px;
}

.scenario-card {
  flex-shrink: 0;
  width: 340px;
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
  transform: translateY(-5px) scale(1.02);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
}

.ghost-card {
  background: rgba(255, 255, 255, 0.02);
  border: 1px dashed rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.add-card:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: #fbbf24;
  box-shadow: 0 0 20px rgba(251, 191, 36, 0.2);
  transform: translateY(-5px);
}

.placeholder-card {
  opacity: 0.3;
  cursor: default;
  pointer-events: none;
}

.ghost-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: #64748b;
  transition: color 0.3s;
}

.add-card:hover .ghost-content {
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

.content {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.title {
  font-size: 1.1rem;
  font-weight: 800;
  color: white;
  letter-spacing: -0.01em;
  margin-bottom: 8px;
}

.desc {
  font-size: 0.85rem;
  color: #94a3b8;
  line-height: 1.5;
  overflow: hidden;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 6; /* Shorter limit */
  line-clamp: 6;
  text-align: justify;
}

.dialogue-rounds {
  margin-top: auto;
  padding-top: 16px;
  font-size: 0.75rem;
  font-weight: 700;
  color: #475569;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  border-top: 1px dashed rgba(255, 255, 255, 0.05);
  display: flex;
  align-items: center;
  gap: 8px;
}

.dialogue-rounds span {
  color: #fbbf24;
  font-size: 1.1rem;
}
</style>
