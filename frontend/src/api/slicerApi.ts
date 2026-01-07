import apiClient from './axios'

// --- Types ---
export interface PhoneticHili {
    type: string
    note: string
}

export interface ExampleData {
    example_zh: string
    example_en: string
}

// Re-export API response types for convenience
export type { SoundScriptResponse, DictionaryResponse } from './aiAnalysisApi'
import type { SoundScriptResponse, DictionaryResponse } from './aiAnalysisApi'

export interface HighlightData {
    id: string           // UUID for the highlight
    start: number        // Character position in original_text
    end: number          // Character position in original_text
    focus_segment: string
    // Store raw API responses directly - no conversion needed
    analysis?: SoundScriptResponse | null
    dictionary?: DictionaryResponse | null
}

export interface CreateSliceRequest {
    id?: number  // Database ID for updates (omit for new slices)
    audio_chunk: number
    start_time: number
    end_time: number
    original_text: string
    highlights: HighlightData[]
    is_favorite?: boolean
}

export interface AudioSliceResponse {
    id: number
    audio_chunk: number
    start_time: number
    end_time: number
    original_text: string
    highlights: HighlightData[]
    is_favorite: boolean
    created_at: string
    updated_at: string
}

// --- API Functions ---

/**
 * Create or update multiple audio slices in batch.
 * Uses update_or_create on backend - same chunk/start/end will update existing.
 */
export async function createBatchSlices(
    slices: CreateSliceRequest[]
): Promise<AudioSliceResponse[]> {
    const response = await apiClient.post<AudioSliceResponse[]>(
        '/v1/audioslices/create_batch/',
        slices
    )
    return response.data
}

/**
 * Get all slices for a specific audio chunk.
 * Handles DRF pagination response format.
 */
export async function getSlicesByChunk(
    chunkId: number
): Promise<AudioSliceResponse[]> {
    const response = await apiClient.get<{ results: AudioSliceResponse[] } | AudioSliceResponse[]>(
        '/v1/audioslices/',
        { params: { audio_chunk: chunkId } }
    )
    // Handle both paginated and non-paginated responses
    if (Array.isArray(response.data)) {
        return response.data
    }
    return response.data.results || []
}

/**
 * Delete a single audio slice by ID.
 */
export async function deleteSlice(sliceId: number): Promise<void> {
    await apiClient.delete(`/v1/audioslices/${sliceId}/`)
}
