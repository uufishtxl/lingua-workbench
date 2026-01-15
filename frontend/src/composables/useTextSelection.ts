import { ref, reactive, type Ref } from 'vue'
import { v4 as uuidv4 } from 'uuid'
import type { Hili } from '@/types/highlight'

export interface TextSelectionInfo {
    text: string
    start: number
    end: number
    rect: DOMRect | null
}

export interface UseTextSelectionOptions {
    containerRef: Ref<HTMLElement | null>
    originalText: Ref<string>
    highlights: Ref<Hili[]>
    isEditing: Ref<boolean>
}

/**
 * Composable for text selection and highlight creation
 * Handles selection detection, highlighter icon positioning, and highlight creation
 */
export function useTextSelection(options: UseTextSelectionOptions) {
    const { containerRef, originalText, highlights, isEditing } = options

    // State
    const selectedTextInfo = ref<TextSelectionInfo | null>(null)
    const highlighterIconVisible = ref(false)
    const highlighterIconPosition = reactive({ top: '0px', left: '0px' })

    /**
     * Handle text selection (call on mouseup)
     */
    const handleTextSelection = () => {
        if (isEditing.value) return

        const selection = window.getSelection()
        if (!selection || selection.rangeCount === 0 || selection.isCollapsed || !containerRef.value) {
            return
        }

        const range = selection.getRangeAt(0)
        const selectedText = selection.toString()

        if (selectedText && containerRef.value.contains(range.commonAncestorContainer)) {
            // Use string search to avoid ruby text interference
            const startIndex = originalText.value.indexOf(selectedText)

            if (startIndex === -1) {
                resetSelection()
                return
            }

            const rect = range.getBoundingClientRect()
            const parentRect = containerRef.value.getBoundingClientRect()

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
     * Reset selection state and hide highlighter icon
     */
    const resetSelection = () => {
        highlighterIconVisible.value = false
        selectedTextInfo.value = null
    }

    /**
     * Create a new highlight from current selection
     * Returns the new highlight ID or null if no selection
     */
    const createHighlight = (): string | null => {
        if (!selectedTextInfo.value) return null

        const newHighlight: Hili = {
            id: uuidv4(),
            start: selectedTextInfo.value.start,
            end: selectedTextInfo.value.end,
            content: selectedTextInfo.value.text,
            tags: [],
            note: ''
        }

        highlights.value.push(newHighlight)
        window.getSelection()?.removeAllRanges()
        resetSelection()

        return newHighlight.id
    }

    return {
        // State
        selectedTextInfo,
        highlighterIconVisible,
        highlighterIconPosition,
        // Actions
        handleTextSelection,
        resetSelection,
        createHighlight
    }
}
