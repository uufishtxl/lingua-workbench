<template>
  <div class="reader-container flex h-full overflow-hidden w-full relative">
    <!-- Sidebar / Outline Panel -->
    <aside v-show="activeLeftSidebar !== null" class="sidebar bg-slate-50 border-r border-slate-200 flex flex-col overflow-hidden w-64 flex-shrink-0 transition-all">
      
      <!-- Content: Library -->
      <div v-show="activeLeftSidebar === 'library'" class="flex-1 overflow-y-auto p-4">
        <h2 class="text-lg font-bold text-slate-800 mb-4 tracking-tight">Library</h2>
        <div v-if="articles.length === 0" class="text-sm text-slate-500 italic">
          No articles saved yet. Use the Chrome Extension to save articles.
        </div>
        <ul class="space-y-2">
          <li v-for="article in articles" :key="article.id">
            <router-link :to="{ name: 'reader', params: { id: article.id } }" 
                         class="block p-3 rounded-lg border text-sm transition-all"
                         :class="currentArticleId === article.id ? 'bg-white border-blue-500 shadow-sm' : 'border-transparent hover:bg-slate-100 text-slate-600'">
              <div class="font-semibold line-clamp-2" :class="currentArticleId === article.id ? 'text-blue-700' : 'text-slate-800'">
                {{ article.title || article.url }}
              </div>
              <div class="text-xs mt-1 opacity-70 flex justify-between">
                <span>{{ article.site_name || 'Unknown source' }}</span>
                <span v-if="article.status === 'processing'" class="text-orange-500 flex items-center gap-1">
                  <svg class="animate-spin h-3 w-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                  Processing
                </span>
              </div>
            </router-link>
          </li>
        </ul>
      </div>

      <!-- Content: Outline -->
      <div v-show="activeLeftSidebar === 'outline'" class="flex-1 overflow-y-auto p-4">
        <h2 class="text-lg font-bold text-slate-800 mb-4 tracking-tight">Outline</h2>
        <div class="relative border-l-2 border-slate-200 ml-3 space-y-6 pb-8">
            <div v-for="(item, idx) in currentArticle?.meta_context?.outline" :key="idx" 
                 class="relative pl-6 cursor-pointer group"
                 @click="scrollToParagraph(item.start_index)">
                 <div class="absolute -left-[5px] top-1.5 w-2 h-2 rounded-full transition-colors"
                      :class="activeOutlineIndex === idx ? 'bg-blue-500 scale-125' : 'bg-slate-300 group-hover:bg-blue-400'"></div>
                 <div class="text-sm font-medium transition-colors"
                      :class="activeOutlineIndex === idx ? 'text-blue-600' : 'text-slate-600 group-hover:text-blue-500'">{{ item.title }}</div>
            </div>
        </div>
      </div>
    </aside>

    <!-- Main Reading Area -->
    <main class="main-reader flex-1 flex relative min-w-0 bg-white">
      <!-- Toggle Buttons -->
      <div class="absolute left-4 top-4 z-20 flex gap-2">
        <button @click="activeLeftSidebar = activeLeftSidebar === 'library' ? null : 'library'" 
                class="p-1.5 border rounded-md shadow-sm transition-colors"
                :class="activeLeftSidebar === 'library' ? 'bg-slate-100 border-slate-300 text-slate-800' : 'bg-white border-slate-200 text-slate-500 hover:text-slate-800 hover:bg-slate-50'"
                title="Toggle Library">
           <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h7" /></svg>
        </button>

        <button v-if="currentArticle?.meta_context?.outline" 
                @click="activeLeftSidebar = activeLeftSidebar === 'outline' ? null : 'outline'" 
                class="p-1.5 border rounded-md shadow-sm transition-colors"
                :class="activeLeftSidebar === 'outline' ? 'bg-slate-100 border-slate-300 text-slate-800' : 'bg-white border-slate-200 text-slate-500 hover:text-slate-800 hover:bg-slate-50'"
                title="Toggle Outline">
           <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16" /></svg>
        </button>
      </div>

      <button v-if="currentArticle" @click="showCopilot = !showCopilot" 
              class="absolute right-4 top-4 z-20 p-1.5 bg-white border border-slate-200 rounded-md shadow-sm text-slate-500 hover:text-slate-800 hover:bg-slate-50 transition-colors"
              title="Toggle AI Copilot">
         <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>
      </button>

      <div v-if="isLoading" class="absolute inset-0 z-10 bg-white/50 backdrop-blur-sm flex items-center justify-center">
        <div class="bg-white p-6 rounded-2xl shadow-xl flex items-center gap-4">
           <svg class="animate-spin h-6 w-6 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
           <span class="text-slate-700 font-medium">Loading article context...</span>
        </div>
      </div>

      <div v-else-if="currentArticle" class="reader-content flex-1 w-full max-w-3xl mx-auto px-12 py-16 overflow-y-auto relative" @scroll="handleScroll">
        <div v-if="currentArticle.status === 'processing'" class="mb-8 p-4 bg-orange-50 text-orange-800 rounded-xl border border-orange-100 flex gap-3 text-sm">
           <span>⚡</span>
           <div>
             <strong>Global analysis in progress.</strong> 
             The LLM is silently extracting the logic skeleton (outline) and domain attributes. Advanced AI features will degrade gracefully until complete.
           </div>
        </div>
        
        <div v-if="currentArticle.status === 'translating'" class="mb-8 p-4 bg-blue-50 text-blue-800 rounded-xl border border-blue-100 flex gap-3 text-sm">
           <svg class="animate-spin h-5 w-5 text-blue-600 shrink-0 mt-0.5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
           <div>
             <strong>Translating remaining paragraphs in the background...</strong> 
             You can start reading now. The page will auto-refresh once translations are ready.
           </div>
        </div>

        <h1 class="text-4xl font-extrabold text-slate-900 mb-2 leading-tight">{{ currentArticle.title }}</h1>
        <div class="text-slate-500 text-sm mb-12 pb-6 border-b border-slate-100 flex gap-4">
          <span v-if="currentArticle.author" class="font-medium text-slate-700">{{ currentArticle.author }}</span>
          <span>{{ currentArticle.site_name }}</span>
          <a :href="currentArticle.url" target="_blank" class="text-blue-500 hover:underline">Original Source ↗</a>
        </div>

        <!-- TIPTAP BUBBLE MENU -->
        <bubble-menu v-if="editor" :editor="editor" :tippy-options="{ duration: 100, appendTo: 'parent' }">
          <div class="flex bg-slate-800 text-white rounded-lg shadow-xl overflow-hidden p-1 items-center z-50">
             <!-- Color Selector -->
             <div v-if="!activeAnnotationColor" class="flex items-center gap-1">
               <button @click="handleColorClick('yellow')" class="p-2 hover:bg-slate-700 rounded transition-colors group relative" title="Jargon (Domain specific term)">
                 <div class="w-4 h-4 rounded-full bg-yellow-400"></div>
               </button>
               <button @click="handleColorClick('blue')" class="p-2 hover:bg-slate-700 rounded transition-colors group relative" title="Usage (Advanced phrasing)">
                 <div class="w-4 h-4 rounded-full bg-blue-400"></div>
               </button>
               <button @click="handleColorClick('pink')" class="p-2 hover:bg-slate-700 rounded transition-colors group relative" title="Thought (Socratic dialogue)">
                 <div class="w-4 h-4 rounded-full bg-pink-400"></div>
               </button>
               <div class="w-px h-6 bg-slate-600 mx-1"></div>
               <button @click="askCopilotAboutSelection()" class="p-2 hover:bg-slate-700 rounded transition-colors flex items-center justify-center text-lg w-8 h-8 filter grayscale hover:grayscale-0 hover:scale-110" title="Edit text with Copilot (Reader Edit)">
                 ✨
               </button>
             </div>
             
             <!-- Note Input form -->
             <div v-else class="flex items-center gap-2 px-2 py-1">
                 <div class="w-3 h-3 rounded-full flex-shrink-0" :class="{
                     'bg-yellow-400': activeAnnotationColor === 'yellow',
                     'bg-green-400': activeAnnotationColor === 'blue',
                     'bg-pink-400': activeAnnotationColor === 'pink'
                 }"></div>
                 <input v-model="userNoteText" 
                        ref="noteInputRef"
                        @keydown.ctrl.enter="submitAnnotation"
                        @keydown.meta.enter="submitAnnotation"
                        @keydown.esc="cancelNoteInput"
                        type="text" 
                        placeholder="Add a thought... (Ctrl+Enter to ask AI)" 
                        class="bg-transparent border-none text-white placeholder-slate-400 text-sm focus:outline-none focus:ring-0 w-64" />
             </div>
          </div>
        </bubble-menu>

        <!-- TIPTAP EDITOR -->
        <editor-content :editor="editor" class="prose prose-lg prose-slate max-w-none focus:outline-none pb-32" @mousemove="handleMouseMove" @mouseleave="hoveredAnno = null" @click="handleEditorClick" />
        
        <!-- Hover Tooltip -->
        <div v-show="hoveredAnno" ref="tooltipRef" class="fixed z-50 pointer-events-none bg-white border border-slate-200 shadow-xl rounded-xl p-4 text-sm w-80 transform -translate-x-1/2 -translate-y-[calc(100%+10px)]" :style="{ left: tooltipPos.x + 'px', top: tooltipPos.y + 'px' }">
            <div class="font-bold mb-2 text-xs uppercase tracking-wider flex justify-between items-center" :class="{
                'text-yellow-600': hoveredAnno?.annotation_type === 'yellow',
                'text-green-600': hoveredAnno?.annotation_type === 'blue',
                'text-pink-600': hoveredAnno?.annotation_type === 'pink',
            }">
               <span>{{ hoveredAnno?.annotation_type === 'yellow' ? 'Jargon' : (hoveredAnno?.annotation_type === 'blue' ? 'Usage' : 'Thought') }}</span>
            </div>
            <div v-if="hoveredAnno?.user_note" class="mb-2 pb-2 border-b border-slate-100 text-slate-600 italic">
               "{{ hoveredAnno.user_note }}"
            </div>
            <div v-if="hoveredAnno?.ai_response" v-html="hoveredAnno.ai_response.content" class="text-slate-800 prose-sm prose-p:my-1"></div>
            <div v-else class="text-slate-400 flex items-center gap-2">
                <svg class="animate-spin h-3 w-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                Processing AI Insights...
            </div>
        </div>
      </div>
      
      <div v-else class="flex-1 flex flex-col items-center justify-center text-slate-400">
         <div class="text-6xl mb-4">📖</div>
         <p>Select an article to start reading</p>
      </div>

      <!-- Right Panel: AI Copilot -->
      <aside v-if="currentArticle" v-show="showCopilot" class="copilot-panel w-96 border-l border-slate-200 bg-white flex flex-col flex-shrink-0 transition-all">
        <div class="p-4 border-b border-slate-100 bg-slate-50 font-semibold text-slate-700 flex justify-between items-center">
           <span>AI Copilot</span>
           <span class="text-xs font-normal text-slate-500 bg-slate-200 px-2 py-0.5 rounded-full" v-if="currentArticle.meta_context?.domain">
             {{ currentArticle.meta_context.domain }}
           </span>
        </div>
        
        <div class="flex-1 p-6 overflow-y-auto space-y-6">
          <!-- Article Summary & Outline (from global AI analysis) -->
          <div v-if="currentArticle.meta_context?.summary" class="mb-6 p-4 bg-slate-50 rounded-xl border border-slate-100">
            <h3 class="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2 flex justify-between">
                <span>Quick Summary</span>
                <span class="text-[10px] bg-slate-200 text-slate-500 px-1.5 py-0.5 rounded">{{ currentArticle.meta_context.difficulty || 'Analysis' }}</span>
            </h3>
            <p class="text-sm text-slate-600 mb-4 leading-relaxed">{{ currentArticle.meta_context.summary }}</p>
            

          </div>

          <div v-if="annotations.length === 0" class="text-center text-slate-400 text-sm italic mt-10">
             Highlight text, pick a color, and hit Ctrl+Enter to consult the AI Copilot.
          </div>
          
          <!-- Render Annotations / AI Chats -->
          <div v-for="anno in annotations" :key="anno.id" class="border rounded-xl shadow-sm overflow-hidden"
               :class="{
                   'border-yellow-200': anno.annotation_type === 'yellow',
                   'border-green-200': anno.annotation_type === 'blue',
                   'border-pink-200': anno.annotation_type === 'pink'
               }">
              <div class="px-4 py-2 text-sm font-medium border-b"
                   :class="{
                       'bg-yellow-50 text-yellow-800 border-yellow-200': anno.annotation_type === 'yellow',
                       'bg-green-50 text-green-800 border-green-200': anno.annotation_type === 'blue',
                       'bg-pink-50 text-pink-800 border-pink-200': anno.annotation_type === 'pink'
                   }">
                <span class="opacity-70 text-xs uppercase mr-2" v-if="anno.annotation_type==='yellow'">Jargon</span>
                <span class="opacity-70 text-xs uppercase mr-2" v-if="anno.annotation_type==='blue'">Usage</span>
                <span class="opacity-70 text-xs uppercase mr-2" v-if="anno.annotation_type==='pink'">Thought</span>
                "{{ anno.selected_text }}"
              </div>
              
              <div v-if="anno.user_note" class="p-4 bg-white text-slate-700 text-sm border-b border-slate-100">
                 🗣️ <strong>You:</strong> {{ anno.user_note }}
              </div>
              
              <div class="p-4 bg-slate-50 text-sm">
                 <div v-if="anno.ai_response" class="text-slate-800">
                     🤖 <span v-html="anno.ai_response.content"></span>
                 </div>
                 <div v-else class="text-slate-400 flex items-center gap-2">
                     <svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                     Thinking...
                 </div>
              </div>
          </div>
        </div>
      </aside>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { readerApi, type Article, type ArticleDetail, type Annotation } from '@/api/readerApi'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import { BubbleMenu } from '@tiptap/vue-3/menus'
import StarterKit from '@tiptap/starter-kit'
import Highlight from '@tiptap/extension-highlight'
import Paragraph from '@tiptap/extension-paragraph'
import { useChatStore } from '@/stores/chatStore'

const route = useRoute()
const router = useRouter()
const chatStore = useChatStore()

const activeLeftSidebar = ref<'library' | 'outline' | null>('library')
const activeOutlineIndex = ref(0)
const showCopilot = ref(true)

function scrollToParagraph(pid: number) {
    if (!pid) return
    const el = document.querySelector(`[data-pid="${pid}"]`)
    if (el) {
        el.scrollIntoView({ behavior: 'auto', block: 'center' })
    }
}

function handleScroll(e: Event) {
    if (activeLeftSidebar.value !== 'outline' || !currentArticle.value?.meta_context?.outline) return;

    const outline = currentArticle.value.meta_context.outline;
    let currentIdx = -1;

    for (let i = 0; i < outline.length; i++) {
        const item = outline[i];
        const el = document.querySelector(`[data-pid="${item.start_index}"]`) as HTMLElement;
        if (el) {
            const rect = el.getBoundingClientRect();
            // Assuming Top Navbar/Container offsets. 300px from the absolute top of viewport
            // seems like a good visual transition point for when a paragraph "takes over".
            if (rect.top <= 250) {
                currentIdx = i;
            } else {
                break;
            }
        }
    }

    if (currentIdx === -1 && outline.length > 0) {
        currentIdx = 0; // default to first outline item
    }

    if (activeOutlineIndex.value !== currentIdx) {
        activeOutlineIndex.value = currentIdx;
    }
}

const articles = ref<Article[]>([])
const currentArticleId = ref<number | null>(null)
const currentArticle = ref<ArticleDetail | null>(null)
const annotations = ref<Annotation[]>([])
const isLoading = ref(false)

// Bubble menu state
const activeAnnotationColor = ref<'yellow' | 'blue' | 'pink' | null>(null)
const userNoteText = ref('')
const noteInputRef = ref<HTMLInputElement | null>(null)

// Tooltip state
const hoveredAnno = ref<Annotation | null>(null)
const tooltipPos = ref({ x: 0, y: 0 })

// Map colors to highlight hex
const colorMap = {
    yellow: '#fef08a', // yellow-200
    blue: '#bbf7d0',   // green-200 used for 'blue' type to avoid clashing with browser selection text
    pink: '#fbcfe8'    // pink-200
}

const CustomParagraph = Paragraph.extend({
  addAttributes() {
    return {
      pid: {
        default: null,
        parseHTML: element => element.getAttribute('data-pid'),
        renderHTML: attributes => {
          if (!attributes.pid) return {}
          return { 'data-pid': attributes.pid }
        },
      },
    }
  },
})

const CustomHighlight = Highlight.extend({
  addAttributes() {
    return {
      ...this.parent?.(),
      annoId: {
        default: null,
        parseHTML: element => element.getAttribute('data-anno-id'),
        renderHTML: attributes => {
          if (!attributes.annoId) return {}
          return { 'data-anno-id': attributes.annoId, class: 'cursor-pointer hover:brightness-95 transition-all outline outline-2 outline-transparent hover:outline-blue-400 rounded px-0.5' }
        },
      },
    }
  },
})

// Init Tiptap Editor
const editor = useEditor({
  extensions: [
    StarterKit.configure({
        paragraph: false
    }),
    CustomParagraph,
    CustomHighlight.configure({
      multicolor: true,
    }),
  ],
  content: '',
  editable: true, 
})

onMounted(async () => {
  await fetchArticles()
  if (route.params.id) {
     loadArticle(Number(route.params.id))
  }
})

onBeforeUnmount(() => {
  editor.value?.destroy()
  clearPolling()
})

watch(() => route.params.id, (newId) => {
  if (newId) {
    loadArticle(Number(newId))
  } else {
    currentArticleId.value = null
    currentArticle.value = null
    annotations.value = []
    editor.value?.commands.setContent('')
    clearPolling()
  }
})

watch(() => chatStore.refreshReaderTrigger, () => {
    if (currentArticleId.value) {
        loadArticle(currentArticleId.value, true)
    }
})

async function fetchArticles() {
  try {
    const data: any = await readerApi.getArticles()
    // Handle Django REST framework pagination fallback
    articles.value = Array.isArray(data) ? data : (data.results || [])
  } catch (err) {
    console.error("Failed to load articles", err)
  }
}

function processExistingAnnotations(articleData: ArticleDetail) {
    // Extract annotations from all paragraphs
    let allAnnos: Annotation[] = []
    articleData.paragraphs.forEach(p => {
        if (p.annotations && p.annotations.length > 0) {
            allAnnos = [...allAnnos, ...p.annotations]
        }
    })
    
    // Sort by newest first
    annotations.value = allAnnos.sort((a,b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
}

function handleMouseMove(e: MouseEvent) {
    const target = e.target as HTMLElement
    if (target && target.tagName === 'MARK' && target.hasAttribute('data-anno-id')) {
        const annoId = Number(target.getAttribute('data-anno-id'))
        const anno = annotations.value.find(a => a.id === annoId)
        if (anno) {
            hoveredAnno.value = anno
            tooltipPos.value = { x: e.clientX, y: e.clientY }
            return
        }
    }
    hoveredAnno.value = null
}

function handleEditorClick(e: MouseEvent) {
    const target = e.target as HTMLElement
    // Because Tiptap wraps marks around text nodes, we need to check if we clicked a mark or its closest parent
    const mark = target.closest('mark[data-anno-id]')
    if (mark) {
        const annoId = Number(mark.getAttribute('data-anno-id'))
        askCopilotAboutAnnotation(annoId)
    }
}

function askCopilotAboutSelection() {
    if (!editor.value) return
    const { from, to } = editor.value.state.selection
    const text = editor.value.state.doc.textBetween(from, to)
    
    // Find the closest paragraph ID from selection
    const $from = editor.value.state.selection.$from
    let pid = null
    for (let d = $from.depth; d > 0; d--) {
        const node = $from.node(d)
        if (node && node.attrs && node.attrs.pid) {
            pid = node.attrs.pid
            break
        }
    }
    const pidInfo = pid ? `[PID:${pid}] ` : ''
    
    const prompt = `[READER_EDIT]\nHi, please help me edit ${pidInfo}text: "${text}".\nMy instructions: `
    chatStore.setInput(prompt)
    chatStore.open()
}

function askCopilotAboutAnnotation(annoId: number) {
    const prompt = `[READER_EDIT]\nHi, please help me edit annotation [AnnoID:${annoId}].\nMy instructions: `
    chatStore.setInput(prompt)
    chatStore.open()
}

let pollingInterval: any = null

function clearPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval)
        pollingInterval = null
    }
}

function startPolling(id: number) {
    clearPolling()
    pollingInterval = setInterval(async () => {
        try {
            const data = await readerApi.getArticle(id)
            if (currentArticle.value && data.status !== currentArticle.value.status) {
                if (data.status === 'ready') {
                    clearPolling()
                    // fully reload UI to get translations
                    loadArticle(id)
                } else if (data.status === 'translating') {
                    // Update meta context directly to show Outline while translating
                    currentArticle.value.meta_context = data.meta_context
                    currentArticle.value.status = data.status
                } else {
                    currentArticle.value.status = data.status
                }
            }
        } catch(e) {}
    }, 5000)
}

async function loadArticle(id: number, preserveState: boolean = false) {
  const prevScrollY = window.scrollY
  if (!preserveState) {
      isLoading.value = true
      activeAnnotationColor.value = null
      editor.value?.commands.setContent('')
  }
  currentArticleId.value = id
  try {
    const data = await readerApi.getArticle(id)
    currentArticle.value = data
    
    // Inject paragraphs as HTML into TipTap
    const contentHtml = data.paragraphs.map(p => {
       let pContent = p.content
       if (p.annotations && p.annotations.length > 0) {
           p.annotations.forEach(anno => {
               const bg = colorMap[anno.annotation_type as keyof typeof colorMap]
               pContent = pContent.replace(anno.selected_text, `<mark style="background-color: ${bg};" data-anno-id="${anno.id}">${anno.selected_text}</mark>`)
           })
       }
       let html = `<p data-pid="${p.id}">${pContent}</p>`
       if (p.translation) {
           html += `<p class="text-[0.9em] text-slate-500 mt-1 mb-6 border-l-2 border-slate-200 pl-3">${p.translation}</p>`
       }
       return html
    }).join('')
    
    editor.value?.commands.setContent(contentHtml)

    processExistingAnnotations(data)

    if (data.status !== 'ready' && data.status !== 'failed') {
       startPolling(id)
    }

    if (preserveState) {
        nextTick(() => {
            window.scrollTo(0, prevScrollY)
        })
    }

  } catch (err) {
    console.error("Failed to load article details", err)
  } finally {
    if (!preserveState) {
        isLoading.value = false
    }
  }
}

// Bubble Menu Logic
async function handleColorClick(color: 'yellow' | 'blue' | 'pink') {
    activeAnnotationColor.value = color
    userNoteText.value = ''
    
    // For yellow and blue, auto-submit right away to save time
    if (color === 'yellow' || color === 'blue') {
        await submitAnnotation()
    } else {
        nextTick(() => {
            noteInputRef.value?.focus()
        })
    }
}

function cancelNoteInput() {
    activeAnnotationColor.value = null
    userNoteText.value = ''
}

async function submitAnnotation() {
    if (!activeAnnotationColor.value || !editor.value) return;

    const { state } = editor.value
    const { from, to } = state.selection
    
    const selectedText = state.doc.textBetween(from, to, ' ')
    if (!selectedText.trim()) return;

    // Find the original paragraph that contains this text
    let paragraphId = null
    for (const p of currentArticle.value?.paragraphs || []) {
        if (p.content.includes(selectedText)) {
            paragraphId = p.id
            break
        }
    }

    if (!paragraphId) paragraphId = currentArticle.value?.paragraphs[0]?.id
    if (!paragraphId) return;

    const newAnnoData = {
        paragraph: paragraphId,
        selected_text: selectedText,
        annotation_type: activeAnnotationColor.value,
        user_note: userNoteText.value
    }

    // Reset UI state first so the popup vanishes
    const colorUsed = activeAnnotationColor.value
    cancelNoteInput()

    try {
        // 1. Create Annotation in DB
        const createdAnno = await readerApi.createAnnotation(newAnnoData)
        annotations.value.unshift(createdAnno) // Add to top of list

        // Apply Highlight locally with annoId attached FIRST, before un-selecting text.
        editor.value.commands.setHighlight({ color: colorMap[colorUsed], annoId: createdAnno.id } as any)
        
        // 🌟 Now safely un-select the text so the browser native outline is removed
        editor.value.commands.setTextSelection(to)

        // 2. Trigger AI Assist
        const aiResult = await readerApi.triggerAiAssist(createdAnno.id, createdAnno.user_note)
        
        // 3. Update the annotation with AI response
        const idx = annotations.value.findIndex(a => a.id === createdAnno.id)
        if (idx !== -1) {
            annotations.value[idx] = aiResult
        }

    } catch (err) {
        console.error("Failed to process annotation", err)
    }
}
</script>

<style scoped>
.reader-container {
  display: flex;
  height: 100vh;
  width: 100%;
  background-color: white;
}
.sidebar {
  width: 320px;
  flex-shrink: 0;
}
.main-reader {
  flex-grow: 1;
  display: flex;
  min-width: 0;
}
.reader-content {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.reader-content::-webkit-scrollbar {
  display: none;
}
.copilot-panel {
  flex-shrink: 0;
}

:deep(.ProseMirror) {
  outline: none !important;
  caret-color: transparent; 
}
:deep(.ProseMirror p) {
  margin-bottom: 1.5em;
  line-height: 1.8;
  color: #334155;
  font-size: 1.125rem;
}
:deep(.ProseMirror p::selection) {
  background-color: rgba(59, 130, 246, 0.2);
}

/* Make Highlights pop */
:deep(mark) {
  border-radius: 4px;
  padding: 2px 0;
}
</style>
