<script setup lang="ts">
/**
 * ChatWidget - Floating documentation assistant chatbot
 * 
 * Features:
 * - Collapsible floating button in bottom-right corner
 * - Expandable chat interface
 * - Role switching (User/Developer)
 * - SSE streaming for typewriter effect
 */
import { ref, nextTick, computed } from 'vue';
import { streamChatMessage, type ChatSource, type AudienceType } from '@/api/chatApi';

// Widget state
const isExpanded = ref(false);
const isLoading = ref(false);
const currentAudience = ref<AudienceType>('user');

// Chat state
interface ChatMessage {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  sources?: ChatSource[];
  isStreaming?: boolean;
}

const messages = ref<ChatMessage[]>([]);
const inputMessage = ref('');

const messagesContainer = ref<HTMLElement | null>(null);
const textareaRef = ref<HTMLTextAreaElement | null>(null);
let messageIdCounter = 0;

// Computed
const audienceLabel = computed(() => 
  currentAudience.value === 'developer' ? '👨‍💻 Developer' : '👤 User'
);

// Methods
function toggleWidget() {
  isExpanded.value = !isExpanded.value;
}

function toggleAudience() {
  currentAudience.value = currentAudience.value === 'user' ? 'developer' : 'user';
}

async function scrollToBottom() {
  await nextTick();
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
}

async function sendMessage() {
  const message = inputMessage.value.trim();
  if (!message || isLoading.value) return;
  
  // Add user message
  const userMessage: ChatMessage = {
    id: ++messageIdCounter,
    role: 'user',
    content: message,
  };
  messages.value.push(userMessage);
  inputMessage.value = '';
  
  // Add placeholder for assistant response
  const assistantMessage: ChatMessage = {
    id: ++messageIdCounter,
    role: 'assistant',
    content: '',
    isStreaming: true,
  };
  messages.value.push(assistantMessage);
  
  isLoading.value = true;
  await scrollToBottom();
  
  try {
    await streamChatMessage(
      message,
      currentAudience.value,
      {
        onToken: (token) => {
          assistantMessage.content += token;
          scrollToBottom();
        },
        onSources: (sources) => {
          assistantMessage.sources = sources;
        },
        onDone: () => {
          assistantMessage.isStreaming = false;
          isLoading.value = false;
        },
        onError: (error) => {
          assistantMessage.content = `❌ Error: ${error}`;
          assistantMessage.isStreaming = false;
          isLoading.value = false;
        },
      }
    );
  } catch (error) {
    assistantMessage.content = `❌ Error: ${error}`;
    assistantMessage.isStreaming = false;
    isLoading.value = false;
  }
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
}

function autoResize() {
  const el = textareaRef.value;
  if (el) {
    el.style.height = 'auto';
    el.style.height = el.scrollHeight + 'px';
  }
}
</script>

<template>
  <div class="chat-widget">
    <!-- Floating Button -->
    <button 
      v-if="!isExpanded"
      class="chat-toggle-btn"
      @click="toggleWidget"
      title="Ask Documentation"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
      </svg>
    </button>

    <!-- Expanded Chat Panel -->
    <div v-if="isExpanded" class="chat-panel">
      <!-- Header -->
      <div class="chat-header">
        <div class="chat-title">
          <span class="chat-icon">📚</span>
          <span>Doc Assistant</span>
        </div>
        <div class="chat-controls">
          <button 
            class="audience-toggle"
            @click="toggleAudience"
            :title="`Switch to ${currentAudience === 'user' ? 'Developer' : 'User'} mode`"
          >
            {{ audienceLabel }}
          </button>
          <button class="close-btn" @click="toggleWidget" title="Close">
            ✕
          </button>
        </div>
      </div>

      <!-- Messages -->
      <div class="chat-messages" ref="messagesContainer">
        <div v-if="messages.length === 0" class="chat-welcome">
          <p>👋 你好！我是文档助手。</p>
          <p>你可以问我任何关于 Lingua Workbench 的问题。</p>
          <div class="sample-questions">
            <button @click="inputMessage = '如何创建 slice?'">如何创建 slice?</button>
            <button @click="inputMessage = 'What are phonetic tags?'">What are phonetic tags?</button>
          </div>
        </div>

        <div
          v-for="msg in messages"
          :key="msg.id"
          :class="['chat-message', msg.role]"
        >
          <div class="message-content">
            {{ msg.content }}
            <span v-if="msg.isStreaming" class="typing-cursor">▊</span>
          </div>
          
          <!-- Sources -->
          <div v-if="msg.sources && msg.sources.length > 0" class="message-sources">
            <span class="sources-label">📄 Sources:</span>
            <span 
              v-for="(source, idx) in msg.sources" 
              :key="idx"
              class="source-tag"
              :title="source.path"
            >
              {{ source.title }}
            </span>
          </div>
        </div>
      </div>

      <!-- Input -->
      <div class="chat-input-area">
        <textarea
          ref="textareaRef"
          v-model="inputMessage"
          @keydown="handleKeydown"
          @input="autoResize"
          placeholder="Ask a question..."
          :disabled="isLoading"
          rows="1"
        ></textarea>
        <button 
          class="send-btn" 
          @click="sendMessage"
          :disabled="!inputMessage.trim() || isLoading"
        >
          <span v-if="isLoading" class="loading-spinner">⏳</span>
          <span v-else>➤</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-widget {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 9999;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* Floating Toggle Button */
.chat-toggle-btn {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s, box-shadow 0.2s;
}

.chat-toggle-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.5);
}

/* Chat Panel */
.chat-panel {
  width: 380px;
  height: 520px;
  background: #1a1a2e;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

/* Header */
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.chat-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 15px;
}

.chat-icon {
  font-size: 20px;
}

.chat-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.audience-toggle {
  padding: 4px 10px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.2s;
}

.audience-toggle:hover {
  background: rgba(255, 255, 255, 0.3);
}

.close-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

/* Messages Area */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chat-welcome {
  text-align: center;
  color: #a0a0b0;
  padding: 20px;
}

.chat-welcome p {
  margin: 8px 0;
}

.sample-questions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 16px;
}

.sample-questions button {
  padding: 10px 16px;
  background: rgba(102, 126, 234, 0.2);
  border: 1px solid rgba(102, 126, 234, 0.3);
  border-radius: 8px;
  color: #a0a0ff;
  cursor: pointer;
  font-size: 13px;
  text-align: left;
  transition: background 0.2s;
}

.sample-questions button:hover {
  background: rgba(102, 126, 234, 0.3);
}

/* Message Bubbles */
.chat-message {
  max-width: 85%;
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

.chat-message.user {
  align-self: flex-end;
}

.chat-message.assistant {
  align-self: flex-start;
}

.message-content {
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.chat-message.user .message-content {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-bottom-right-radius: 4px;
}

.chat-message.assistant .message-content {
  background: #2a2a40;
  color: #e0e0e8;
  border-bottom-left-radius: 4px;
}

.typing-cursor {
  animation: blink 0.8s infinite;
  color: #667eea;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* Sources */
.message-sources {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.sources-label {
  font-size: 11px;
  color: #808090;
}

.source-tag {
  padding: 2px 8px;
  background: rgba(102, 126, 234, 0.15);
  border-radius: 10px;
  font-size: 11px;
  color: #a0a0ff;
}

/* Input Area */
.chat-input-area {
  display: flex;
  padding: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  background: #16162a;
  gap: 8px;
}

.chat-input-area textarea {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  background: #2a2a40;
  color: #e0e0e8;
  font-size: 14px;
  resize: none;
  outline: none;
  font-family: inherit;
  line-height: 1.5;
  max-height: 125px; /* Approx 5 rows */
  overflow-y: auto;
  
  /* Hide scrollbar */
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE/Edge */
}

.chat-input-area textarea::-webkit-scrollbar {
  display: none; /* Chrome/Safari */
}

.chat-input-area textarea:focus {
  border-color: #667eea;
}

.chat-input-area textarea::placeholder {
  color: #606070;
}

.send-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
  cursor: pointer;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: opacity 0.2s;
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading-spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Scrollbar */
.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}
</style>
