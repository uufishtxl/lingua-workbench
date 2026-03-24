import axios from './axios';

// ================================================================
// Types — matching backend serializer output
// ================================================================

export interface Scenario {
  id: number;
  title: string;
  description: string;
  icon: string;
  system_prompt: string;
  is_preset: boolean;
  created_at: string;
}

export interface TutorFeedback {
  polished_text: string;
  explanation_cn: string;
}

export interface CharacterReply {
  content: string;
  audio_url: string | null;
}

export interface PracticeMessage {
  id: number;
  role: 'user' | 'assistant';
  status: 'PENDING' | 'PROCESSING' | 'SUCCESS' | 'FAILED';
  is_processed: boolean;
  timestamp: string;
  user_content: string;
  tutor_feedback: TutorFeedback | null;
  character_reply: CharacterReply | null;
}

export interface Conversation {
  id: number;
  scenario: number;
  scenario_title: string;
  scenario_icon: string;
  summary: string;
  is_active: boolean;
  created_at: string;
  messages?: PracticeMessage[];
}

export interface WordNode {
  id: number;
  label: string;
  node_type: 'keyword' | 'phrase';
  explanation: string;
  example: string;
  status: 'PENDING' | 'SUCCESS' | 'FAILED';
  mastery: number;
  box_level: number;
  message_ids?: number[];
}

export interface GraphData {
  nodes: WordNode[];
  links: {
    source: string;
    target: string;
    relation: string;
  }[];
}

export interface Flashcard {
  id: number;
  target_phrase: string;
  prompt_question: string;
  answer: string;
  example_context: string;
  box_level: number;
  next_review_at: string;
  created_at: string;
}

// ================================================================
// API Functions
// ================================================================

export const englishCornerApi = {
  // --- Scenarios ---
  getScenarios: () =>
    axios.get<Scenario[]>('/scenarios/'),

  createScenario: (payload: { title: string; description: string; icon: string }) =>
    axios.post<Scenario>('/scenarios/', payload),

  // --- Conversations ---
  createConversation: (scenarioId: number) =>
    axios.post<Conversation>('/conversations/', { scenario: scenarioId }),

  getConversationDetail: (conversationId: number) =>
    axios.get<Conversation>(`/conversations/${conversationId}/`),

  // --- Messages (async 202 pattern) ---
  sendMessage: (conversationId: number, content: string) =>
    axios.post<{ message_id: number }>(
      `/conversations/${conversationId}/messages/`,
      { content },
    ),

  getMessage: (conversationId: number, messageId: number) =>
    axios.get<PracticeMessage>(
      `/conversations/${conversationId}/messages/${messageId}/`,
    ),

  getMessages: (conversationId: number, offset = 0, limit = 10) =>
    axios.get<{ results: PracticeMessage[]; has_more: boolean }>(
      `/conversations/${conversationId}/messages/`,
      { params: { offset, limit } }
    ),

  // --- Flashcards ---
  generateFlashcard: (payload: { message_id: number; text: string }) =>
    axios.post<Flashcard>('/flashcards/generate/', payload),

  // --- Review ---
  getReviewToday: () =>
    axios.get<Flashcard[]>('/review/today/'),

  submitReview: (cardId: number, success: boolean) =>
    axios.post<{ status: string; box_level: number }>(`/flashcards/${cardId}/review/`, { success }),

  // --- Knowledge Graph ---
  getGraph: (scenarioId?: number) =>
    axios.get<GraphData>('/relationship-graph/', { params: { scenario_id: scenarioId } }),

  // --- Vocab Extraction ---
  extractVocab: (payload: { text: string; scenario_id?: number; message_id?: number; context_sentence?: string }) =>
    axios.post<WordNode>('/extract/', payload),
};
