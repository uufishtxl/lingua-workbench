import service from '@/api/axios'

// Reuse types from existing sources if possible, but defining specific response types here for clarity
export interface TranslationTask {
    id: number
    original_text: string
    translation?: string | null
    // Add other fields if needed for display context (like drama name, episode etc - might need serializer update if we want those)
    // For now, AudioSliceSerializer returns basic fields.
}

export interface BatchTranslateResponse {
    message: string
    translations: { id: number; translation: string }[]
}

export const translationApi = {
    // Get idioms missing translation
    getMissingTranslations() {
        return service.get<TranslationTask[]>('/v1/audioslices/missing_translations/')
    },

    // Batch translate list of IDs
    batchTranslate(ids: number[]) {
        return service.post<BatchTranslateResponse>('/v1/audioslices/batch_translate/', { ids })
    }
}
