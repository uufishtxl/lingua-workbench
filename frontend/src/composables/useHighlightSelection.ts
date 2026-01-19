import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { v4 as uuidv4 } from 'uuid'
import type { Hili } from '@/types/highlight'

export interface UseHighlightSelectionOptions {
    containerRef: ReturnType<typeof ref<HTMLElement | null>>
    currentText: () => string
    isEditingMode: () => boolean
    onHighlightCreated: (highlight: Hili) => void
}

/**
 * Composable for text selection and highlighting functionality
 * Handles text selection, highlighter icon positioning, and highlight creation
 */
export function useHighlightSelection(options: UseHighlightSelectionOptions) {
    // State
    const selectedTextInfo = ref<{ text: string; start: number; end: number; rect: DOMRect | null } | null>(null)
    const highlighterIconVisible = ref(false)
    const highlighterIconPosition = reactive({ top: '0px', left: '0px' })

    /**
     * Reset selection state and hide highlighter icon
     */
    const resetSelection = () => {
        highlighterIconVisible.value = false
    }

    /**
     * Handle text selection in the container
     */
    const handleTextSelection = () => {
        if (options.isEditingMode()) return

        const selection = window.getSelection()
        const container = options.containerRef.value

        if (!selection || selection.rangeCount === 0 || selection.isCollapsed || !container) {
            return
        }

        const range = selection.getRangeAt(0)
        const selectedText = selection.toString()

        if (selectedText && container.contains(range.commonAncestorContainer)) {
            // Use string search instead of DOM position to avoid ruby text interference
            const originalText = options.currentText()
            const startIndex = originalText.indexOf(selectedText)

            if (startIndex === -1) {
                resetSelection()
                return
            }

            const rect = range.getBoundingClientRect()
            const parentRect = container.getBoundingClientRect()

            selectedTextInfo.value = {
                text: selectedText,
                start: startIndex,
                end: startIndex + selectedText.length,
                rect
            }

            highlighterIconPosition.top = `${rect.top - parentRect.top - 30}px`
            highlighterIconPosition.left = `${rect.left - parentRect.left + rect.width / 2}px`
            highlighterIconVisible.value = true
        } else {
            resetSelection()
        }
    }

    /**
     * Handle click on highlighter icon - creates a new highlight
     */
    const handleHighlighterClick = () => {
        if (!selectedTextInfo.value) return

        const newHighlight: Hili = {
            id: uuidv4(),
            start: selectedTextInfo.value.start,
            end: selectedTextInfo.value.end,
            content: selectedTextInfo.value.text,
            tags: [],
            note: '',
        }

        options.onHighlightCreated(newHighlight)
        window.getSelection()?.removeAllRanges()
        resetSelection()
    }

    /**
     * Global mouseup listener to clear selection when user clicks elsewhere
     */
    const handleWindowMouseUp = () => {
        setTimeout(() => {
            const selection = window.getSelection()
            if (!selection || selection.isCollapsed) {
                resetSelection()
            }
        }, 100)
    }

    // Lifecycle - register/unregister global listeners
    onMounted(() => {
        document.addEventListener('mouseup', handleWindowMouseUp)
    })

    onUnmounted(() => {
        document.removeEventListener('mouseup', handleWindowMouseUp)
    })

    return {
        // State
        selectedTextInfo,
        highlighterIconVisible,
        highlighterIconPosition,
        // Methods
        handleTextSelection,
        handleHighlighterClick,
        resetSelection
    }
}
