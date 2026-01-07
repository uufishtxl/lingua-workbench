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
    is_stressed: boolean
}

export interface SoundScriptResponse {
    card_type: 'visual_sound_script'
    speed_profile: 'native_fast' | 'native_normal'
    full_context: string
    focus_segment: string
    phonetic_tags: string[]
    phonetic_tag_notes: string[]  // Corresponds to phonetic_tags
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

// Dictionary Types
export interface ExampleSentence {
    english: string
    chinese: string
}

export interface DictionaryResponse {
    card_type: 'dictionary'
    word_or_phrase: string
    part_of_speech: string
    definition_en: string
    definition_cn: string
    examples: ExampleSentence[]
    usage_note: string
}

export interface DictionaryRequest {
    full_context: string
    word_or_phrase: string
}

/**
 * Look up a word or phrase and get dictionary entry.
 */
export async function lookupDictionary(
    request: DictionaryRequest
): Promise<DictionaryResponse> {
    const response = await apiClient.post<DictionaryResponse>(
        '/ai/dictionary/',
        request,
        { timeout: 30000 }
    )
    return response.data
}

// Refresh Example Types
export interface RefreshExampleResponse {
    word_or_phrase: string
    example: ExampleSentence
}

export interface RefreshExampleRequest {
    word_or_phrase: string
    definition: string
    original_context: string
}

/**
 * Generate a new example sentence for a word/phrase.
 */
export async function refreshExample(
    request: RefreshExampleRequest
): Promise<RefreshExampleResponse> {
    const response = await apiClient.post<RefreshExampleResponse>(
        '/ai/refresh-example/',
        request,
        { timeout: 30000 }
    )
    return response.data
}
