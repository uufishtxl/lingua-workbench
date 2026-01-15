import { ref, type Ref } from 'vue'
import { lookupDictionary, refreshExample, type DictionaryResponse } from '@/api/aiAnalysisApi'

export type DictStatus = 'default' | 'loading' | 'active'

export interface UseDictionaryOptions {
    fullContext: Ref<string>
    wordOrPhrase: Ref<string>
}

export function useDictionary(options: UseDictionaryOptions) {
    const { fullContext, wordOrPhrase } = options

    // State
    const dictionaryResult = ref<DictionaryResponse | null>(null)
    const dictStatus = ref<DictStatus>('default')
    const exampleStatus = ref<DictStatus>('default')
    const showEnglishExample = ref(false)
    const isEditingDefinition = ref(false)

    // Handle dictionary button (✨) click
    const handleDictClick = async () => {
        if (dictStatus.value === 'loading') return

        dictStatus.value = 'loading'

        try {
            const requestData = {
                full_context: fullContext.value,
                word_or_phrase: wordOrPhrase.value
            }

            const result = await lookupDictionary(requestData)
            dictionaryResult.value = result
            dictStatus.value = 'active'
            return result
        } catch (error) {
            console.error('Dictionary lookup failed:', error)
            dictStatus.value = 'default'
            return null
        }
    }

    // Handle refresh example button click
    const handleRefreshExample = async () => {
        if (exampleStatus.value === 'loading') return
        if (!dictionaryResult.value) return

        exampleStatus.value = 'loading'

        try {
            const result = await refreshExample({
                word_or_phrase: dictionaryResult.value.word_or_phrase,
                definition: dictionaryResult.value.definition_cn || '',
                original_context: fullContext.value,
                current_example: dictionaryResult.value.examples?.[0]?.chinese || ''
            })

            dictionaryResult.value.examples = [result.example]
            exampleStatus.value = 'active'
            return result
        } catch (error) {
            console.error('Refresh example failed:', error)
            exampleStatus.value = 'default'
            return null
        }
    }

    // Handle definition click - returns the definition content for editing
    const handleDefinitionClick = (): string | null => {
        if (!dictionaryResult.value?.definition_cn) return null

        isEditingDefinition.value = true
        return dictionaryResult.value.definition_cn
    }

    // Save edited definition
    const handleSaveDefinition = (content: string): boolean => {
        if (!content.trim() || !dictionaryResult.value) return false

        dictionaryResult.value.definition_cn = content
        isEditingDefinition.value = false
        return true
    }

    // Toggle example language
    const toggleExampleLanguage = () => {
        showEnglishExample.value = !showEnglishExample.value
    }

    // Initialize from saved data
    const initFromSaved = (savedDictionary: DictionaryResponse | null) => {
        dictionaryResult.value = savedDictionary
        dictStatus.value = savedDictionary ? 'active' : 'default'
    }

    return {
        // State
        dictionaryResult,
        dictStatus,
        exampleStatus,
        showEnglishExample,
        isEditingDefinition,
        // Actions
        handleDictClick,
        handleRefreshExample,
        handleDefinitionClick,
        handleSaveDefinition,
        toggleExampleLanguage,
        initFromSaved
    }
}
