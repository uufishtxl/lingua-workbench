import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useChatStore = defineStore('chat', () => {
    const isExpanded = ref(false)
    const inputMessage = ref('')

    function toggle() {
        isExpanded.value = !isExpanded.value
    }

    function open() {
        isExpanded.value = true
    }

    function close() {
        isExpanded.value = false
    }

    function appendToInput(text: string) {
        if (inputMessage.value) {
            inputMessage.value += ' ' + text
        } else {
            inputMessage.value = text
        }
    }

    // Active Selection State (for Ctrl+Enter hotkey)
    const activeSelection = ref<{ lineId: number, text: string } | null>(null)

    function setActiveSelection(lineId: number, text: string) {
        activeSelection.value = { lineId, text }
    }

    function clearActiveSelection() {
        activeSelection.value = null
        selectionCoordinates.value = null
    }

    // Coordinates for floating button
    const selectionCoordinates = ref<{ x: number, y: number } | null>(null)

    function setSelectionCoordinates(x: number, y: number) {
        selectionCoordinates.value = { x, y }
    }

    // Widget Position (left/right)
    const position = ref<'left' | 'right'>('right')

    function togglePosition() {
        position.value = position.value === 'right' ? 'left' : 'right'
    }

    return {
        isExpanded,
        inputMessage,
        activeSelection,
        selectionCoordinates,
        position,
        toggle,
        open,
        close,
        appendToInput,
        setActiveSelection,
        clearActiveSelection,
        setSelectionCoordinates,
        togglePosition
    }
})

