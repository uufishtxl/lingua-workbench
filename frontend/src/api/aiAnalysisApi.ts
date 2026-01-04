/**
 * AI Analysis API client
 * For calling the sound-script and other AI analysis endpoints
 */
import apiClient from './axios'

// Types matching backend SoundScriptResponse
export interface ScriptSegment {
    original: string
    sound_display: string
    ipa: string
    type: string
    is_stressed: boolean
    note: string
}

export interface SoundScriptResponse {
    card_type: 'visual_sound_script'
    speed_profile: 'native_fast' | 'native_normal'
    full_context: string
    focus_segment: string
    phonetic_tags: string[]
    script_segments: ScriptSegment[]
}

export interface SoundScriptRequest {
    full_context: string
    focus_segment: string
    speed_profile?: 'native_fast' | 'native_normal'
}

/**
 * Analyze a text segment and get phonetic breakdown.
 * Note: This is a long-running request (~10s), so we use a longer timeout.
 */
export async function analyzeSoundScript(
    request: SoundScriptRequest
): Promise<SoundScriptResponse> {
    const response = await apiClient.post<SoundScriptResponse>(
        '/ai/sound-script/',
        request,
        { timeout: 30000 } // 30 second timeout for AI requests
    )
    return response.data
}
