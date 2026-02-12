import apiClient from './axios'

// --- Types ---

export interface ResumeData {
    has_content: boolean
    message?: string
    chunk_id?: number
    chunk_index?: number
    total_chunks?: number
    is_studied?: boolean
    last_studied_at?: string | null
    source_audio?: {
        id: number
        drama_id: number
        drama_name: string
        season: number
        episode: number
        title: string
        cover_url: string | null
    }
}

export interface DashboardStats {
    total_chunks_studied: number
    hard_sentences: number
    review_sentences: number
}

// --- API Functions ---

/**
 * Get the chunk to resume learning from.
 */
export async function getResumeData(): Promise<ResumeData> {
    const response = await apiClient.get<ResumeData>('/v1/dashboard/resume/')
    return response.data
}

/**
 * Get learning stats for the dashboard.
 */
export async function getDashboardStats(): Promise<DashboardStats> {
    const response = await apiClient.get<DashboardStats>('/v1/dashboard/stats/')
    return response.data
}

export interface UploadCoverResponse {
    success: boolean
    source_audio_id: number
    cover_url: string | null
}

/**
 * Upload a cover image for an episode (SourceAudio).
 */
export async function uploadEpisodeCover(sourceAudioId: number, file: File): Promise<UploadCoverResponse> {
    const formData = new FormData()
    formData.append('cover_image', file)

    const response = await apiClient.post<UploadCoverResponse>(
        `/v1/audios/${sourceAudioId}/upload_cover/`,
        formData,
        {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        }
    )
    return response.data
}
