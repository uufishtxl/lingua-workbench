import { ref, type Ref } from 'vue'
import { analyzeSoundScript, type SoundScriptResponse } from '@/api/aiAnalysisApi'

export type AiStatus = 'default' | 'loading' | 'active'
export type EditorMode = 'note' | 'sound'

export interface UseAiAnalysisOptions {
    fullContext: Ref<string>
    focusSegment: Ref<string>
}

export function useAiAnalysis(options: UseAiAnalysisOptions) {
    const { fullContext, focusSegment } = options

    // State
    const analysisResult = ref<SoundScriptResponse | null>(null)
    const aiStatus = ref<AiStatus>('default')
    const isFastSpeed = ref(true)
    const editorMode = ref<EditorMode>('note')
    const editingSegmentIndex = ref<number | null>(null)
    const editingTagIndex = ref<number | null>(null)

    // Handle AI button click
    const handleAiClick = async () => {
        if (aiStatus.value === 'loading') return

        aiStatus.value = 'loading'

        try {
            const requestData = {
                full_context: fullContext.value,
                focus_segment: focusSegment.value,
                speed_profile: isFastSpeed.value ? 'native_fast' as const : 'native_normal' as const
            }

            const result = await analyzeSoundScript(requestData)
            analysisResult.value = result
            aiStatus.value = 'active'
            return result
        } catch (error) {
            console.error('AI analysis failed:', error)
            aiStatus.value = 'default'
            return null
        }
    }

    // Handle tag click - returns the note content for the input
    const handleTagClick = (tag: string): string | null => {
        if (!analysisResult.value) return null

        const tagIndex = analysisResult.value.phonetic_tags.indexOf(tag)
        if (tagIndex !== -1 && analysisResult.value.phonetic_tag_notes?.[tagIndex]) {
            editingTagIndex.value = tagIndex
            return analysisResult.value.phonetic_tag_notes[tagIndex]
        }
        return null
    }

    // Delete a phonetic tag note
    const handleDeleteNote = (idx: number) => {
        if (!analysisResult.value) return

        analysisResult.value.phonetic_tags.splice(idx, 1)
        analysisResult.value.phonetic_tag_notes.splice(idx, 1)
    }

    // Save note: update existing or add as Custom
    const handleSaveNote = (noteContent: string): boolean => {
        if (!noteContent.trim()) return false

        // Initialize analysisResult if null
        if (!analysisResult.value) {
            analysisResult.value = {
                card_type: 'visual_sound_script',
                speed_profile: 'native_fast',
                full_context: fullContext.value,
                focus_segment: focusSegment.value,
                phonetic_tags: [],
                phonetic_tag_notes: [],
                script_segments: []
            }
        }

        if (editingTagIndex.value !== null) {
            // Update existing note
            analysisResult.value.phonetic_tag_notes[editingTagIndex.value] = noteContent
        } else {
            // Add as new Custom tag
            analysisResult.value.phonetic_tags.push('Custom')
            analysisResult.value.phonetic_tag_notes.push(noteContent)
        }

        editingTagIndex.value = null
        return true
    }

    // Handle segment click in Sound Display mode
    const handleSegmentClick = (idx: number): string | null => {
        editingSegmentIndex.value = idx
        const segment = analysisResult.value?.script_segments[idx]
        return segment?.sound_display || null
    }

    // Save segment sound_display
    const handleSaveSegment = (content: string): boolean => {
        if (editingSegmentIndex.value === null || !analysisResult.value || !content.trim()) {
            return false
        }

        const segment = analysisResult.value.script_segments[editingSegmentIndex.value]
        if (segment) {
            segment.sound_display = content
        }

        editingSegmentIndex.value = null
        return true
    }

    // Get CSS class based on segment type
    const getTypeClass = (type: string): string => {
        const typeMap: Record<string, string> = {
            'Reduction': 'type-reduction',
            'Linking': 'type-linking',
            'Assimilation': 'type-assimilation',
            'Elision': 'type-elision',
            'Flap T': 'type-flap',
            'Glottal Stop': 'type-glottal',
            'Custom': 'type-custom'
        }
        return typeMap[type] || 'type-default'
    }

    // Initialize from saved data
    const initFromSaved = (savedAnalysis: SoundScriptResponse | null) => {
        analysisResult.value = savedAnalysis
        aiStatus.value = savedAnalysis ? 'active' : 'default'
    }

    return {
        // State
        analysisResult,
        aiStatus,
        isFastSpeed,
        editorMode,
        editingSegmentIndex,
        editingTagIndex,
        // Actions
        handleAiClick,
        handleTagClick,
        handleDeleteNote,
        handleSaveNote,
        handleSegmentClick,
        handleSaveSegment,
        getTypeClass,
        initFromSaved
    }
}
