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

export interface Paragraph {
    id: number;
    article: number;
    index: number;
    content: string;
    translation?: string;
    annotations: Annotation[];
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

export const readerApi = {
    // Articles
    getArticles: async () => {
        const response = await api.get<Article[]>('/v1/articles/');
        return response.data;
    },

    getArticle: async (id: number) => {
        const response = await api.get<ArticleDetail>(`/v1/articles/${id}/`);
        return response.data;
    },

    deleteArticle: async (id: number) => {
        await api.delete(`/v1/articles/${id}/`);
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
    }
};
