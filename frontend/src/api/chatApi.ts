/**
 * Documentation Assistant Chat API
 * 
 * Provides interface to the DITA RAG chatbot with SSE streaming support.
 */
import apiClient from './axios';

export interface ChatSource {
    title: string;
    path: string;
    topic_type: string;
}

export interface ChatResponse {
    answer: string;
    sources: ChatSource[];
}

export type AudienceType = 'user' | 'developer';

/**
 * Send a chat message and get a complete response (non-streaming).
 */
export async function sendChatMessage(
    message: string,
    audience: AudienceType = 'user'
): Promise<ChatResponse> {
    const response = await apiClient.post('/doc-assistant/chat/', {
        message,
        audience,
    });
    return response.data;
}

/**
 * SSE Event types from the streaming endpoint
 */
interface SSETokenEvent {
    type: 'token';
    content: string;
}

interface SSESourcesEvent {
    type: 'sources';
    sources: ChatSource[];
}

interface SSEDoneEvent {
    type: 'done';
}

interface SSEErrorEvent {
    type: 'error';
    error: string;
}

type SSEEvent = SSETokenEvent | SSESourcesEvent | SSEDoneEvent | SSEErrorEvent;

/**
 * Callbacks for streaming chat events
 */
export interface StreamCallbacks {
    onToken: (token: string) => void;
    onSources: (sources: ChatSource[]) => void;
    onDone: () => void;
    onError: (error: string) => void;
}

/**
 * Send a chat message with streaming response (SSE).
 * Provides typewriter effect via callbacks.
 */
export async function streamChatMessage(
    message: string,
    audience: AudienceType = 'user',
    callbacks: StreamCallbacks
): Promise<void> {
    // Get the access token for authentication
    const authStore = await import('@/stores/authStore').then(m => m.useAuthStore());
    const token = authStore.accessToken;

    // Use fetch for SSE (axios doesn't support streaming well)
    const response = await fetch('/api/doc-assistant/chat/stream/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ message, audience }),
        credentials: 'include',
    });

    if (!response.ok) {
        callbacks.onError(`HTTP error: ${response.status}`);
        return;
    }

    const reader = response.body?.getReader();
    if (!reader) {
        callbacks.onError('No response body');
        return;
    }

    const decoder = new TextDecoder();
    let buffer = '';

    try {
        while (true) {
            const { done, value } = await reader.read();

            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            // Process complete SSE events
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // Keep incomplete line in buffer

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const jsonStr = line.slice(6); // Remove 'data: ' prefix

                    try {
                        const event: SSEEvent = JSON.parse(jsonStr);

                        switch (event.type) {
                            case 'token':
                                callbacks.onToken(event.content);
                                break;
                            case 'sources':
                                callbacks.onSources(event.sources);
                                break;
                            case 'done':
                                callbacks.onDone();
                                break;
                            case 'error':
                                callbacks.onError(event.error);
                                break;
                        }
                    } catch (e) {
                        console.warn('Failed to parse SSE event:', jsonStr);
                    }
                }
            }
        }
    } finally {
        reader.releaseLock();
    }
}
