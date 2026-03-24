import type { WordNode } from '@/api/englishCornerApi';

export interface TextToken {
  text: string;
  isVocab: boolean;
  vocabData?: WordNode;
}

/**
 * Splits text into tokens based on available vocabulary nodes.
 * Uses a longest-match-first strategy to avoid partial matches.
 */
export function tokenizeByVocab(text: string, vocabNodes: WordNode[]): TextToken[] {
  if (!text || vocabNodes.length === 0) {
    return [{ text, isVocab: false }];
  }

  const result: TextToken[] = [];
  let currentIndex = 0;

  // Create a sorted list of vocabs by length (descending) to match longer phrases first
  const sortedVocabs = [...vocabNodes].sort((a, b) => b.label.length - a.label.length);

  while (currentIndex < text.length) {
    let match: WordNode | null = null;
    let matchPos = -1;

    // Find the earliest match from this position
    // Note: We search from currentIndex onwards
    const remainingText = text.slice(currentIndex).toLowerCase();
    
    // Check all vocabs for the earliest occurrence
    let earliestPos = Infinity;
    
    for (const vocab of sortedVocabs) {
      const pos = remainingText.indexOf(vocab.label.toLowerCase());
      if (pos !== -1 && pos < earliestPos) {
        earliestPos = pos;
        match = vocab;
        matchPos = pos;
      } else if (pos !== -1 && pos === earliestPos && match && vocab.label.length > match.label.length) {
        // Longest match if positions are identical
        match = vocab;
      }
    }

    if (match && matchPos !== -1) {
      // 1. Push text before the match
      if (matchPos > 0) {
        result.push({
          text: text.slice(currentIndex, currentIndex + matchPos),
          isVocab: false
        });
      }

      // 2. Push the match itself (using original casing from the text)
      const actualText = text.slice(currentIndex + matchPos, currentIndex + matchPos + match.label.length);
      result.push({
        text: actualText,
        isVocab: true,
        vocabData: match
      });

      // 3. Jump past the match
      currentIndex += matchPos + match.label.length;
    } else {
      // No more matches found
      result.push({
        text: text.slice(currentIndex),
        isVocab: false
      });
      break;
    }
  }

  return result;
}
