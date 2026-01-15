/**
 * Highlight (Hili) related types
 * Used in SliceCard, HighlightEditor, InteractiveTextWithHilis
 */

// Abbreviated phonetic tag values stored in data
export type AbbreviatedTag = 'FT' | 'RED' | 'LINK' | 'RESYL' | 'FT_HYPHEN' | 'CUSTOM'

// Full display names for phonetic tags
export type PhoneticTagDisplay = 'Flap T' | 'Reduction' | 'Linking' | 'Resyllabification' | 'Flap-T' | 'Custom'

// Highlight (Hili) - a marked segment of text with annotations
export interface Hili {
    id: string
    start: number
    end: number
    content: string
    tags: AbbreviatedTag[]
    note: string
}

// Tag option for select dropdowns
export interface TagOption {
    value: AbbreviatedTag
    label: PhoneticTagDisplay
}

export const TAG_OPTIONS: TagOption[] = [
    { value: 'FT', label: 'Flap T' },
    { value: 'RED', label: 'Reduction' },
    { value: 'LINK', label: 'Linking' },
    { value: 'RESYL', label: 'Resyllabification' },
    { value: 'FT_HYPHEN', label: 'Flap-T' },
    { value: 'CUSTOM', label: 'Custom' },
]
