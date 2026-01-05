<template>
  <div class="dev-container">
    <h1 class="dev-title">🔧 SliceCard 组件开发预览</h1>
    
    <div class="preview-sections">
      <!-- Section 1: Text Display + HighlightEditor -->
      <div class="section-card">
        <h2>📝 文本显示 + HighlightEditor</h2>
        <div class="slice-preview">
          <!-- 模拟 SliceCard 的文本显示区 -->
          <div class="text-display-area" @click="activeHighlight = mockHighlight">
            <InteractiveTextWithHilis 
              :text="mockText" 
              :highlights="mockHighlights"
              :current-active-id="activeHighlight?.id ?? null"
              @click-highlight="onHighlightClick"
            />
          </div>
          
          <!-- HighlightEditor -->
          <div v-if="activeHighlight" class="editor-area">
            <HighlightEditor 
              :highlight="activeHighlight" 
              :full-context="mockText"
              @update:highlight="onUpdate"
              @delete-highlight="onDelete"
              @cancel="onCancel"
            />
          </div>
          <div v-else class="placeholder-area">
            <span>👆 点击上方高亮文本打开编辑器</span>
          </div>
        </div>
      </div>

      <!-- Section 2: Ruby Text 演示 -->
      <div class="section-card">
        <h2>🎵 Ruby Text 听觉图谱</h2>
        <div class="ruby-demo">
          <div class="ruby-display">
            <ruby v-for="seg in rubySegments" :key="seg.original" :class="['ruby-word', seg.type]">
              {{ seg.original }}
              <rt>{{ seg.sound_display }}</rt>
            </ruby>
          </div>
          
          <div class="ruby-legend">
            <span class="legend-item"><span class="dot normal"></span> 正常</span>
            <span class="legend-item"><span class="dot reduction"></span> 弱读</span>
            <span class="legend-item"><span class="dot linking"></span> 连读</span>
            <span class="legend-item"><span class="dot flap_t"></span> Flap T</span>
          </div>

          <h3>编辑 Ruby 数据</h3>
          <div class="ruby-editor">
            <div v-for="(seg, i) in rubySegments" :key="i" class="ruby-row">
              <input v-model="seg.original" placeholder="原文" />
              <input v-model="seg.sound_display" placeholder="发音" />
              <select v-model="seg.type">
                <option value="normal">normal</option>
                <option value="reduction">弱读</option>
                <option value="linking">连读</option>
                <option value="flap_t">Flap T</option>
              </select>
              <button @click="rubySegments.splice(i, 1)">✕</button>
            </div>
            <button class="add-btn" @click="addRubySegment">+ 添加音节</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Debug Panel -->
    <div class="debug-panel">
      <h3>📤 状态</h3>
      <pre>activeHighlight: {{ activeHighlight?.id ?? 'null' }}</pre>
      
      <h3>📝 事件日志</h3>
      <div class="event-log">
        <div v-for="(log, i) in eventLogs" :key="i" class="log-item">{{ log }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import HighlightEditor from '@/components/HighlightEditor.vue'
import InteractiveTextWithHilis from '@/components/InteractiveTextWithHilis.vue'

// Types
type AbbreviatedTag = 'FT' | 'RED' | 'LINK' | 'RESYL' | 'FT_HYPHEN'

interface Hili {
  id: string
  start: number
  end: number
  content: string
  tags: AbbreviatedTag[]
  note: string
}

interface RubySegment {
  original: string
  sound_display: string
  type: 'normal' | 'reduction' | 'linking' | 'flap_t'
}

// === Mock Data ===
const mockText = ref("You've got to live with it.")

const mockHighlights = ref<Hili[]>([
  {
    id: 'h1',
    start: 0,
    end: 6,
    content: "You've",
    tags: ['RED'],
    note: '/jəv/'
  },
  {
    id: 'h2',
    start: 7,
    end: 13,
    content: 'got to',
    tags: ['LINK', 'FT'],
    note: '/ˈɡɑːtə/ - gotta'
  }
])

const mockHighlight = ref<Hili>({
  id: 'dev-123',
  start: 0,
  end: 13,
  content: "You've got to",
  tags: ['RED', 'LINK'],
  note: '/jəv ˈɡɑːtə/'
})

const activeHighlight = ref<Hili | null>(null)

// Ruby Text Data
const rubySegments = ref<RubySegment[]>([
  { original: "You've", sound_display: 'Yuh', type: 'reduction' },
  { original: 'got to', sound_display: 'GAH-duh', type: 'flap_t' },
  { original: 'live', sound_display: 'liv', type: 'normal' },
  { original: 'with it', sound_display: 'wi-thit', type: 'linking' }
])

const addRubySegment = () => {
  rubySegments.value.push({ original: '', sound_display: '', type: 'normal' })
}

// Event Logging
const eventLogs = ref<string[]>([])

const log = (msg: string) => {
  eventLogs.value.unshift(`[${new Date().toLocaleTimeString()}] ${msg}`)
  if (eventLogs.value.length > 10) eventLogs.value.pop()
}

// Handlers
const onHighlightClick = (h: Hili) => {
  log(`click-highlight → "${h.content}"`)
  activeHighlight.value = h
}

const onUpdate = (h: Hili) => {
  log(`update → note: "${h.note}"`)
  // Update in mockHighlights
  const idx = mockHighlights.value.findIndex(x => x.id === h.id)
  if (idx !== -1) mockHighlights.value[idx] = h
  activeHighlight.value = null
}

const onDelete = (id: string) => {
  log(`delete → id: ${id}`)
  mockHighlights.value = mockHighlights.value.filter(h => h.id !== id)
  activeHighlight.value = null
}

const onCancel = () => {
  log('cancel')
  activeHighlight.value = null
}
</script>

<style scoped>
.dev-container {
  min-height: 100vh;
  background: #0f0a1e;
  padding: 24px;
  color: white;
}

.dev-title {
  font-size: 20px;
  margin-bottom: 20px;
  color: #a78bfa;
}

.preview-sections {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
  margin-bottom: 24px;
}

.section-card {
  background: #1a1429;
  border-radius: 12px;
  padding: 16px;
  min-width: 380px;
  flex: 1;
}

.section-card h2 {
  font-size: 14px;
  color: #818cf8;
  margin-bottom: 12px;
}

.section-card h3 {
  font-size: 12px;
  color: #6b7280;
  margin: 16px 0 8px;
}

/* Text Display Area */
.slice-preview {
  border: 1px dashed #4E466E;
  border-radius: 8px;
  overflow: hidden;
}

.text-display-area {
  background: #fff;
  padding: 16px;
  font-size: 18px;
  min-height: 60px;
  cursor: pointer;
  color: #1a1a1a;
}

.editor-area {
  border-top: 1px solid #4E466E;
}

.placeholder-area {
  background: #1C1338;
  padding: 24px;
  text-align: center;
  color: #6b7280;
  font-size: 12px;
}

/* Ruby Text Styles */
.ruby-demo {
  background: #0d0817;
  padding: 16px;
  border-radius: 8px;
}

.ruby-display {
  font-size: 24px;
  line-height: 2.5;
  padding: 16px;
  background: white;
  border-radius: 8px;
  color: #1a1a1a;
}

.ruby-word {
  margin: 0 4px;
  padding: 2px 6px;
  border-radius: 4px;
}

.ruby-word rt {
  font-size: 0.5em;
  font-weight: 500;
}

/* Ruby type colors */
.ruby-word.normal { background: transparent; }
.ruby-word.normal rt { color: #6b7280; }

.ruby-word.reduction { background: #fef3c7; }
.ruby-word.reduction rt { color: #d97706; }

.ruby-word.linking { background: #dbeafe; }
.ruby-word.linking rt { color: #2563eb; }

.ruby-word.flap_t { background: #fce7f3; }
.ruby-word.flap_t rt { color: #db2777; }

.ruby-legend {
  display: flex;
  gap: 16px;
  margin-top: 12px;
  font-size: 11px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #9ca3af;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.dot.normal { background: #6b7280; }
.dot.reduction { background: #d97706; }
.dot.linking { background: #2563eb; }
.dot.flap_t { background: #db2777; }

/* Ruby Editor */
.ruby-editor {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ruby-row {
  display: flex;
  gap: 8px;
}

.ruby-row input, .ruby-row select {
  flex: 1;
  background: #302849;
  border: 1px solid #4E466E;
  border-radius: 4px;
  padding: 6px 8px;
  color: white;
  font-size: 12px;
}

.ruby-row button {
  background: #7f1d1d;
  border: none;
  border-radius: 4px;
  color: white;
  padding: 0 10px;
  cursor: pointer;
}

.add-btn {
  background: #1e3a5f;
  border: 1px dashed #3b82f6;
  border-radius: 4px;
  color: #60a5fa;
  padding: 8px;
  cursor: pointer;
  font-size: 12px;
}

/* Debug Panel */
.debug-panel {
  background: #1a1429;
  padding: 16px;
  border-radius: 8px;
  max-width: 600px;
}

.debug-panel h3 {
  color: #818cf8;
  font-size: 12px;
  margin: 12px 0 8px;
}

.debug-panel h3:first-child { margin-top: 0; }

.debug-panel pre {
  background: #0d0817;
  padding: 8px;
  border-radius: 4px;
  font-size: 11px;
  color: #4ade80;
}

.event-log {
  background: #0d0817;
  padding: 8px;
  border-radius: 4px;
  max-height: 120px;
  overflow-y: auto;
}

.log-item {
  font-family: monospace;
  font-size: 11px;
  color: #fbbf24;
  padding: 2px 0;
  border-bottom: 1px solid #1f1830;
}
</style>
