import service from '@/api/axios'

export interface ReviewCard {
    id: number
    box_level: number
    next_review_date: string
    review_type: 'translation' | 'listening'
    slice_text: string
    slice_translation: string | null
    audio_url: string
    start_time: number
    end_time: number
    audio_slice: number // ID of the underlying slice
}

export interface ReviewSubmissionResult {
    status: string
    new_level: number
    next_review: string
}

export const reviewApi = {
    // Get all cards due for review
    getDueReviews() {
        return service.get<ReviewCard[]>('/v1/reviews/due/')
    },

    // Submit a review result (success/fail)
    submitReview(cardId: number, success: boolean) {
        return service.post<ReviewSubmissionResult>(`/v1/reviews/${cardId}/submit/`, { success })
    },

    // Update slice translation
    updateTranslation(sliceId: number, translation: string) {
        return service.patch(`/v1/audioslices/${sliceId}/`, { translation })
    },

    // Update any AudioSlice fields (original_text, translation, etc.)
    updateSlice(sliceId: number, data: Partial<{ translation: string; original_text: string }>) {
        return service.patch(`/v1/audioslices/${sliceId}/`, data)
    }
}
