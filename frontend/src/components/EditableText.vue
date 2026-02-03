<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'

const props = withDefaults(defineProps<{
    modelValue: string | null
    placeholder?: string
    rows?: number
    displayClass?: string
}>(), {
    placeholder: '点击编辑...',
    rows: 2,
    displayClass: 'text-lg text-zinc-700'
})

const emit = defineEmits<{
    'update:modelValue': [value: string]
    'save': [value: string]
}>()

const isEditing = ref(false)
const editingText = ref('')
const inputRef = ref<HTMLTextAreaElement | null>(null)

// Watch for external changes to modelValue
watch(() => props.modelValue, (newVal) => {
    if (!isEditing.value) {
        editingText.value = newVal || ''
    }
})

const startEdit = () => {
    editingText.value = props.modelValue || ''
    isEditing.value = true
    nextTick(() => inputRef.value?.focus())
}

const cancelEdit = () => {
    isEditing.value = false
    editingText.value = ''
}

const saveEdit = () => {
    const newText = editingText.value.trim()
    
    // Skip if empty or unchanged
    if (!newText || newText === props.modelValue) {
        cancelEdit()
        return
    }

    emit('update:modelValue', newText)
    emit('save', newText)
    isEditing.value = false
}
</script>

<template>
    <div class="w-full">
        <!-- Display Mode -->
        <p 
            v-if="!isEditing"
            @click="startEdit"
            :class="[displayClass, 'cursor-pointer hover:text-blue-600 transition-colors']"
            :title="'Click to edit'"
        >
            {{ modelValue || placeholder }}
        </p>

        <!-- Edit Mode -->
        <div v-else class="w-full relative">
            <textarea
                v-model="editingText"
                ref="inputRef"
                :rows="rows"
                class="w-full bg-zinc-50 border-2 border-blue-300 rounded-xl p-3 pr-20 text-lg text-center focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 outline-none resize-none font-serif"
                :placeholder="placeholder"
                @keydown.ctrl.enter="saveEdit"
                @keydown.esc="cancelEdit"
            ></textarea>
            <!-- Action Buttons -->
            <div class="absolute right-2 bottom-2 flex gap-1">
                <button 
                    @click="cancelEdit"
                    class="p-1.5 rounded-full text-zinc-400 hover:text-zinc-600 hover:bg-zinc-200 transition-all"
                    title="取消 (Esc)"
                >
                    <i-tabler-x class="text-base" />
                </button>
                <button 
                    @click="saveEdit"
                    class="p-1.5 rounded-full text-green-500 hover:text-green-600 hover:bg-green-100 transition-all"
                    title="保存 (Ctrl+Enter)"
                >
                    <i-tabler-check class="text-base" />
                </button>
            </div>
        </div>
    </div>
</template>
