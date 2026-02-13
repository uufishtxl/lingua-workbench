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

    return {
        isExpanded,
        inputMessage,
        toggle,
        open,
        close,
        appendToInput
    }
})
