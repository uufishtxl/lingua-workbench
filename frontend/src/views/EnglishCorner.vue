<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import KnowledgeGraph from '@/components/english-corner/KnowledgeGraph.vue';
import ChatInterface from '@/components/english-corner/ChatInterface.vue';
import ScenarioSelector from '@/components/english-corner/ScenarioSelector.vue';
import ScenarioCreationModal from '@/components/english-corner/ScenarioCreationModal.vue';
import { englishCornerApi } from '@/api/englishCornerApi';
import type { Scenario, WordNode } from '@/api/englishCornerApi';
import { useRouter } from 'vue-router';

const router = useRouter();
const scenarios = ref<Scenario[]>([]);
const graphData = ref<{ nodes: WordNode[], links: any[] }>({ nodes: [], links: [] });
const chatRef = ref<any>(null);

const loading = ref(true);

const fetchInitialData = async () => {
  loading.value = true;
  try {
    const scenariosRes = await englishCornerApi.getScenarios();
    scenarios.value = scenariosRes.data;
    
    if (Array.isArray(scenarios.value) && scenarios.value.length > 0 && !currentScenarioId.value) {
      currentScenarioId.value = scenarios.value[0]?.id;
    }
    
    // Initial graph fetch (with scenario filter if exists)
    await refreshGraph();
  } catch (err) {
    console.error('Failed to fetch English Corner data:', err);
  } finally {
    loading.value = false;
  }
};

const goHome = () => {
  router.push('/');
};

// Scenario Selector & Creation Logic
const showScenarioSelector = ref(false);
const showCreationModal = ref(false);
const currentScenarioId = ref<number | undefined>(undefined);
const hoverTimer = ref<any>(null);

const onIndicatorHover = () => {
  hoverTimer.value = setTimeout(() => {
    showScenarioSelector.value = true;
  }, 500); // 0.5s intent hover
};

const clearHoverTimer = () => {
  if (hoverTimer.value) {
    clearTimeout(hoverTimer.value);
    hoverTimer.value = null;
  }
};

const handleScenarioSelect = async (scenario: Scenario) => {
  currentScenarioId.value = scenario.id;
  showScenarioSelector.value = false;
  await refreshGraph();
};

const handleAddRequest = () => {
  showScenarioSelector.value = false;
  showCreationModal.value = true;
};

const handleCreateScenario = async (data: { icon: string, title: string, description: string }) => {
  try {
    const res = await englishCornerApi.createScenario({
      title: data.title,
      description: data.description,
      icon: data.icon,
    });
    scenarios.value.push(res.data);
    currentScenarioId.value = res.data.id;
    showCreationModal.value = false;
    await refreshGraph();
  } catch (err) {
    console.error('Failed to create scenario:', err);
  }
};

const handleExtractVocab = async (payload: { word: WordNode, scenarioId?: number, messageId?: number }) => {
  try {
    await englishCornerApi.extractVocab({
      text: payload.word.label,
      scenario_id: payload.scenarioId,
      message_id: payload.messageId,
      context_sentence: payload.word.example
    });
    await refreshGraph();
  } catch (err) {
    console.error('Failed to extract vocabulary:', err);
  }
};

const refreshGraph = async () => {
  try {
    const res = await englishCornerApi.getGraph(currentScenarioId.value);
    graphData.value = {
      ...res.data,
      nodes: res.data.nodes.map(n => ({
        ...n,
        mastery: Math.min(100, n.mastery + Math.floor(Math.random() * 2))
      }))
    };
  } catch (err) {
    console.error('Failed to refresh graph:', err);
  }
};

const handleNodeClick = (nodeData: any) => {
  if (chatRef.value && nodeData.message_ids?.length) {
    // Jump to the MOST RECENT message that contains this vocab
    const msgIdstr = nodeData.message_ids[nodeData.message_ids.length - 1];
    chatRef.value.jumpToMessage(Number(msgIdstr));
  }
};

const closeSelector = (e: MouseEvent) => {
  if (showScenarioSelector.value) {
    const selector = document.querySelector('.scenario-selector-container');
    const indicator = document.querySelector('.home-indicator-trigger');
    if (selector && !selector.contains(e.target as Node) && indicator && !indicator.contains(e.target as Node)) {
      showScenarioSelector.value = false;
    }
  }
};

onMounted(() => {
  window.addEventListener('mousedown', closeSelector);
  fetchInitialData();
});

onUnmounted(() => {
  window.removeEventListener('mousedown', closeSelector);
});
</script>

<template>
  <div class="immersive-screen">
    <!-- Level 0: Background Canvas (Full Screen) -->
    <KnowledgeGraph :data="graphData" @node-click="handleNodeClick" />

    <!-- Level 1: Home Escape Pod (Left Sensor) -->
    <div class="home-sensor-zone">
      <button class="home-btn" @click="goHome">
        <span class="home-icon">🏠</span>
        <span class="label">HOME</span>
      </button>
    </div>

    <!-- Level 2: UI Overlays -->
    <div class="top-stats">
      <div class="stat-item">
        <span class="label">VOCABULARIES</span>
        <span class="value">{{ graphData.nodes.length }}</span>
      </div>
      <div class="stat-item">
        <span class="label">PRACTICE STREAK</span>
        <span class="value">1 Day</span>
      </div>
      <div class="stat-item">
        <span class="label">MASTERY</span>
        <span class="value">64%</span>
      </div>
    </div>

    <!-- Level 3: Interactive Floating Panels -->
    <ChatInterface 
      ref="chatRef"
      v-if="currentScenarioId" 
      :scenario-id="currentScenarioId" 
      @extract-vocab="handleExtractVocab" 
    />

    <!-- Level 4: Bottom Navigation (Scenario Switcher) -->
    <div 
      class="home-indicator-trigger"
      @mouseenter="onIndicatorHover"
      @mouseleave="clearHoverTimer"
      @click="showScenarioSelector = !showScenarioSelector"
    >
      <div class="indicator-bar"></div>
      <span class="scenario-name">{{ (Array.isArray(scenarios) && scenarios.find(s => s && s.id === currentScenarioId)?.title) || 'SELECT SCENARIO' }}</span>
    </div>

    <Transition name="slide-up">
      <div v-if="showScenarioSelector" class="scenario-selector-container">
        <ScenarioSelector 
          :active-id="currentScenarioId" 
          :scenarios="scenarios"
          @select="handleScenarioSelect" 
          @add-request="handleAddRequest"
        />
      </div>
    </Transition>

    <Transition name="fade-scale">
      <ScenarioCreationModal 
        v-if="showCreationModal"
        @close="showCreationModal = false"
        @create="handleCreateScenario"
      />
    </Transition>
    
    <!-- Level 5: Atmosphere Layer -->
    <div class="vignette"></div>
  </div>
</template>

<style scoped>
.immersive-screen {
  position: relative;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  color: #f8fafc;
}

/* Home Escape Pod - Left Edge Sensor */
.home-sensor-zone {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: 12px;
  z-index: 1000;
  display: flex;
  align-items: center;
  transition: width 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.home-sensor-zone:hover {
  width: 120px;
  background: linear-gradient(to right, rgba(15, 23, 42, 0.8), transparent);
}

.home-btn {
  opacity: 0;
  transform: translateX(-20px);
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  background: none;
  border: none;
  color: #94a3b8;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  margin-left: 20px;
}

.home-sensor-zone:hover .home-btn {
  opacity: 1;
  transform: translateX(0);
}

.home-icon {
  font-size: 24px;
}

.home-btn .label {
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.15em;
}

.home-btn:hover {
  color: white;
  text-shadow: 0 0 15px rgba(255, 255, 255, 0.5);
}

.top-stats {
  position: fixed;
  top: 40px; /* Moved back up as Search/Filter are now hidden */
  left: 60px;
  display: flex;
  gap: 60px;
  z-index: 10;
  pointer-events: none;
}

.stat-item {
  display: flex;
  flex-direction: column;
}

.stat-item .label {
  font-size: 0.65rem;
  color: #475569;
  letter-spacing: 0.2em;
  font-weight: 800;
  margin-bottom: 6px;
}

.stat-item .value {
  font-size: 1.8rem;
  font-weight: 800;
  color: #f8fafc;
  font-family: 'Inter', sans-serif;
  letter-spacing: -0.02em;
}

.vignette {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  box-shadow: inset 0 0 200px rgba(0, 0, 0, 0.7);
  pointer-events: none;
  z-index: 5;
}

/* Bottom Scenario Switcher Trigger */
.home-indicator-trigger {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  padding: 12px 40px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  z-index: 1000;
  transition: all 0.3s;
}

.indicator-bar {
  width: 120px;
  height: 4px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 2px;
  transition: all 0.3s;
}

.scenario-name {
  font-size: 0.7rem;
  font-weight: 800;
  color: #64748b;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  opacity: 0;
  transform: translateY(10px);
  transition: all 0.3s;
}

.home-indicator-trigger:hover .indicator-bar {
  background: rgba(255, 255, 255, 0.5);
  box-shadow: 0 0 15px rgba(255, 255, 255, 0.2);
  width: 160px;
}

.home-indicator-trigger:hover .scenario-name {
  opacity: 1;
  transform: translateY(0);
}

.scenario-selector-container {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 1100;
}

/* Transitions */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(100%);
  opacity: 0;
}

/* Fade Scale Transition for Modal */
.fade-scale-enter-active,
.fade-scale-leave-active {
  transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}

.fade-scale-enter-from,
.fade-scale-leave-to {
  opacity: 0;
  transform: scale(0.9) translateY(20px);
}
</style>

<style>
/* Global Content Overrides for Widgets in English Corner View */
.immersive-screen ~ .chat-widget {
  left: 24px !important;
  right: auto !important;
  bottom: 24px !important;
}

.immersive-screen ~ .pomodoro-widget {
  left: 90px !important; /* Move it next to ChatWidget */
  right: auto !important;
  bottom: 24px !important;
}

/* Ensure ChatWidget button is not too high when moved to left */
.immersive-screen ~ .chat-widget .chat-toggle-btn {
  width: 48px;
  height: 48px;
}

.immersive-screen ~ .pomodoro-widget .pomodoro-toggle-btn {
  width: 48px;
  height: 48px;
  font-size: 11px;
}
</style>
