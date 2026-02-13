import apiClient from './axios'

// Types
export interface ScriptLine {
    id: number
    index: number
    line_type: 'dialogue' | 'action' | 'scene'
    speaker: string | null
    text: string
    text_zh: string | null
    action_note: string | null
    slice: number | null
    highlight: 'none' | 'yellow' | 'red'
}

export interface ScriptLinesResponse {
    results: ScriptLine[]
    count: number
    limit: number
}

export interface SplitResponse {
    moved_count: number
    from_chunk_id: number
    to_chunk_id: number
    start_index: number
}

export interface UndoSplitResponse {
    moved_count: number
    to_chunk_id: number
    from_chunk_id: number
}

export interface IngestResponse {
    created: number
    target_chunk_id: number
}

// API Functions

/**
 * Ingest a script from fanfr.com into the database.
 */
export const ingestScript = async (
    sourceAudioId: number,
    season: number,
    episode: number
): Promise<IngestResponse> => {
    const response = await apiClient.post('/scripts/ingest/', {
        source_audio_id: sourceAudioId,
        season,
        episode,
    })
    return response.data
}

/**
 * Get script lines for a chunk.
 */
export const getScriptLines = async (
    chunkId: number,
    limit = 50
): Promise<ScriptLinesResponse> => {
    const response = await apiClient.get(`/scripts/chunk/${chunkId}/lines/`, {
        params: { limit },
    })
    return response.data
}

/**
 * Split script: move lines from startIndex onwards to nextChunkId.
 */
export const splitScript = async (
    chunkId: number,
    startIndex: number,
    nextChunkId: number
): Promise<SplitResponse> => {
    const response = await apiClient.post(`/scripts/chunk/${chunkId}/split/`, {
        start_index: startIndex,
        next_chunk_id: nextChunkId,
    })
    return response.data
}

/**
 * Undo split: move all lines from fromChunkId back to chunkId.
 */
export const undoSplit = async (
    chunkId: number,
    fromChunkId: number
): Promise<UndoSplitResponse> => {
    const response = await apiClient.post(`/scripts/chunk/${chunkId}/undo-split/`, {
        from_chunk_id: fromChunkId,
    })
    return response.data
}

/**
 * Update a script line's highlight status.
 */
export const updateScriptLine = async (
    lineId: number,
    data: { highlight?: 'none' | 'yellow' | 'red' }
): Promise<ScriptLine> => {
    const response = await apiClient.patch(`/scripts/lines/${lineId}/`, data)
    return response.data
}

// --- Slice Search (Vector Match) ---

export interface SliceMatch {
    slice_id: number
    original_text: string
    translation: string
    start_time: number
    end_time: number
    similarity: number
}

export interface SearchSlicesResponse {
    query_text: string
    results: SliceMatch[]
    message?: string
}

/**
 * Search for matching AudioSlices using embedding similarity.
 */
export const searchSlices = async (lineId: number): Promise<SearchSlicesResponse> => {
    const response = await apiClient.post(`/scripts/lines/${lineId}/search-slices/`)
    return response.data
}

/**
 * Bind a ScriptLine to a specific AudioSlice.
 */
export const bindSlice = async (
    lineId: number,
    sliceId: number
): Promise<{ line_id: number; slice_id: number; message: string }> => {
    const response = await apiClient.post(`/scripts/lines/${lineId}/bind-slice/`, {
        slice_id: sliceId,
    })
    return response.data
}

// --- Script Task Status (Background Ingest + Translate) ---

export type ScriptTaskStatus = 'pending' | 'ingesting' | 'translating' | 'completed' | 'failed'

export interface ScriptTaskResponse {
    id: number
    status: ScriptTaskStatus
    message: string
    ingest_count: number
    translate_count: number
    created_at: string
    updated_at: string
}

/**
 * Get the latest script task status for a source audio.
 */
export const getScriptTaskStatus = async (
    sourceAudioId: number
): Promise<ScriptTaskResponse> => {
    const response = await apiClient.get('/scripts/task_status/', {
        params: { source_audio_id: sourceAudioId },
    })
    return response.data
}

interface PollScriptTaskOptions {
    interval?: number       // Polling interval in ms, default 3000
    maxAttempts?: number    // Max retries, default 120 (~6 min)
    onStatusChange?: (status: ScriptTaskStatus, message: string) => void
}

/**
 * Poll script task until completed or failed.
 * Returns the final task response.
 */
export const pollScriptTask = async (
    sourceAudioId: number,
    options: PollScriptTaskOptions = {}
): Promise<ScriptTaskResponse> => {
    const {
        interval = 3000,
        maxAttempts = 120,
        onStatusChange,
    } = options

    let attempts = 0
    let lastStatus = ''

    while (attempts < maxAttempts) {
        try {
            const task = await getScriptTaskStatus(sourceAudioId)

            if (task.status !== lastStatus) {
                lastStatus = task.status
                onStatusChange?.(task.status, task.message)
            }

            if (task.status === 'completed') {
                return task
            }

            if (task.status === 'failed') {
                throw new Error(task.message || 'Script task failed')
            }
        } catch (err: any) {
            // 404 means task not created yet, keep waiting
            if (err?.response?.status !== 404) {
                throw err
            }
        }

        await new Promise(resolve => setTimeout(resolve, interval))
        attempts++
    }

    throw new Error('Script task timeout: max polling attempts reached')
}
