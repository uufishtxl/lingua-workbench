import { ref } from 'vue'
import { extractAudioSegment } from '@/utils/audioUtils'
import { transcribeAudio, pollTaskUntilComplete } from '@/api/whisperApi'

export interface UseTranscriptionOptions {
    audioUrl: string
    startTime: number
    endTime: number
}

/**
 * Composable for Whisper transcription functionality
 * Handles audio extraction and API transcription
 */
export function useTranscription() {
    // State
    const isTranscribing = ref(false)

    /**
     * Transcribe audio segment
     * @param options Audio URL and time range
     * @returns Transcribed text or null if failed
     */
    const transcribe = async (options: UseTranscriptionOptions): Promise<string | null> => {
        if (isTranscribing.value) return null

        isTranscribing.value = true
        try {
            // Extract audio segment
            const audioBlob = await extractAudioSegment(
                options.audioUrl,
                options.startTime,
                options.endTime
            )

            // Start transcription
            const { task_id } = await transcribeAudio(audioBlob)

            // Poll for result
            const result = await pollTaskUntilComplete(task_id, {
                onStatusChange: (status) => {
                    console.log(`Transcription task ${task_id} status: ${status}`)
                }
            })

            return result
        } catch (error) {
            console.error('Transcription failed:', error)
            return null
        } finally {
            isTranscribing.value = false
        }
    }

    return {
        isTranscribing,
        transcribe
    }
}
