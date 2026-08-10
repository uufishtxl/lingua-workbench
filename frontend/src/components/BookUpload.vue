<template>
  <div class="book-upload">
    <!-- Upload Button -->
    <button @click="showUploadDialog = true" 
            class="w-full p-2 border-2 border-dashed border-slate-300 rounded-lg text-slate-500 hover:border-blue-400 hover:text-blue-500 transition-colors flex items-center justify-center gap-2 text-sm">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
      </svg>
      Upload PDF Book
    </button>

    <!-- Upload Dialog -->
    <div v-if="showUploadDialog" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6">
        <h3 class="text-lg font-bold text-slate-800 mb-4">Upload PDF Book</h3>
        
        <!-- File Input -->
        <div class="mb-4">
          <label class="block text-sm font-medium text-slate-700 mb-2">Select PDF File</label>
          <input type="file" accept=".pdf" @change="handleFileSelect" 
                 class="w-full p-3 border border-slate-200 rounded-lg text-sm file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100">
        </div>

        <!-- Book Metadata -->
        <div class="space-y-3 mb-4">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">Title (optional)</label>
            <input v-model="bookTitle" type="text" placeholder="Extracted from filename if empty"
                   class="w-full p-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent">
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">Author (optional)</label>
            <input v-model="bookAuthor" type="text" placeholder="Book author"
                   class="w-full p-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent">
          </div>
        </div>

        <!-- Error Message -->
        <div v-if="error" class="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
          {{ error }}
        </div>

        <!-- Actions -->
        <div class="flex justify-end gap-3">
          <button @click="closeDialog" 
                  class="px-4 py-2 text-sm text-slate-600 hover:text-slate-800 transition-colors">
            Cancel
          </button>
          <button @click="uploadBook" :disabled="!selectedFile || isUploading"
                  class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2">
            <svg v-if="isUploading" class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ isUploading ? 'Uploading...' : 'Upload' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { readerApi } from '@/api/readerApi'

const emit = defineEmits<{
  (e: 'uploaded', bookId: number): void
}>()

const showUploadDialog = ref(false)
const selectedFile = ref<File | null>(null)
const bookTitle = ref('')
const bookAuthor = ref('')
const isUploading = ref(false)
const error = ref('')

function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files && input.files[0]) {
    selectedFile.value = input.files[0]
    // Auto-fill title from filename
    if (!bookTitle.value) {
      bookTitle.value = input.files[0].name.replace('.pdf', '')
    }
  }
}

async function uploadBook() {
  if (!selectedFile.value) return
  
  isUploading.value = true
  error.value = ''
  
  try {
    const formData = new FormData()
    formData.append('pdf_file', selectedFile.value)
    formData.append('original_filename', selectedFile.value.name)
    
    if (bookTitle.value) {
      formData.append('title', bookTitle.value)
    }
    if (bookAuthor.value) {
      formData.append('author', bookAuthor.value)
    }
    
    const book = await readerApi.uploadBook(formData)
    emit('uploaded', book.id)
    closeDialog()
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to upload book'
  } finally {
    isUploading.value = false
  }
}

function closeDialog() {
  showUploadDialog.value = false
  selectedFile.value = null
  bookTitle.value = ''
  bookAuthor.value = ''
  error.value = ''
}
</script>
