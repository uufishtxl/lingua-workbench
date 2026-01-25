import { ref, onUnmounted } from 'vue'

/**
 * Composable for audio recording functionality
 * Handles microphone access, recording, and playback of recorded audio
 */
export function useRecording() {
    // State
    const isRecording = ref(false)
    const isPlayingRecordedAudio = ref(false)
    const recordedAudioUrl = ref<string | null>(null)

    // Internal variables (not exposed)
    let mediaRecorder: MediaRecorder | null = null
    let audioChunks: Blob[] = []

    /**
     * Start recording from microphone
     */
    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
            mediaRecorder = new MediaRecorder(stream)
            audioChunks = []

            mediaRecorder.ondataavailable = (event) => {
                audioChunks.push(event.data)
            }

            mediaRecorder.onstop = () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' })
                // Clean up previous URL
                if (recordedAudioUrl.value) {
                    URL.revokeObjectURL(recordedAudioUrl.value)
                }
                recordedAudioUrl.value = URL.createObjectURL(audioBlob)
            }

            mediaRecorder.start()
            isRecording.value = true
        } catch (err) {
            console.error('Error accessing microphone:', err)
        }
    }

    /**
     * Stop current recording
     */
    const stopRecording = () => {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop()
            mediaRecorder.stream.getTracks().forEach(track => track.stop())
        }
        isRecording.value = false
    }

    /**
     * Toggle recording state
     */
    const toggleRecording = async () => {
        if (isRecording.value) {
            stopRecording()
        } else {
            await startRecording()
        }
    }

    /**
     * Play the recorded audio
     */
    const playRecording = () => {
        if (recordedAudioUrl.value) {
            const audio = new Audio(recordedAudioUrl.value)
            isPlayingRecordedAudio.value = true
            audio.play()
            audio.onended = () => {
                isPlayingRecordedAudio.value = false
            }
        }
    }

    /**
     * Clear recorded audio and reset state
     */
    const clearRecording = () => {
        if (recordedAudioUrl.value) {
            URL.revokeObjectURL(recordedAudioUrl.value)
            recordedAudioUrl.value = null
        }
    }

    // Clean up on unmount
    onUnmounted(() => {
        clearRecording()
    })

    return {
        // State
        isRecording,
        recordedAudioUrl,
        isPlayingRecordedAudio,
        // Actions
        startRecording,
        stopRecording,
        toggleRecording,
        playRecording,
        clearRecording
    }
}
