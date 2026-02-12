import { ref, watch, onUnmounted, type Ref } from 'vue'

export interface AudioSlice {
    audio_url: string
    start_time: number
    end_time: number
}

/**
 * Composable for audio slice playback
 * Handles preloading, seeking, and play/pause toggle for audio slices
 * 
 * @param audioRef - Ref to the HTML audio element
 * @param currentSlice - Reactive reference to the current audio slice data
 */
export function useAudio(
    audioRef: Ref<HTMLAudioElement | null>,
    currentSlice: Ref<AudioSlice | null | undefined>
) {
    // State
    const isPlaying = ref(false)
    const isLoading = ref(false)
    const isReady = ref(false)

    // Internal: track timeupdate listener for cleanup
    let activeTimeUpdateListener: ((e: Event) => void) | null = null
    let listenersInitialized = false

    /**
     * Setup play/pause/ended event listeners on the audio element
     */
    const setupPlaybackListeners = () => {
        if (!audioRef.value || listenersInitialized) return
        const audio = audioRef.value

        audio.addEventListener('play', () => {
            isPlaying.value = true
        })
        audio.addEventListener('pause', () => {
            isPlaying.value = false
        })
        audio.addEventListener('ended', () => {
            isPlaying.value = false
        })
        listenersInitialized = true
    }

    /**
     * Stop playback and clean up
     */
    const stop = () => {
        if (!audioRef.value) return
        const audio = audioRef.value

        if (!audio.paused) {
            audio.pause()
        }
        isPlaying.value = false

        // Clean up timeupdate listener
        if (activeTimeUpdateListener) {
            audio.removeEventListener('timeupdate', activeTimeUpdateListener)
            activeTimeUpdateListener = null
        }
    }

    /**
     * Setup listener to stop at end_time
     */
    const setupStopAtEndListener = () => {
        if (!audioRef.value || !currentSlice.value) return
        const audio = audioRef.value
        const stopTime = Number(currentSlice.value.end_time) || 0

        // Remove any existing listener
        if (activeTimeUpdateListener) {
            audio.removeEventListener('timeupdate', activeTimeUpdateListener)
        }

        const handleTimeUpdate = () => {
            if (audio.currentTime >= stopTime) {
                audio.pause()
                audio.removeEventListener('timeupdate', handleTimeUpdate)
                if (activeTimeUpdateListener === handleTimeUpdate) {
                    activeTimeUpdateListener = null
                }
            }
        }

        activeTimeUpdateListener = handleTimeUpdate
        audio.addEventListener('timeupdate', handleTimeUpdate)
    }

    /**
     * Toggle play/pause
     * When playing: pause
     * When paused: seek to start_time and play
     */
    const toggle = () => {
        if (!audioRef.value || !currentSlice.value || isLoading.value) return

        console.log("Toggle Play/Pause", audioRef.value, currentSlice.value)
        const audio = audioRef.value

        if (!audio.paused) {
            // Currently playing -> pause
            audio.pause()
        } else {
            // Currently paused -> play from start_time
            const targetTime = Number(currentSlice.value.start_time) || 0
            audio.currentTime = targetTime
            setupStopAtEndListener()
            audio.play().catch(e => console.warn('Audio play blocked', e))
        }
    }

    /**
     * Play from start (always resets position)
     */
    const play = () => {
        if (!audioRef.value || !currentSlice.value || isLoading.value) return
        const audio = audioRef.value

        const targetTime = Number(currentSlice.value.start_time) || 0
        audio.currentTime = targetTime
        setupStopAtEndListener()
        audio.play().catch(e => console.warn('Audio play blocked', e))
    }

    /**
     * Pause playback
     */
    const pause = () => {
        if (!audioRef.value) return
        audioRef.value.pause()
    }

    // Watch for slice changes and preload audio
    watch(currentSlice, (newSlice) => {
        if (!audioRef.value) return
        const audio = audioRef.value

        setupPlaybackListeners()

        // 1. Stop any currently playing audio
        stop()

        // 2. If no new slice, reset state
        if (!newSlice) {
            isLoading.value = false
            isReady.value = false
            return
        }

        // 3. Start loading new audio
        const targetSrc = newSlice.audio_url
        const targetTime = Number(newSlice.start_time) || 0

        // Only reload if source changed
        const currentSrcUrl = audio.src ? new URL(audio.src, window.location.href).href : ''
        const targetSrcUrl = new URL(targetSrc, window.location.href).href

        if (currentSrcUrl !== targetSrcUrl) {
            isLoading.value = true
            isReady.value = false

            audio.src = targetSrc

            // Use loadedmetadata for reliable seeking
            const onLoadedMetadata = () => {
                audio.currentTime = targetTime
                audio.removeEventListener('loadedmetadata', onLoadedMetadata)
            }

            // Use seeked to confirm seek completed
            const onSeeked = () => {
                isLoading.value = false
                isReady.value = true
                audio.removeEventListener('seeked', onSeeked)
            }

            // Fallback: canplaythrough + timeout
            const onCanPlay = () => {
                if (isLoading.value) {
                    audio.currentTime = targetTime
                }
                setTimeout(() => {
                    if (isLoading.value) {
                        isLoading.value = false
                        isReady.value = true
                    }
                }, 100)
                audio.removeEventListener('canplaythrough', onCanPlay)
            }

            const onError = () => {
                isLoading.value = false
                isReady.value = false
                console.error('Failed to load audio:', targetSrc)
                audio.removeEventListener('error', onError)
                audio.removeEventListener('loadedmetadata', onLoadedMetadata)
                audio.removeEventListener('seeked', onSeeked)
                audio.removeEventListener('canplaythrough', onCanPlay)
            }

            audio.addEventListener('loadedmetadata', onLoadedMetadata)
            audio.addEventListener('seeked', onSeeked)
            audio.addEventListener('canplaythrough', onCanPlay)
            audio.addEventListener('error', onError)
            audio.load()
        } else {
            // Same source, just seek
            audio.currentTime = targetTime
            isReady.value = true
        }
    }, { immediate: true })

    // Cleanup on unmount
    onUnmounted(() => {
        stop()
    })

    return {
        // State
        isPlaying,
        isLoading,
        isReady,
        // Actions
        toggle,
        play,
        pause,
        stop
    }
}
