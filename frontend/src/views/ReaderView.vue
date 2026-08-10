<template>
  <div class="reader-container flex h-full overflow-hidden w-full relative">
    <!-- Sidebar / Outline Panel -->
    <aside v-show="activeLeftSidebar !== null" class="sidebar bg-slate-50 border-r border-slate-200 flex flex-col overflow-hidden w-64 flex-shrink-0 transition-all">
      
      <!-- Content: Library -->
      <div v-show="activeLeftSidebar === 'library'" class="flex-1 overflow-y-auto p-4">
        <h2 class="text-lg font-bold text-slate-800 mb-3 tracking-tight">Library</h2>
        
        <!-- Filter Toggle -->
        <div class="flex bg-slate-100 rounded-lg p-1 mb-4">
          <button @click="setFilter('all')" 
                  class="flex-1 px-3 py-1.5 text-xs font-medium rounded-md transition-colors"
                  :class="contentFilter === 'all' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-700'">
            所有
          </button>
          <button @click="setFilter('article')" 
                  class="flex-1 px-3 py-1.5 text-xs font-medium rounded-md transition-colors"
                  :class="contentFilter === 'article' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-700'">
            📄 网页
          </button>
          <button @click="setFilter('book')" 
                  class="flex-1 px-3 py-1.5 text-xs font-medium rounded-md transition-colors"
                  :class="contentFilter === 'book' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-700'">
            📚 书籍
          </button>
        </div>

        <!-- Upload Button (only for books) -->
        <BookUpload v-if="contentFilter === 'book' || contentFilter === 'all'" @uploaded="handleBookUploaded" />

        <!-- Articles List -->
        <div v-if="contentFilter !== 'book'">
          <div v-if="filteredArticles.length === 0 && contentFilter === 'article'" class="text-sm text-slate-500 italic mb-4">
            No articles saved yet. Use the Chrome Extension to save articles.
          </div>
          <ul class="space-y-2 mt-3">
            <li v-for="article in filteredArticles" :key="'article-' + article.id">
              <router-link :to="{ name: 'reader', params: { id: 'article-' + article.id } }" 
                           class="block p-3 rounded-lg border text-sm transition-all"
                           :class="currentItemId === 'article-' + article.id ? 'bg-white border-blue-500 shadow-sm' : 'border-transparent hover:bg-slate-100 text-slate-600'">
                <div class="flex items-start gap-2">
                  <span class="text-base mt-0.5">📄</span>
                  <div class="flex-1 min-w-0">
                    <div class="font-semibold line-clamp-2" :class="currentItemId === 'article-' + article.id ? 'text-blue-700' : 'text-slate-800'">
                      {{ article.title || article.url }}
                    </div>
                    <div class="text-xs mt-1 opacity-70 flex justify-between">
                      <span>{{ article.site_name || 'Unknown source' }}</span>
                      <span v-if="article.status === 'processing'" class="text-orange-500 flex items-center gap-1">
                        <svg class="animate-spin h-3 w-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                        Processing
                      </span>
                    </div>
                  </div>
                </div>
              </router-link>
            </li>
          </ul>
        </div>

        <!-- Books List -->
        <div v-if="contentFilter !== 'article'">
          <div v-if="filteredBooks.length === 0 && contentFilter === 'book'" class="text-sm text-slate-500 italic mt-2">
            No books uploaded yet. Click the button above to upload a PDF.
          </div>
          <ul class="space-y-2 mt-3">
            <li v-for="book in filteredBooks" :key="'book-' + book.id">
              <div @click="selectBook(book.id)" 
                   class="block p-3 rounded-lg border text-sm transition-all cursor-pointer"
                   :class="currentItemId === 'book-' + book.id ? 'bg-white border-blue-500 shadow-sm' : 'border-transparent hover:bg-slate-100 text-slate-600'">
                <div class="flex items-start gap-2">
                  <span class="text-base mt-0.5">📚</span>
                  <div class="flex-1 min-w-0">
                    <div class="font-semibold line-clamp-2" :class="currentItemId === 'book-' + book.id ? 'text-blue-700' : 'text-slate-800'">
                      {{ book.title || book.original_filename }}
                    </div>
                    <div class="text-xs mt-1 opacity-70 flex justify-between">
                      <span>{{ book.author || 'Unknown author' }}</span>
                      <span v-if="book.status === 'processing'" class="text-orange-500 flex items-center gap-1">
                        <svg class="animate-spin h-3 w-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                        Processing
                      </span>
                      <span v-else-if="book.status === 'ready'" class="text-green-500">✓ Ready</span>
                      <span v-else-if="book.status === 'failed'" class="text-red-500">✗ Failed</span>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- Chapter List (shown when book is selected) -->
              <div v-if="currentItemId === 'book-' + book.id && currentBook?.chapters" class="ml-6 mt-2">
                <div class="flex items-center justify-between mb-2">
                  <span class="text-xs font-medium text-slate-500">Chapters</span>
                  <button v-if="currentBook.last_read_chapter" 
                          @click.stop="scrollToLastReadPosition" 
                          class="p-1 text-blue-500 hover:text-blue-700 hover:bg-blue-50 rounded transition-colors"
                          title="Jump to last read position">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 11l7-7 7 7M5 19l7-7 7 7" />
                    </svg>
                  </button>
                </div>
                <div class="space-y-1">
                  <div v-for="chapter in currentBook.chapters" :key="chapter.id"
                       @click="selectChapter(chapter.id)"
                       class="p-2 rounded text-xs cursor-pointer transition-colors flex items-center gap-2"
                       :class="currentChapterId === chapter.id ? 'bg-blue-50 text-blue-700' : 'hover:bg-slate-100 text-slate-600'">
                    <span class="w-5 h-5 flex items-center justify-center bg-slate-200 rounded-full text-[10px] font-bold">
                      {{ chapter.chapter_index + 1 }}
                    </span>
                    <span class="line-clamp-1">{{ chapter.title }}</span>
                  </div>
                </div>
              </div>
            </li>
          </ul>
        </div>
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
           <span class="text-slate-700 font-medium">Loading content...</span>
        </div>
      </div>

      <div v-if="currentArticle" class="flex-1 w-full px-10 mx-auto relative">
        <div class="reader-content w-full px-12 py-16 overflow-y-auto relative" @scroll="handleScroll">
        <!-- Reading Progress Bar -->
        <div v-if="currentArticle" style="position: sticky; top: 50%; transform: translateY(-50%); float: right; margin-right: -40px; z-index: 9999;">
          <div style="background: white; padding: 10px; border-radius: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.2); border: 1px solid #e2e8f0;">
            <div style="width: 12px; height: 200px; background: #e2e8f0; border-radius: 6px; overflow: hidden; position: relative;">
              <div :style="{ position: 'absolute', top: 0, left: 0, width: '100%', background: 'linear-gradient(to bottom, #3b82f6, #60a5fa)', borderRadius: '6px', transition: 'height 0.15s', height: readingProgress + '%' }"></div>
            </div>
            <!-- <div style="text-align: center; margin-top: 8px; font-size: 12px; font-weight: bold; color: #475569;">{{ Math.round(readingProgress) }}%</div> -->
          </div>
        </div>
        
        <div v-if="currentArticle.status === 'processing'" class="mb-8 p-4 bg-orange-50 text-orange-800 rounded-xl border border-orange-100 flex gap-3 text-sm">
           <span>⚡</span>
           <div>
             <strong>Processing in progress.</strong> 
             Content is being analyzed. Features will be available once processing is complete.
           </div>
        </div>
        
        <div v-if="currentArticle.status === 'translating'" class="mb-8 p-4 bg-blue-50 text-blue-800 rounded-xl border border-blue-100 flex gap-3 text-sm">
           <svg class="animate-spin h-5 w-5 text-blue-600 shrink-0 mt-0.5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
           <div>
             <strong>Translating remaining paragraphs in the background...</strong> 
             You can start reading now.
           </div>
        </div>

        <h1 class="text-4xl font-extrabold text-slate-900 mb-2 leading-tight">{{ currentArticle.title }}</h1>
        <div class="text-slate-500 text-sm mb-12 pb-6 border-b border-slate-100 flex gap-4">
          <span v-if="currentArticle.author" class="font-medium text-slate-700">{{ currentArticle.author }}</span>
          <span v-if="currentArticle.site_name">{{ currentArticle.site_name }}</span>
          <a v-if="currentArticle.url" :href="currentArticle.url" target="_blank" class="text-blue-500 hover:underline">Original Source ↗</a>
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
               <button v-if="currentBook" @click="saveBookmarkAtSelection()" class="p-2 hover:bg-slate-700 rounded transition-colors flex items-center justify-center text-lg w-8 h-8" title="Save reading position here">
                 📖
               </button>
               <div class="w-px h-6 bg-slate-600 mx-1"></div>
               <button @click="generateTtsForSelection()" 
                       class="p-2 hover:bg-slate-700 rounded transition-colors flex items-center justify-center text-lg w-8 h-8"
                       :class="{ 'animate-pulse': isGeneratingTts }"
                       :disabled="isGeneratingTts"
                       title="Generate audio for selected text">
                 {{ isGeneratingTts ? '⏳' : '🔊' }}
               </button>
             </div>
             
             <!-- Note Input form -->
             <div v-else class="flex items-center gap-2 px-2 py-1">
                 <div class="w-3 h-3 rounded-full flex-shrink-0" :class="{
                     'bg-yellow-400': activeAnnotationColor === 'yellow',
                     'bg-blue-400': activeAnnotationColor === 'blue',
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
            <div v-if="hoveredAnno?.ai_response && !hoveredAnno.ai_response.error" v-html="hoveredAnno.ai_response.content" class="text-slate-800 prose-sm prose-p:my-1"></div>
            <div v-else-if="hoveredAnno?.ai_response?.error" class="text-red-500 text-xs">❌ {{ hoveredAnno.ai_response.message }}</div>
            <div v-else class="text-slate-400 flex items-center gap-2">
                <svg class="animate-spin h-3 w-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                Processing AI Insights...
            </div>
        </div>

        <!-- Audio play buttons (absolute positioned inside scroll container) -->
         <!-- bg-blue-500 hover:bg-blue-600 shadow-lg -->
        <div v-for="btn in audioButtonPositions" :key="btn.pid"
             class="absolute z-50 w-7 h-7 rounded-full text-blue-500 flex items-center justify-center cursor-pointer transition-transform hover:scale-200"
             :style="{ left: btn.x + 'px', top: btn.y + 'px' }"
             @click="playParagraphAudio(btn.pid)">
          <svg v-if="currentPlayingPid !== btn.pid || !isPlaying" xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd" />
          </svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" />
          </svg>
        </div>
        </div>
      </div>
      
      <div v-else class="flex-1 flex flex-col items-center justify-center text-slate-400">
         <div class="text-6xl mb-4">📖</div>
         <p>Select an article or book to start reading</p>
      </div>

      <!-- Bottom Bar: Audio Player + Recording (fixed at viewport bottom) -->
      <div v-if="currentArticle"
           class="fixed bottom-0 left-0 right-0 z-50 bg-white/95 backdrop-blur border-t border-slate-200 shadow-[0_-4px_20px_rgba(0,0,0,0.08)]">
        <div class="max-w-3xl mx-auto px-6 py-2.5 flex items-center gap-3">
          <!-- Audio Player Section -->
          <template v-if="currentPlayingPid !== null">
            <button @click="toggleSharedAudio"
                    class="w-9 h-9 rounded-full bg-blue-500 hover:bg-blue-600 text-white flex items-center justify-center transition-all shrink-0">
              <svg v-if="!isPlaying" xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd" />
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
            </button>
            <div class="flex-1 min-w-0">
              <div class="text-xs text-slate-500 font-medium mb-1 truncate">🔊 Paragraph {{ currentPlayingPid }}</div>
              <input 
                type="range" 
                min="0" 
                max="100" 
                step="0.1"
                :value="audioProgress" 
                @input="seekSharedAudio($event)"
                class="w-full h-1.5 appearance-none bg-slate-200 rounded-full cursor-pointer audio-slider"
              />
              <div class="flex justify-between mt-0.5">
                <span class="text-[11px] text-slate-400">{{ formatTime(audioProgress * audioDuration / 100) }}</span>
                <span class="text-[11px] text-slate-400">{{ formatTime(audioDuration) }}</span>
              </div>
            </div>
            <button @click="closeSharedAudio" class="text-slate-400 hover:text-red-500 transition-colors px-1 shrink-0">
              <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
              </svg>
            </button>
          </template>
          <div v-else class="flex-1 text-xs text-slate-400">Click ▶ on a paragraph to play audio</div>

          <!-- Divider -->
          <div class="w-px h-8 bg-slate-200 shrink-0"></div>

          <!-- Recording Section -->
          <button 
            @click="toggleRecording" 
            :class="[
              'w-9 h-9 rounded-full flex items-center justify-center text-base transition-all duration-200 shrink-0',
              isRecording 
                ? 'bg-red-500 hover:bg-red-600 text-white animate-pulse' 
                : 'bg-slate-100 hover:bg-slate-200 text-slate-600'
            ]"
            :title="isRecording ? 'Stop Recording' : 'Start Recording'"
          >
            {{ isRecording ? '⏹' : '🎤' }}
          </button>
          <button 
            @click="playRecordedAudio" 
            :disabled="!recordedAudioUrl"
            :class="[
              'w-9 h-9 rounded-full flex items-center justify-center text-base transition-all duration-200 shrink-0',
              recordedAudioUrl 
                ? 'bg-green-500 hover:bg-green-600 text-white' 
                : 'bg-slate-100 text-slate-300 cursor-not-allowed'
            ]"
            title="Play Recording"
          >
            ▶
          </button>
        </div>
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
                 <div v-if="anno.ai_response && !anno.ai_response.error" class="text-slate-800">
                     🤖 <span v-html="anno.ai_response.content"></span>
                 </div>
                 <div v-else-if="anno.ai_response?.error" class="text-red-600 flex items-center gap-2">
                     ❌ <span>{{ anno.ai_response.message }}</span>
                     <button @click="retryAiAssist(anno)" class="ml-auto text-xs px-2 py-1 bg-red-50 hover:bg-red-100 border border-red-200 rounded transition-colors">
                         重新获取
                     </button>
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
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import { readerApi, type Article, type ArticleDetail, type Book, type Chapter, type Annotation, type ContentType } from '@/api/readerApi'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import { BubbleMenu } from '@tiptap/vue-3/menus'
import StarterKit from '@tiptap/starter-kit'
import Highlight from '@tiptap/extension-highlight'
import Paragraph from '@tiptap/extension-paragraph'
import { useChatStore } from '@/stores/chatStore'
import BookUpload from '@/components/BookUpload.vue'

const route = useRoute()
const router = useRouter()
const chatStore = useChatStore()

// State
const activeLeftSidebar = ref<'library' | 'outline' | null>('library')
const activeOutlineIndex = ref(0)
const readingProgress = ref(0)
const showCopilot = ref(true)
const contentFilter = ref<ContentType>('all')
const articles = ref<Article[]>([])
const books = ref<Book[]>([])
const currentItemId = ref<string | null>(null)
const currentArticle = ref<ArticleDetail | null>(null)
const currentBook = ref<Book | null>(null)
const currentChapterId = ref<number | null>(null)
const annotations = ref<Annotation[]>([])
const isLoading = ref(false)

// Bubble menu state
const activeAnnotationColor = ref<'yellow' | 'blue' | 'pink' | null>(null)
const userNoteText = ref('')
const noteInputRef = ref<HTMLInputElement | null>(null)

// TTS state
const isGeneratingTts = ref(false)

// Shared audio player (single player at viewport bottom)
const sharedAudio = ref<HTMLAudioElement | null>(null)
const currentPlayingPid = ref<number | null>(null)
const isPlaying = ref(false)
const audioProgress = ref(0)
const audioDuration = ref(0)

// Audio paragraph button positions (recalculated on scroll/resize)
const audioButtonPositions = ref<{ pid: number; x: number; y: number }[]>([])

// Recording state
const isRecording = ref(false)
const mediaRecorder = ref<MediaRecorder | null>(null)
const recordedAudioUrl = ref<string | null>(null)
const recordedAudio = ref<HTMLAudioElement | null>(null)

// Tooltip state
const hoveredAnno = ref<Annotation | null>(null)
const tooltipPos = ref({ x: 0, y: 0 })

// Map colors to highlight hex
const colorMap = {
    yellow: '#fef08a',
    blue: '#bbf7d0',
    pink: '#fbcfe8'
}

// Computed
const filteredArticles = computed(() => {
  if (contentFilter.value === 'book') return []
  return articles.value
})

const filteredBooks = computed(() => {
  if (contentFilter.value === 'article') return []
  return books.value
})

// Methods
function scrollToParagraph(pid: number) {
    if (!pid) return
    const el = document.querySelector(`[data-pid="${pid}"]`)
    if (el) {
        el.scrollIntoView({ behavior: 'auto', block: 'center' })
    }
}

async function scrollToLastReadPosition() {
    if (!currentBook.value) return
    
    const chapterId = currentBook.value.last_read_chapter
    const paragraphIndex = currentBook.value.last_read_paragraph_index
    
    console.log('scrollToLastReadPosition called:', { chapterId, paragraphIndex, currentChapterId: currentChapterId.value })
    
    if (!chapterId) {
        ElMessage.warning('No reading position saved')
        return
    }
    
    // If we need to switch chapters
    if (currentChapterId.value !== chapterId) {
        console.log('Switching to chapter:', chapterId)
        await selectChapter(chapterId)
        console.log('Chapter switched, waiting for nextTick...')
        await nextTick()
        console.log('Now scrolling to paragraph index:', paragraphIndex)
        scrollToParagraphByIndex(paragraphIndex)
    } else {
        console.log('Already in correct chapter, scrolling to index:', paragraphIndex)
        scrollToParagraphByIndex(paragraphIndex)
    }
}

function scrollToParagraphByIndex(index: number) {
    const paragraphs = currentArticle.value?.paragraphs || []
    console.log('scrollToParagraphByIndex called with index:', index)
    console.log('Available paragraphs:', paragraphs.length)
    
    if (index >= 0 && index < paragraphs.length) {
        const pid = paragraphs[index].id
        console.log('Scrolling to pid:', pid)
        scrollToParagraph(pid)
    } else {
        console.log('Index out of range or no paragraphs, scrolling to top')
        // Scroll to top if index is out of range
        const editorEl = document.querySelector('.ProseMirror')
        if (editorEl) {
            editorEl.scrollTop = 0
        }
    }
}

async function saveCurrentReadPosition() {
    if (!currentBook.value || !currentChapterId.value || !currentArticle.value?.paragraphs?.length) {
        ElMessage.warning('No book or chapter selected')
        return
    }
    
    // Find the first visible paragraph
    const paragraphs = currentArticle.value.paragraphs
    let closestIndex = 0
    let closestDistance = Infinity
    
    // Get the editor element
    const editorEl = document.querySelector('.ProseMirror')
    if (editorEl) {
        const editorRect = editorEl.getBoundingClientRect()
        const viewportTop = editorRect.top
        
        // Find which paragraph is closest to the top of viewport
        for (let i = 0; i < paragraphs.length; i++) {
            const el = document.querySelector(`[data-pid="${paragraphs[i].id}"]`)
            if (el) {
                const rect = el.getBoundingClientRect()
                // Only consider paragraphs that are at or below viewport top
                if (rect.top >= viewportTop - 50) {
                    const distance = Math.abs(rect.top - viewportTop)
                    if (distance < closestDistance) {
                        closestDistance = distance
                        closestIndex = i
                    }
                }
            }
        }
    }
    
    console.log('Saving position:', {
        bookId: currentBook.value.id,
        chapterId: currentChapterId.value,
        paragraphIndex: closestIndex,
        totalParagraphs: paragraphs.length
    })
    console.log('Current book state:', currentBook.value)
    
    try {
        await readerApi.updateReadPosition(currentBook.value.id, currentChapterId.value, closestIndex)
        // Update local state
        if (currentBook.value) {
            currentBook.value.last_read_chapter = currentChapterId.value
            currentBook.value.last_read_paragraph_index = closestIndex
        }
        ElMessage.success('Reading position saved!')
    } catch (err) {
        console.error('Failed to save reading position', err)
        ElMessage.error('Failed to save reading position')
    }
}

function handleScroll(e: Event) {
    // Update reading progress
    const target = e.target as HTMLElement
    if (target) {
        const scrollTop = target.scrollTop
        const scrollHeight = target.scrollHeight - target.clientHeight
        if (scrollHeight > 0) {
            readingProgress.value = (scrollTop / scrollHeight) * 100
        }
    }
    
    // Update audio button positions on scroll
    updateAudioButtonPositions()
    
    // Update outline highlight
    if (activeLeftSidebar.value !== 'outline' || !currentArticle.value?.meta_context?.outline) return;

    const outline = currentArticle.value.meta_context.outline;
    let currentIdx = -1;

    for (let i = 0; i < outline.length; i++) {
        const item = outline[i];
        const el = document.querySelector(`[data-pid="${item.start_index}"]`) as HTMLElement;
        if (el) {
            const rect = el.getBoundingClientRect();
            if (rect.top <= 250) {
                currentIdx = i;
            } else {
                break;
            }
        }
    }

    if (currentIdx === -1 && outline.length > 0) {
        currentIdx = 0;
    }

    if (activeOutlineIndex.value !== currentIdx) {
        activeOutlineIndex.value = currentIdx;
    }
}

function setFilter(filter: ContentType) {
  contentFilter.value = filter
  fetchContent()
}

async function fetchContent() {
  try {
    const [articlesData, booksData] = await Promise.all([
      readerApi.getArticles(contentFilter.value),
      readerApi.getBooks(contentFilter.value)
    ])
    articles.value = Array.isArray(articlesData) ? articlesData : (articlesData.results || [])
    books.value = Array.isArray(booksData) ? booksData : (booksData.results || [])
  } catch (err) {
    console.error("Failed to load content", err)
  }
}

function handleBookUploaded(bookId: number) {
  fetchContent()
  selectBook(bookId)
}

async function selectBook(bookId: number) {
  currentItemId.value = `book-${bookId}`
  isLoading.value = true
  
  try {
    const book = await readerApi.getBook(bookId)
    currentBook.value = book
    
    // If book has chapters, select the first one or the last read chapter
    if (book.chapters && book.chapters.length > 0) {
      const chapterToLoad = book.last_read_chapter || book.chapters[0].id
      selectChapter(chapterToLoad)
    }
  } catch (err) {
    console.error("Failed to load book", err)
  } finally {
    isLoading.value = false
  }
}

async function selectChapter(chapterId: number) {
  currentChapterId.value = chapterId
  isLoading.value = true
  
  try {
    const chapter = await readerApi.getChapter(chapterId)
    
    // Create a fake ArticleDetail-like object for the reading view
    currentArticle.value = {
      id: chapterId,
      title: `${currentBook.value?.title || ''} - ${chapter.title}`,
      author: currentBook.value?.author || '',
      url: '',
      site_name: `Chapter ${chapter.chapter_index + 1}`,
      status: chapter.status as any,
      meta_context: {},
      raw_text: '',
      raw_html: '',
      paragraphs: chapter.paragraphs || [],
      created_at: '',
      updated_at: ''
    }
    
    // Don't update reading position here - only update when explicitly saving
    
    // Load content into editor
    loadContentIntoEditor()
    
  } catch (err) {
    console.error("Failed to load chapter", err)
  } finally {
    isLoading.value = false
  }
}

function loadContentIntoEditor() {
  if (!currentArticle.value || !editor.value) return
  
  const contentHtml = currentArticle.value.paragraphs.map(p => {
     let pContent = p.content
     if (p.annotations && p.annotations.length > 0) {
         p.annotations.forEach(anno => {
             const bg = colorMap[anno.annotation_type as keyof typeof colorMap]
             pContent = pContent.replace(anno.selected_text, `<mark style="background-color: ${bg};" data-anno-id="${anno.id}">${anno.selected_text}</mark>`)
         })
     }
     
     // Build original paragraph
     let html = `<p data-pid="${p.id}">${pContent}</p>`
     
     // Add translation in a separate paragraph if available
     if (p.translation) {
         html += `<p data-pid="${p.id}-trans" class="translation-para" style="color: #6b7280; font-size: 0.9em; font-style: italic; margin-bottom: 1.5em;">${p.translation}</p>`
     }
     
     return html
  }).join('')
  
  editor.value.commands.setContent(contentHtml)
  processExistingAnnotations()
  nextTick(() => updateAudioButtonPositions())
}

function processExistingAnnotations() {
  if (!currentArticle.value) return
  
  let allAnnos: Annotation[] = []
  currentArticle.value.paragraphs.forEach(p => {
      if (p.annotations && p.annotations.length > 0) {
          allAnnos = [...allAnnos, ...p.annotations]
      }
  })
  
  annotations.value = allAnnos.sort((a,b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
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
  await fetchContent()
  
  // Handle route params
  if (route.params.id) {
    const id = String(route.params.id)
    if (id.startsWith('article-')) {
      const articleId = parseInt(id.replace('article-', ''))
      loadArticle(articleId)
    } else if (id.startsWith('book-')) {
      const bookId = parseInt(id.replace('book-', ''))
      selectBook(bookId)
    }
  }
  
  // Update audio button positions on resize
  window.addEventListener('resize', updateAudioButtonPositions)
})

onBeforeUnmount(() => {
  editor.value?.destroy()
  clearPolling()
  window.removeEventListener('resize', updateAudioButtonPositions)
})

watch(() => route.params.id, (newId) => {
  if (newId) {
    const id = String(newId)
    if (id.startsWith('article-')) {
      const articleId = parseInt(id.replace('article-', ''))
      loadArticle(articleId)
    } else if (id.startsWith('book-')) {
      const bookId = parseInt(id.replace('book-', ''))
      selectBook(bookId)
    }
  } else {
    currentItemId.value = null
    currentArticle.value = null
    currentBook.value = null
    currentChapterId.value = null
    annotations.value = []
    editor.value?.commands.setContent('')
    clearPolling()
  }
})

watch(() => chatStore.refreshReaderTrigger, () => {
    if (currentItemId.value?.startsWith('article-')) {
        const articleId = parseInt(currentItemId.value.replace('article-', ''))
        loadArticle(articleId, true)
    } else if (currentItemId.value?.startsWith('book-') && currentChapterId.value) {
        // Save scroll position before refresh
        const editorEl = document.querySelector('.ProseMirror')
        const scrollTop = editorEl?.scrollTop || 0
        
        // Reload current chapter for books
        selectChapter(currentChapterId.value).then(() => {
            nextTick(() => {
                // Restore scroll position (get fresh element after re-render)
                const newEditorEl = document.querySelector('.ProseMirror')
                if (newEditorEl) {
                    newEditorEl.scrollTop = scrollTop
                }
            })
        })
    }
})

function handleMouseMove(e: MouseEvent) {
    const target = e.target as HTMLElement
    // Check for annotation marks
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

// Update audio play button positions (called on content change, scroll, resize)
function updateAudioButtonPositions() {
    if (!editor.value || !currentArticle.value?.paragraphs) {
        audioButtonPositions.value = []
        return
    }
    const editorEl = editor.value.view.dom as HTMLElement
    const scrollContainer = editorEl.closest('.reader-content') as HTMLElement | null
    if (!scrollContainer) return
    const containerRect = scrollContainer.getBoundingClientRect()
    const scrollTop = scrollContainer.scrollTop
    const scrollLeft = scrollContainer.scrollLeft
    const pEls = editorEl.querySelectorAll('p[data-pid]')
    const positions: { pid: number; x: number; y: number }[] = []
    pEls.forEach(pEl => {
        const pid = Number(pEl.getAttribute('data-pid'))
        const para = currentArticle.value?.paragraphs?.find(p => p.id === pid)
        if (para?.audio_url) {
            const rect = pEl.getBoundingClientRect()
            // Position relative to scroll container (absolute)
            positions.push({
                pid,
                x: rect.left - containerRect.left + scrollLeft - 32,
                y: rect.top - containerRect.top + scrollTop + 0
            })
        }
    })
    audioButtonPositions.value = positions
}

function handleEditorClick(e: MouseEvent) {
    const target = e.target as HTMLElement
    const mark = target.closest('mark[data-anno-id]')
    if (mark) {
        const annoId = Number(mark.getAttribute('data-anno-id'))
        askCopilotAboutAnnotation(annoId)
    }
}

async function saveBookmarkAtSelection() {
    if (!editor.value || !currentBook.value || !currentChapterId.value) return
    
    // Get the paragraph ID from the current selection
    const $from = editor.value.state.selection.$from
    let pid = null
    for (let d = $from.depth; d > 0; d--) {
        const node = $from.node(d)
        if (node && node.attrs && node.attrs.pid) {
            pid = Number(node.attrs.pid)
            break
        }
    }
    
    if (!pid) {
        ElMessage.warning('Could not determine paragraph')
        return
    }
    
    // Find paragraph index in current chapter
    const paragraphs = currentArticle.value?.paragraphs || []
    const paraIndex = paragraphs.findIndex(p => p.id === pid)
    
    if (paraIndex === -1) {
        ElMessage.warning('Paragraph not found')
        return
    }
    
    console.log('Saving bookmark at paragraph:', { pid, paraIndex })
    
    try {
        await readerApi.updateReadPosition(currentBook.value.id, currentChapterId.value, paraIndex)
        // Update local state
        currentBook.value.last_read_chapter = currentChapterId.value
        currentBook.value.last_read_paragraph_index = paraIndex
        ElMessage.success('Reading position saved!')
    } catch (err) {
        console.error('Failed to save reading position', err)
        ElMessage.error('Failed to save reading position')
    }
}

function askCopilotAboutSelection() {
    if (!editor.value) return
    const { from, to } = editor.value.state.selection
    const text = editor.value.state.doc.textBetween(from, to)
    
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

// TTS Generation
async function generateTtsForSelection() {
    if (!editor.value) return
    
    const { from, to } = editor.value.state.selection
    const text = editor.value.state.doc.textBetween(from, to)
    
    if (!text.trim()) {
        ElMessage.warning('Please select some text first')
        return
    }
    
    // Find paragraph ID
    const $from = editor.value.state.selection.$from
    let pid = null
    for (let d = $from.depth; d > 0; d--) {
        const node = $from.node(d)
        if (node && node.attrs && node.attrs.pid) {
            pid = Number(node.attrs.pid)
            break
        }
    }
    
    console.log('[generateTtsForSelection] text:', text.substring(0, 50), 'pid:', pid)
    
    isGeneratingTts.value = true
    try {
        const result = await readerApi.generateTts(text, pid || undefined)
        console.log('[generateTtsForSelection] result:', result)
        
        if (result.audio_url) {
            // Backend returns relative path like 'english_corner/tts/0/123.wav'
            // Need to prepend /media/ for the full URL
            // Also normalize path separators (backend may return mixed slashes)
            const normalizedPath = result.audio_url.replace(/\\/g, '/')
            const audioUrl = normalizedPath.startsWith('http') 
                ? normalizedPath 
                : `/media/${normalizedPath}`
            
            console.log('[generateTtsForSelection] audioUrl:', audioUrl)
            
            // Update paragraph's audio_url in local state so play button appears
            if (pid && currentArticle.value?.paragraphs) {
                const para = currentArticle.value.paragraphs.find(p => p.id === pid)
                if (para) {
                    para.audio_url = result.audio_url
                }
                nextTick(() => updateAudioButtonPositions())
            }
            
            // Play via shared audio player
            if (pid) {
                // Small delay so the paragraph data is updated first
                await nextTick()
                playParagraphAudio(pid)
            }
            
            ElMessage.success('Audio generated and playing')
        } else {
            console.warn('[generateTtsForSelection] No audio_url in result')
        }
    } catch (err) {
        console.error('Failed to generate TTS:', err)
        ElMessage.error('Failed to generate audio')
    } finally {
        isGeneratingTts.value = false
    }
}

// Paragraph highlight for playing audio
function addParagraphHighlight(pid: number) {
    // Remove old highlight first
    document.querySelectorAll('.ProseMirror p.audio-playing').forEach(el => {
        el.classList.remove('audio-playing')
    })
    const pEl = document.querySelector(`.ProseMirror p[data-pid="${pid}"]`)
    if (pEl) {
        pEl.classList.add('audio-playing')
    }
}

function removeParagraphHighlight(pid: number) {
    const pEl = document.querySelector(`.ProseMirror p[data-pid="${pid}"]`)
    if (pEl) {
        pEl.classList.remove('audio-playing')
    }
}

// Shared audio player functions
function playParagraphAudio(pid: number) {
    const para = currentArticle.value?.paragraphs?.find(p => p.id === pid)
    if (!para?.audio_url) return

    const normalizedPath = para.audio_url.replace(/\\/g, '/')
    const audioUrl = normalizedPath.startsWith('http') ? normalizedPath : `/media/${normalizedPath}`

    // If same paragraph, just toggle play/pause
    if (currentPlayingPid.value === pid && sharedAudio.value) {
        if (sharedAudio.value.paused) {
            sharedAudio.value.play()
            isPlaying.value = true
        } else {
            sharedAudio.value.pause()
            isPlaying.value = false
        }
        return
    }

    // New paragraph - create or replace audio
    if (sharedAudio.value) {
        sharedAudio.value.pause()
        sharedAudio.value.src = ''
    }

    const audio = new Audio(audioUrl)
    sharedAudio.value = audio
    currentPlayingPid.value = pid
    isPlaying.value = true
    audioProgress.value = 0
    audioDuration.value = 0
    
    // Highlight the paragraph
    addParagraphHighlight(pid)

    audio.addEventListener('loadedmetadata', () => {
        audioDuration.value = audio.duration
    })
    audio.addEventListener('ended', () => {
        isPlaying.value = false
        audioProgress.value = 0
        removeParagraphHighlight(pid)
    })

    audio.play()
}

function toggleSharedAudio() {
    if (!sharedAudio.value) return
    if (sharedAudio.value.paused) {
        sharedAudio.value.play()
        isPlaying.value = true
        if (currentPlayingPid.value) addParagraphHighlight(currentPlayingPid.value)
    } else {
        sharedAudio.value.pause()
        isPlaying.value = false
        if (currentPlayingPid.value) removeParagraphHighlight(currentPlayingPid.value)
    }
}

function seekSharedAudio(event: Event) {
    if (!sharedAudio.value || !sharedAudio.value.duration) return
    const target = event.target as HTMLInputElement
    const value = parseFloat(target.value)
    sharedAudio.value.currentTime = (value / 100) * sharedAudio.value.duration
    audioProgress.value = value
}

function closeSharedAudio() {
    const pid = currentPlayingPid.value
    if (sharedAudio.value) {
        sharedAudio.value.pause()
        sharedAudio.value.src = ''
    }
    sharedAudio.value = null
    currentPlayingPid.value = null
    isPlaying.value = false
    audioProgress.value = 0
    audioDuration.value = 0
    if (pid) removeParagraphHighlight(pid)
}

// Update shared audio progress periodically
setInterval(() => {
    if (sharedAudio.value && !sharedAudio.value.paused && sharedAudio.value.duration) {
        audioProgress.value = (sharedAudio.value.currentTime / sharedAudio.value.duration) * 100
    }
}, 250)

function formatTime(seconds: number): string {
    if (!seconds || isNaN(seconds)) return '0:00'
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
}

// Recording
async function toggleRecording() {
    if (isRecording.value) {
        stopRecording()
    } else {
        await startRecording()
    }
}

async function startRecording() {
    try {
        // Clear previous recording
        if (recordedAudioUrl.value) {
            URL.revokeObjectURL(recordedAudioUrl.value)
            recordedAudioUrl.value = null
        }
        // Reset the audio player object so new recording creates a fresh player
        recordedAudio.value = null
        
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        mediaRecorder.value = new MediaRecorder(stream)
        const chunks: Blob[] = []
        
        mediaRecorder.value.ondataavailable = (e) => {
            if (e.data.size > 0) {
                chunks.push(e.data)
            }
        }
        
        mediaRecorder.value.onstop = () => {
            const blob = new Blob(chunks, { type: 'audio/webm' })
            recordedAudioUrl.value = URL.createObjectURL(blob)
            
            // Stop all tracks
            stream.getTracks().forEach(track => track.stop())
            
            // Audio URL is stored for play button
            
            ElMessage.success('Recording complete! You can play it back.')
        }
        
        mediaRecorder.value.start()
        isRecording.value = true
        ElMessage.info('Recording started...')
    } catch (err) {
        console.error('Failed to start recording:', err)
        ElMessage.error('Could not access microphone')
    }
}

function stopRecording() {
    if (mediaRecorder.value && isRecording.value) {
        mediaRecorder.value.stop()
        isRecording.value = false
    }
}

function playRecordedAudio() {
    if (!recordedAudioUrl.value) return
    
    if (recordedAudio.value) {
        if (recordedAudio.value.paused) {
            recordedAudio.value.play()
        } else {
            recordedAudio.value.pause()
        }
    } else {
        recordedAudio.value = new Audio(recordedAudioUrl.value)
        recordedAudio.value.play()
        
        recordedAudio.value.addEventListener('ended', () => {
            if (recordedAudio.value) {
                recordedAudio.value.currentTime = 0
            }
        })
    }
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
                    loadArticle(id)
                } else if (data.status === 'translating') {
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
  currentItemId.value = `article-${id}`
  try {
    const data = await readerApi.getArticle(id)
    currentArticle.value = data
    currentBook.value = null
    currentChapterId.value = null
    
    loadContentIntoEditor()

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

    const colorUsed = activeAnnotationColor.value
    cancelNoteInput()

    try {
        const createdAnno = await readerApi.createAnnotation(newAnnoData)
        annotations.value.unshift(createdAnno)

        editor.value.commands.setHighlight({ color: colorMap[colorUsed], annoId: createdAnno.id } as any)
        editor.value.commands.setTextSelection(to)

        const aiResult = await readerApi.triggerAiAssist(createdAnno.id, createdAnno.user_note)
        
        const idx = annotations.value.findIndex(a => a.id === createdAnno.id)
        if (idx !== -1) {
            annotations.value[idx] = aiResult
        }

    } catch (err) {
        console.error("Failed to process annotation", err)
    }
}

async function retryAiAssist(anno: Annotation) {
    // Set loading state
    const idx = annotations.value.findIndex(a => a.id === anno.id)
    if (idx === -1) return
    annotations.value[idx] = { ...anno, ai_response: null }

    try {
        const result = await readerApi.triggerAiAssist(anno.id, anno.user_note)
        annotations.value[idx] = result
    } catch (err) {
        console.error("Retry AI assist failed", err)
        annotations.value[idx] = {
            ...anno,
            ai_response: { error: true, message: "重试失败，请稍后再试。" }
        }
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
  height: 100vh;
  overflow-y: auto;
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

:deep(.translation-para) {
  padding-left: 0;
}

:deep(mark) {
  border-radius: 4px;
  padding: 2px 0;
}

:deep(.audio-player-placeholder) {
  transition: all 0.3s ease;
}

:deep(.audio-player-placeholder:hover) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

:deep(p.audio-playing) {
  transform: scale(1.03);
  transform-origin: left center;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.06) 0%, rgba(96, 165, 250, 0.04) 100%);
  box-shadow: 0 2px 16px rgba(59, 130, 246, 0.10), 0 0 0 1px rgba(59, 130, 246, 0.08);
  border-radius: 8px;
  padding: 6px 10px;
  margin-left: -10px;
  margin-right: -10px;
  transition: transform 0.4s cubic-bezier(0.22, 1, 0.36, 1),
              background 0.4s ease,
              box-shadow 0.4s ease,
              padding 0.4s ease;
}

/* Audio slider styles */
.audio-slider {
  -webkit-appearance: none;
  appearance: none;
  height: 6px;
  background: #e2e8f0;
  border-radius: 3px;
  outline: none;
}

.audio-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #3b82f6;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  transition: transform 0.15s ease;
}

.audio-slider::-webkit-slider-thumb:hover {
  transform: scale(1.2);
}

.audio-slider::-moz-range-thumb {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #3b82f6;
  cursor: pointer;
  border: none;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  transition: transform 0.15s ease;
}

.audio-slider::-moz-range-thumb:hover {
  transform: scale(1.2);
}
</style>
