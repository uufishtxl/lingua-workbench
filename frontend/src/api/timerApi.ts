import api from './axios';

export interface PomodoroTag {
    id: number;
    name: string;
    order: number;
}

export interface Pomodoro {
    id: number;
    duration: number;
    tag: PomodoroTag;
    tag_id?: number;
    created_at: string;
    completed_at: string | null;
    status: 'started' | 'completed' | 'interrupted';
    user: number;
    task: string | null;
}

export const timerApi = {
    async getTags(): Promise<PomodoroTag[]> {
        const response = await api.get<PomodoroTag[]>('/v1/pomodoro-tags/');
        return response.data;
    },

    /** POST: 按下开始键时调用，后端记录 created_at 并设置 status=started */
    async startPomodoro(data: { tag_id: number; duration: number }): Promise<Pomodoro> {
        const response = await api.post<Pomodoro>('/v1/pomodoros/', {
            tag_id: data.tag_id,
            duration: data.duration,
            // status 默认为 'started'（后端 Model default）
        });
        return response.data;
    },

    /** PATCH: 倒计时自然结束时调用，后端自动填入 completed_at */
    async completePomodoro(id: number): Promise<Pomodoro> {
        const response = await api.patch<Pomodoro>(`/v1/pomodoros/${id}/`, {
            status: 'completed'
        });
        return response.data;
    },

    /** PATCH: 用户主动中断时调用，后端自动填入 completed_at */
    async interruptPomodoro(id: number): Promise<Pomodoro> {
        const response = await api.patch<Pomodoro>(`/v1/pomodoros/${id}/`, {
            status: 'interrupted'
        });
        return response.data;
    },

    /** GET: 页面加载时检查活跃会话 */
    async getOngoing(): Promise<Pomodoro | null> {
        const response = await api.get('/v1/pomodoros/ongoing/');
        if (response.status === 204) return null;
        return response.data;
    },

    /** GET: 获取某天的专注历史，按 created_at 升序 */
    async getHistory(date: string): Promise<Pomodoro[]> {
        const response = await api.get<Pomodoro[]>(`/v1/pomodoros/history/?date=${date}`);
        return response.data;
    },

    /** PATCH: 更新某条记录的备注 */
    async updateNote(id: number, task: string): Promise<Pomodoro> {
        const response = await api.patch<Pomodoro>(`/v1/pomodoros/${id}/`, { task });
        return response.data;
    },

    /** GET: 获取最早的记录日期（日历可选范围边界） */
    async getEarliestDate(): Promise<string | null> {
        const response = await api.get<{ date: string | null }>('/v1/pomodoros/earliest/');
        return response.data.date;
    }
};
