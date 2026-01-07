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

export interface HighlightData {
    focus_segment: string
    phonetic_hilis: PhoneticHili[]
    definition?: string
    example?: ExampleData
}

export interface CreateSliceRequest {
    audio_chunk: number
    start_time: number
    end_time: number
    original_text: string
    highlights: HighlightData[]
}

export interface AudioSliceResponse {
    id: number
    audio_chunk: number
    start_time: number
    end_time: number
    original_text: string
    highlights: HighlightData[]
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
