import api from './axios';

export interface Article {
    id: number;
    url: string;
    title: string;
    author: string;
    site_name: string;
    status: 'processing' | 'translating' | 'ready' | 'failed';
    meta_context: any;
    created_at: string;
    updated_at: string;
}

export interface Book {
    id: number;
    title: string;
    author: string;
    original_filename: string;
    status: 'processing' | 'ready' | 'failed';
    meta_context: any;
    last_read_chapter: number | null;
    last_read_paragraph_index: number;
    last_read_at: string | null;
    chapters?: Chapter[];
    created_at: string;
    updated_at: string;
}

export interface Chapter {
    id: number;
    book: number;
    title: string;
    chapter_index: number;
    start_page: number;
    end_page: number;
    status: 'processing' | 'ready' | 'failed';
    paragraphs?: Paragraph[];
}

export interface Paragraph {
    id: number;
    article: number | null;
    chapter: number | null;
    index: number;
    content: string;
    translation?: string;
    annotations: Annotation[];
    audio_url?: string;
}

export interface Annotation {
    id: number;
    paragraph: number;
    selected_text: string;
    user_note: string;
    annotation_type: 'yellow' | 'blue' | 'pink';
    ai_response: any;
    created_at: string;
}

export interface ArticleDetail extends Article {
    raw_text: string;
    raw_html: string;
    paragraphs: Paragraph[];
}

export type ContentType = 'all' | 'article' | 'book';

export const readerApi = {
    // Articles
    getArticles: async (type?: ContentType) => {
        const params = type && type !== 'all' ? { type } : {};
        const response = await api.get<Article[]>('/v1/articles/', { params });
        return response.data;
    },

    getArticle: async (id: number) => {
        const response = await api.get<ArticleDetail>(`/v1/articles/${id}/`);
        return response.data;
    },

    deleteArticle: async (id: number) => {
        await api.delete(`/v1/articles/${id}/`);
    },

    // Books
    getBooks: async (type?: ContentType) => {
        const params = type && type !== 'all' ? { type } : {};
        const response = await api.get<Book[]>('/v1/books/', { params });
        return response.data;
    },

    getBook: async (id: number) => {
        const response = await api.get<Book>(`/v1/books/${id}/`);
        return response.data;
    },

    uploadBook: async (formData: FormData) => {
        const response = await api.post<Book>('/v1/books/', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    deleteBook: async (id: number) => {
        await api.delete(`/v1/books/${id}/`);
    },

    updateReadPosition: async (bookId: number, chapterId: number, paragraphIndex: number = 0) => {
        const response = await api.put(`/v1/books/${bookId}/update-read-position/`, {
            chapter_id: chapterId,
            paragraph_index: paragraphIndex,
        });
        return response.data;
    },

    // Chapters
    getChapters: async (bookId: number) => {
        const response = await api.get<Chapter[]>('/v1/chapters/', {
            params: { book: bookId },
        });
        return response.data;
    },

    getChapter: async (id: number) => {
        const response = await api.get<Chapter>(`/v1/chapters/${id}/`);
        return response.data;
    },

    // Annotations
    createAnnotation: async (data: {
        paragraph: number;
        selected_text: string;
        annotation_type: 'yellow' | 'blue' | 'pink';
        user_note?: string;
    }) => {
        const response = await api.post<Annotation>('/v1/annotations/', data);
        return response.data;
    },

    updateAnnotation: async (id: number, data: Partial<Annotation>) => {
        const response = await api.patch<Annotation>(`/v1/annotations/${id}/`, data);
        return response.data;
    },

    deleteAnnotation: async (id: number) => {
        await api.delete(`/v1/annotations/${id}/`);
    },

    // AI Assist
    triggerAiAssist: async (annotationId: number, userNote?: string) => {
        const data = userNote ? { user_note: userNote } : {};
        const response = await api.post<Annotation>(`/v1/annotations/${annotationId}/ai_assist/`, data);
        return response.data;
    },

    // TTS Audio Generation
    generateTts: async (text: string, paragraphId?: number) => {
        const response = await api.post<{ audio_url: string }>('/v1/tts/generate/', {
            text,
            paragraph_id: paragraphId
        }, {
            timeout: 300000 // 5 minutes for TTS generation
        });
        return response.data;
    }
};
