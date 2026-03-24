<script setup lang="ts">
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue';
import { englishCornerApi, type Scenario, type PracticeMessage, type WordNode } from '@/api/englishCornerApi';

const emit = defineEmits(['vocab-extracted', 'extract-vocab']);

const props = defineProps<{
  scenarioId?: number;
}>();

const messages = ref<UIMessage[]>([]);
const vocabs = ref<WordNode[]>([]); 
const isCollapsed = ref(false);
const scenarioTitle = ref('Loading...');
const scenarioSummary = ref('');
const showScenarioMenu = ref(false);
const availableScenarios = ref<Scenario[]>([]);
const inputText = ref('');
const textareaRef = ref<HTMLTextAreaElement | null>(null);
const currentConversationId = ref<number | null>(null);
const isLoading = ref(false);
const scrollContainerRef = ref<HTMLElement | null>(null);
const hasMore = ref(false);
const isLoadingMore = ref(false);
const messageOffset = ref(0);
const PAGE_SIZE = 10;

// Helper to map backend's PracticeMessage to our frontend state if needed.
// Since we now use the backend's PracticeMessage interface directly from API,
// we just adapt it slightly (adding sender_name/avatar for UI)
type UIMessage = PracticeMessage & { sender_name: string; avatar?: string };

const mapBackendToFrontendMessage = (msg: PracticeMessage): UIMessage => {
  const isAI = msg.role === 'assistant';
  return {
    ...msg,
    sender_name: isAI ? 'AI Partner' : 'You',
    avatar: `https://api.dicebear.com/7.x/avataaars/svg?seed=${isAI ? 'Assistant' : 'Felix'}`,
  };
};

const scrollToBottom = (behavior: 'smooth' | 'auto' = 'smooth') => {
  nextTick(() => {
    if (scrollContainerRef.value) {
      scrollContainerRef.value.scrollTo({ top: scrollContainerRef.value.scrollHeight, behavior });
    }
  });
};

const initConversation = async () => {
  if (!props.scenarioId) return;
  
  isLoading.value = true;
  try {
    const scenariosRes = await englishCornerApi.getScenarios();
    availableScenarios.value = scenariosRes.data;
    
    const activeScenario = availableScenarios.value.find(s => s.id === props.scenarioId);
    if (activeScenario) {
      scenarioTitle.value = activeScenario.title;
    }

    const convRes = await englishCornerApi.createConversation(props.scenarioId);
    currentConversationId.value = convRes.data.id;
    scenarioSummary.value = convRes.data.summary || 'Starting a new conversation...';
    
    // Load initial messages
    messageOffset.value = 0;
    const msgsRes = await englishCornerApi.getMessages(currentConversationId.value, messageOffset.value, PAGE_SIZE);
    messages.value = msgsRes.data.results.map(mapBackendToFrontendMessage);
    hasMore.value = msgsRes.data.has_more;

    scrollToBottom('auto'); // Jump to bottom for existing history

    const graphRes = await englishCornerApi.getGraph();
    vocabs.value = graphRes.data.nodes;

  } catch (err) {
    console.error('Failed to initialize conversation:', err);
  } finally {
    isLoading.value = false;
  }
};

const sendMessage = async () => {
  if (!inputText.value.trim() || !currentConversationId.value || isLoading.value) return;
  
  const text = inputText.value.trim();
  inputText.value = '';
  
  const tempId = Date.now();
  messages.value.push({
    id: tempId,
    role: 'user',
    status: 'PENDING',
    is_processed: false,
    sender_name: 'You',
    user_content: text,
    timestamp: new Date().toISOString(),
    tutor_feedback: null,
    character_reply: null
  });

  scrollToBottom(); // Scroll to show user's pending message

  try {
    const res = await englishCornerApi.sendMessage(currentConversationId.value, text);
    
    // The backend returns { message_id: 123 } (202 Accepted pattern).
    // Let's replace the temp ID so we can poll it later block
    const userMsg = messages.value.find(m => m.id === tempId);
    if (userMsg) {
       userMsg.id = res.data.message_id;
       userMsg.status = 'PROCESSING';
       
       // Start polling for this message
       pollMessage(res.data.message_id);
    }

  } catch (err) {
    console.error('Failed to send message:', err);
    const userMsg = messages.value.find(m => m.id === tempId);
    if (userMsg) userMsg.status = 'FAILED';
  }
};

const pollMessage = async (messageId: number) => {
  if (!currentConversationId.value) return;
  try {
    const res = await englishCornerApi.getMessage(currentConversationId.value, messageId);
    
    const idx = messages.value.findIndex(m => m.id === messageId);
    if (idx !== -1) {
      messages.value[idx] = mapBackendToFrontendMessage(res.data);
      if (res.data.status !== 'SUCCESS' && res.data.status !== 'FAILED') {
        setTimeout(() => pollMessage(messageId), 2000);
      } else if (res.data.status === 'SUCCESS') {
        messages.value[idx] = mapBackendToFrontendMessage(res.data);
        
        // The backend creates a completely new PracticeMessage for the AI character's reply.
        // Fetch the most recent messages and append any new ones we don't have natively yet.
        const recentMsgsRes = await englishCornerApi.getMessages(currentConversationId.value, 0, 5);
        const recentMsgs = recentMsgsRes.data.results.map(mapBackendToFrontendMessage);
        // recentMsgs are newest first from backend API, so we reverse it to append in chronological order
        for (const newMsg of recentMsgs.reverse()) {
          if (!messages.value.find(m => m.id === newMsg.id)) {
            messages.value.push(newMsg);
          }
        }
        
        scrollToBottom(); // Scroll to show AI's reply
      }
    }
  } catch (err) {
    console.error("Failed to poll message status", err);
  }
};

const handleScroll = async (e: Event) => {
  const target = e.target as HTMLElement;
  if (target.scrollTop === 0 && hasMore.value && !isLoadingMore.value && currentConversationId.value) {
    isLoadingMore.value = true;
    try {
      const oldHeight = target.scrollHeight; // Save old height to restore scroll position

      messageOffset.value += PAGE_SIZE;
      const msgsRes = await englishCornerApi.getMessages(currentConversationId.value, messageOffset.value, PAGE_SIZE);
      const newMessages = msgsRes.data.results.map(mapBackendToFrontendMessage);
      
      // Prepend the older messages (deduplicate just in case offset shifted due to newly sent messages)
      const uniqueOldMessages = newMessages.filter(n => !messages.value.find(m => m.id === n.id));
      messages.value = [...uniqueOldMessages, ...messages.value];
      hasMore.value = msgsRes.data.has_more;

      // Restore scroll position
      nextTick(() => {
        target.scrollTop = target.scrollHeight - oldHeight;
      });
    } catch (err) {
      console.error("Failed to load more history:", err);
    } finally {
      isLoadingMore.value = false;
    }
  }
};

defineExpose({
  jumpToMessage: async (msgId: number) => {
    let maxTries = 10;
    while (messages.value.findIndex(m => m.id === msgId) === -1 && hasMore.value && maxTries > 0) {
      if (scrollContainerRef.value) {
        await handleScroll({ target: scrollContainerRef.value } as any);
      }
      maxTries--;
    }

    const idx = messages.value.findIndex(m => m.id === msgId);
    if (idx !== -1) {
      nextTick(() => {
        const msgEl = document.getElementById(`msg-${msgId}`);
        if (msgEl) {
          msgEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
          msgEl.classList.add('highlight-msg');
          setTimeout(() => msgEl.classList.remove('highlight-msg'), 2000);
        }
      });
    } else {
      console.warn("Could not find message:", msgId);
    }
  }
});

const selectionInfo = ref<{ text: string; rect: DOMRect; messageId?: number } | null>(null);

const handleTextSelection = (info: { text: string; rect: DOMRect }, messageId?: number) => {
  selectionInfo.value = { ...info, messageId };
};

const isExtracting = ref(false);

const extractVocab = () => {
  if (!selectionInfo.value || isExtracting.value) return;
  
  isExtracting.value = true;
  try {
    const text = selectionInfo.value.text.trim();
    const isPhrase = text.includes(' ');
    
    const newWord: WordNode = {
      id: Date.now(), // Fallback before actual backend ID
      label: text,
      node_type: isPhrase ? 'phrase' : 'keyword',
      explanation: 'Extracted...',
      example: '...',
      mastery: 0,
      status: 'PENDING',
      box_level: 1
    };
    const msgId = selectionInfo.value.messageId;
    selectionInfo.value = null;
    window.getSelection()?.removeAllRanges();
    
    emit('extract-vocab', { word: newWord, scenarioId: props.scenarioId, messageId: msgId });
    vocabs.value.push(newWord);
    
    nextTick(() => {
      isExtracting.value = false;
    });
  } catch (err) {
    console.error('Extraction failed:', err);
    isExtracting.value = false;
    selectionInfo.value = null;
  }
};

const playAudio = (url: string | null) => {
  if (!url) return;
  // Fallback normalize for Windows paths and missing prefixes
  let finalUrl = url.replace(/\\/g, '/');
  
  if (!finalUrl.startsWith('http')) {
    if (!finalUrl.startsWith('/')) {
      // If it doesn't start with /, maybe it's just the file path without /media/
      if (!finalUrl.startsWith('media/')) {
        finalUrl = '/media/' + finalUrl;
      } else {
        finalUrl = '/' + finalUrl;
      }
    }
    // Now it definitely starts with /media/ or /...
    // Prepend Dev Backend URL if in dev mode
    finalUrl = import.meta.env.VITE_DEV_BACKEND_URL 
               ? `${import.meta.env.VITE_DEV_BACKEND_URL}${finalUrl}` 
               : finalUrl;
  }
  
  const audio = new Audio(finalUrl);
  audio.play().catch(e => console.error('Audio playback failed:', e));
};

const formatTime = (timestamp: string) => {
  if (!timestamp) return '';
  return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

const autoResize = () => {
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto';
    textareaRef.value.style.height = textareaRef.value.scrollHeight + 'px';
  }
};

const closeExtraction = (e: MouseEvent) => {
  if (selectionInfo.value) {
    const tooltip = document.querySelector('.extract-tooltip');
    if (tooltip && !tooltip.contains(e.target as Node)) {
      selectionInfo.value = null;
      window.getSelection()?.removeAllRanges();
    }
  }
};

const switchScenario = (s: Scenario) => {
  scenarioTitle.value = s.title;
  showScenarioMenu.value = false;
  // This should actually emit something or change scenarioId
};

onMounted(() => {
  window.addEventListener('mousedown', closeExtraction);
  initConversation();
});

onUnmounted(() => {
  window.removeEventListener('mousedown', closeExtraction);
});

watch(() => props.scenarioId, () => {
  initConversation();
});

watch(inputText, () => {
  nextTick(autoResize);
});
</script>

<template>
  <div :class="['floating-sidebar', { collapsed: isCollapsed }]">
    <div class="sidebar-handle" @click="isCollapsed = !isCollapsed">
      <span v-if="isCollapsed">❯</span>
      <span v-else>❮</span>
    </div>

    <div class="sidebar-content" v-show="!isCollapsed">
      <div class="chat-header">
        <div class="header-main" @click="showScenarioMenu = !showScenarioMenu">
          <h3>{{ scenarioTitle }}</h3>
          <span class="chevron" :class="{ open: showScenarioMenu }">▼</span>
        </div>
        <div v-if="showScenarioMenu" class="scenario-menu">
          <div 
            v-for="s in availableScenarios" 
            :key="s.id" 
            class="scenario-item"
            @click="switchScenario(s)"
          >
            <span class="icon">{{ s.icon }}</span>
            <div class="info">
              <div class="title">{{ s.title }}</div>
              <div class="desc">{{ s.description }}</div>
            </div>
          </div>
        </div>
        <div class="summary-pill">{{ scenarioSummary }}</div>
      </div>

      <div class="message-list" ref="scrollContainerRef" @scroll="handleScroll">
        <!-- Loading spinner for history -->
        <div v-if="isLoadingMore" class="history-loader">
          Loading history...
        </div>

        <div 
          v-for="msg in messages" 
          :key="msg.id" 
          :id="'msg-' + msg.id"
          :class="['message-item', msg.role]"
        >
          <!-- Avatar -->
          <img v-if="msg.avatar" :src="msg.avatar" class="avatar" :alt="msg.sender_name" />
          
          <div class="bubble-wrapper">
            <div class="sender-name">{{ msg.sender_name }}</div>
            
            <div class="bubble">
              <!-- Character Content -->
              <div v-if="msg.character_reply" class="character-section">
                <VocabRichText 
                  :text="msg.character_reply.content" 
                  :vocabs="vocabs"
                  @select-text="handleTextSelection($event, msg.id)"
                />
                <button 
                  v-if="msg.character_reply.audio_url" 
                  class="audio-btn"
                  @click="playAudio(msg.character_reply.audio_url)"
                >
                  🔊
                </button>
              </div>

              <!-- User Content -->
              <div v-if="msg.user_content" class="user-section">
                <VocabRichText 
                  class="user-text"
                  :text="msg.user_content" 
                  :vocabs="vocabs"
                  @select-text="handleTextSelection($event, msg.id)"
                />
                
                <!-- Refactored Tutor Feedback -->
                <div v-if="msg.tutor_feedback" class="inline-feedback">
                  <div class="feedback-line"></div>
                  <div class="feedback-content">
                    <div class="polished">
                      <span class="label">Polished:</span>
                      <VocabRichText 
                        class="text"
                        :text="msg.tutor_feedback.polished_text" 
                        :vocabs="vocabs"
                        @select-text="handleTextSelection($event, msg.id)"
                      />
                    </div>
                    <div class="explanation">
                      {{ msg.tutor_feedback.explanation_cn }}
                    </div>
                  </div>
                </div>
              </div>
              
              <div class="msg-meta">
                {{ formatTime(msg.timestamp) }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="input-area">
        <textarea 
          ref="textareaRef"
          v-model="inputText"
          placeholder="Shift + Enter for new line..." 
          rows="1"
          @input="autoResize"
          @keydown.enter.prevent="sendMessage"
        ></textarea>
        <div class="actions">
          <button class="voice-btn">🎤</button>
          <button class="send-btn" :disabled="!inputText.trim()" @click="sendMessage">Send</button>
        </div>
      </div>
    </div>

    <!-- Floating Extraction Tooltip -->
    <Teleport to="body">
      <div 
        v-if="selectionInfo" 
        class="extract-tooltip"
        :style="{ 
          left: selectionInfo.rect.left + selectionInfo.rect.width/2 + 'px', 
          top: selectionInfo.rect.top + 'px' 
        }"
      >
        <button class="extract-btn" @click="extractVocab">
          ✨ Extract to Graph
        </button>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.floating-sidebar {
  position: fixed;
  top: 20px;
  right: 20px;
  bottom: 20px;
  width: 800px;
  background: rgba(15, 23, 42, 0.5);
  backdrop-filter: blur(24px) saturate(180%);
  -webkit-backdrop-filter: blur(24px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  display: flex;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.6);
  transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  z-index: 100;
}

.floating-sidebar.collapsed {
  transform: translateX(calc(100% - 40px));
}

.sidebar-handle {
  width: 40px;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #64748b;
  font-size: 14px;
  border-right: 1px solid rgba(255, 255, 255, 0.05);
}

.sidebar-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Header & Scenario Switching */
.chat-header {
  padding: 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  position: relative;
}

.header-main {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.header-main h3 {
  margin: 0;
  color: #f8fafc;
  font-size: 1.1rem;
  font-weight: 700;
}

.chevron {
  font-size: 10px;
  color: #64748b;
  transition: transform 0.3s;
}

.chevron.open { transform: rotate(180deg); }

.scenario-menu {
  position: absolute;
  top: 70px;
  left: 20px;
  right: 20px;
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
  z-index: 150;
  overflow: hidden;
}

.scenario-item {
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 16px;
  cursor: pointer;
  transition: background 0.2s;
}

.scenario-item:hover { background: #334155; }

.scenario-item .icon { font-size: 1.5rem; }

.scenario-item .title { font-weight: 600; color: #f8fafc; font-size: 0.9rem; }

.scenario-item .desc { font-size: 0.75rem; color: #94a3b8; }

.summary-pill {
  font-size: 0.8rem;
  color: #94a3b8;
  margin-top: 10px;
  line-height: 1.5;
}

/* Message List & Bubbles */
.message-list {
  flex: 1;
  min-height: 0; /* Crucial: allows flex child to shrink and scroll inside the sidebar */
  padding: 24px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.message-item {
  display: flex;
  gap: 12px;
  max-width: 90%;
}

.message-item.ai { align-self: flex-start; }

.message-item.user { 
  align-self: flex-end; 
  flex-direction: row-reverse; 
}

.highlight-msg {
  animation: pulse-border 2s ease-out;
}

@keyframes pulse-border {
  0% { box-shadow: 0 0 0 0 rgba(251, 191, 36, 0.7); border-radius: 16px; }
  70% { box-shadow: 0 0 0 20px rgba(251, 191, 36, 0); border-radius: 16px; }
  100% { box-shadow: 0 0 0 0 rgba(251, 191, 36, 0); border-radius: 16px; }
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: #334155;
  flex-shrink: 0;
}

.bubble-wrapper {
  display: flex;
  flex-direction: column;
}

.sender-name {
  font-size: 0.7rem;
  font-weight: 700;
  color: #64748b;
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.user .sender-name { text-align: right; }

.bubble {
  padding: 16px;
  border-radius: 16px;
  font-size: 0.95rem;
  line-height: 1.6;
}

.ai .bubble {
  background: rgba(30, 41, 59, 0.5);
  color: #e2e8f0;
  border-top-left-radius: 4px;
}

.user .bubble {
  background: rgba(37, 99, 235, 0.15); /* Soft Blue Tint */
  color: #60a5fa;
  border-top-right-radius: 4px;
}

.user-text { margin: 0; font-weight: 500; }

.audio-btn {
  background: none;
  border: none;
  color: #fbbf24;
  cursor: pointer;
  padding: 0;
  font-size: 0.9rem;
  margin-top: 8px;
  opacity: 0.7;
}

/* Feedback Styling */
.inline-feedback {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  display: flex;
  gap: 12px;
}

.feedback-line {
  width: 2px;
  background: #f43f5e;
  border-radius: 2px;
  opacity: 0.5;
}

.feedback-content { flex: 1; font-size: 0.82rem; }

.polished .label {
  color: #94a3b8;
  margin-right: 6px;
  font-size: 0.7rem;
  font-weight: 800;
}

.polished .text { color: #cbd5e1; }

.explanation { color: #64748b; margin-top: 4px; }

.msg-meta {
  font-size: 0.7rem;
  color: #475569;
  margin-top: 8px;
}

.user .msg-meta { text-align: right; }

/* Input Area */
.input-area {
  padding: 24px;
  background: rgba(15, 23, 42, 0.3);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.input-area textarea {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 12px 16px;
  color: white;
  width: 100%;
  outline: none;
  resize: none;
  font-size: 0.95rem;
  line-height: 1.5;
  max-height: 150px;
  transition: border-color 0.2s;
}

.input-area textarea:focus { border-color: #3b82f6; }

.actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.voice-btn, .send-btn {
  border: none;
  color: white;
  padding: 10px 24px;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
}

.voice-btn { background: rgba(255, 255, 255, 0.05); }

.send-btn { background: #2563eb; }

.send-btn:disabled { opacity: 0.3; cursor: not-allowed; }

/* Extraction Tooltip */
.extract-tooltip {
  position: fixed;
  z-index: 2100;
  transform: translate(-50%, -100%) translateY(-10px);
  animation: popIn 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes popIn {
  from { opacity: 0; transform: translate(-50%, -100%) translateY(0); }
  to { opacity: 1; transform: translate(-50%, -100%) translateY(-10px); }
}

.extract-btn {
  background: #fbbf24;
  color: #0f172a;
  border: none;
  padding: 8px 16px;
  border-radius: 99px;
  font-size: 0.8rem;
  font-weight: 800;
  cursor: pointer;
  white-space: nowrap;
  box-shadow: 0 10px 20px rgba(251, 191, 36, 0.4);
  transition: all 0.2s;
}

.extract-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 15px 30px rgba(251, 191, 36, 0.6);
}

/* Scrollbar */
.message-list::-webkit-scrollbar { width: 4px; }
.message-list::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 10px; }
</style>
