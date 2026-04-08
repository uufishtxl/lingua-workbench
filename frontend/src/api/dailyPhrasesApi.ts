import service from '@/api/axios'

export interface Scenario {
  description: string;
  tag: string;
}

export interface BonusWord {
  id: number;
  word: string;
}

export interface SessionWord {
  id: number;
  word: string;
  explanation: string;
  scenarios: Scenario[];
  bonus_words: BonusWord[];
}

export interface DailyPhrasesInitResponse {
  is_completed: boolean;
  words_practiced: number;
  session_words?: SessionWord[];
  completed_at?: string;
  summary?: {
    focus_minutes: number;
    daily_streak_percent: number;
  };
}

export interface Alternative {
  vibe: string;
  expression: string;
  example: string;
}

export interface VerifyResponse {
  verification: {
    is_pass: boolean;
    polished_text: string;
    native_version?: string;
    community_version?: string;
    feedback: string;
    mastered_word_ids: number[];
    alternatives?: Alternative[];
  };
  session_progress: {
    words_practiced: number;
    is_completed: boolean;
  };
}

export interface RefreshBonusResponse {
  bonus_words: BonusWord[];
}

export const dailyPhrasesApi = {
  // Initialize the daily session
  initSession() {
    return service.get<DailyPhrasesInitResponse>('/v1/daily-phrases/init/')
  },

  // Verify the user's sentence
  verifySentence(wordId: number, userSentence: string, activeBonusWords: BonusWord[]) {
    return service.post<VerifyResponse>('/v1/daily-phrases/verify/', {
      word_id: wordId,
      user_sentence: userSentence,
      active_bonus_words: activeBonusWords
    })
  },

  // Refresh bonus words
  refreshBonus(excludeIds: number[]) {
    const idsParams = excludeIds.join(',')
    return service.get<RefreshBonusResponse>(`/v1/daily-phrases/refresh-bonus/?exclude_ids=${idsParams}`)
  }
}
