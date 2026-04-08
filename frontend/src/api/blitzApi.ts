import service from '@/api/axios'

export interface BlitzCard {
    id: number
    script_id: number
    episode: string // e.g. "S10E12"
    chunk_id: number
    order: number

    highlight: 'red' | 'yellow' | 'none'

    speaker: string

    content: {
        text: string
        text_zh: string
        audio_url?: string
        start_time?: number
        end_time?: number
    }
}

export interface BlitzStats {
    speaker: string
    count: number
}

export interface BlitzFilters {
    mode: 'normal' | 'shuffle'
    status: 'all' | 'hard' | 'review' | 'learning'
    character: string
    page: number
    limit: number
    drama_id?: number | string | null
    season?: number | null
    episode?: number | null
}

export interface BlitzResponse {
    count: number
    next: string | null
    previous: string | null
    results: BlitzCard[]
}

// Fetch Cards
export function fetchBlitzCards(params: BlitzFilters) {
    return service.get<BlitzResponse>('/scripts/blitz-cards/', {
        params
    })
}

// Fetch Stats (for Dock)
export function fetchBlitzStats(params?: Partial<BlitzFilters>) {
    return service.get<BlitzStats[]>('/scripts/blitz-cards/stats/', {
        params
    })
}

// Update Card Status
export function updateCardStatus(id: number, status: 'red' | 'yellow' | 'none') {
    return service.patch(`/scripts/blitz-cards/${id}/update_status/`, {
        status
    })
}
