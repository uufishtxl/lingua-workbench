/**
 * Whisper API service for audio transcription
 */
import axios from 'axios';

interface TranscribeResponse {
    status: string;
    task_id: number;
    message: string;
}

interface TaskStatusResponse {
    id: number;
    filename: string;
    source_url?: string;
    video_title?: string;
    thumbnail_url?: string;
    duration?: number;
    whisper_model?: string;
    status: 'queued' | 'processing' | 'completed' | 'failed';
    result: string | null;
    created_at: string;
    error?: string;
}

interface VideoInfo {
    title: string;
    thumbnail_url: string;
    duration: number;
    author: string;
    platform: string;
    url: string;
}

interface PollOptions {
    interval?: number;      // 轮询间隔（毫秒），默认 1000
    maxAttempts?: number;   // 最大重试次数，默认 60
    onStatusChange?: (status: string) => void;  // 状态变化回调
}

const WHISPER_BASE_URL = '/whisper';

/**
 * 上传音频文件到 Whisper 服务进行转写
 * @param audioBlob 音频 Blob
 * @param options 配置项
 * @returns 包含 task_id 的响应
 */
export async function transcribeAudio(
    audioBlob: Blob,
    options: { filename?: string; skipLlm?: boolean } = {}
): Promise<TranscribeResponse> {
    const { filename = 'audio.wav', skipLlm = true } = options;

    const formData = new FormData();
    formData.append('file', audioBlob, filename);

    const response = await axios.post<TranscribeResponse>(
        `${WHISPER_BASE_URL}/transcribe`,
        formData,
        {
            params: skipLlm ? { skip_llm: 'true' } : undefined,
        }
    );

    return response.data;
}

/**
 * 查询任务状态
 * @param taskId 任务 ID
 * @returns 任务状态响应
 */
export async function getTaskStatus(taskId: number): Promise<TaskStatusResponse> {
    const response = await axios.get<TaskStatusResponse>(
        `${WHISPER_BASE_URL}/task/${taskId}`
    );

    return response.data;
}



/**
 * 轮询任务直到完成或失败
 * @param taskId 任务 ID
 * @param options 轮询选项
 * @returns 转写结果文本
 */
export async function pollTaskUntilComplete(
    taskId: number,
    options: PollOptions = {}
): Promise<string> {
    const {
        interval = 1000,
        maxAttempts = 60,
        onStatusChange,
    } = options;

    let attempts = 0;
    let lastStatus = '';

    while (attempts < maxAttempts) {
        const taskStatus = await getTaskStatus(taskId);

        // 通知状态变化
        if (taskStatus.status !== lastStatus) {
            lastStatus = taskStatus.status;
            onStatusChange?.(taskStatus.status);
        }

        if (taskStatus.status === 'completed') {
            const raw = taskStatus.result || '';
            // 兼容 segments JSON（corpus TTS 流程后 /transcribe 返回 [{text,start,end}]）
            if (raw.trim().startsWith('[')) {
                try {
                    const segs = JSON.parse(raw);
                    if (Array.isArray(segs)) {
                        return segs.map((s: any) => s.text || '').join(' ');
                    }
                } catch { /* 非 JSON 数组则按原样返回 */ }
            }
            return raw;
        }

        if (taskStatus.status === 'failed') {
            throw new Error(`Transcription failed: ${taskStatus.result || 'Unknown error'}`);
        }

        // 等待后继续轮询
        await new Promise(resolve => setTimeout(resolve, interval));
        attempts++;
    }

    throw new Error('Transcription timeout: max polling attempts reached');
}


/**
 * 获取视频元数据
 * @param url 视频 URL
 * @returns 视频信息
 */
export async function getVideoInfo(url: string): Promise<VideoInfo> {
    const response = await axios.get<VideoInfo>(
        `${WHISPER_BASE_URL}/info`,
        {
            params: { url }
        }
    );

    return response.data;
}

/**
 * 通过 URL 进行转录
 * @param url 视频 URL
 * @param options 选项
 * @returns 任务信息
 */
export async function transcribeUrl(
    url: string,
    options: { skipLlm?: boolean; whisperModel?: string; videoTitle?: string; thumbnailUrl?: string; duration?: number } = {}
): Promise<TranscribeResponse> {
    const { skipLlm = true, whisperModel = 'base', videoTitle = '', thumbnailUrl = '', duration = 0 } = options;
    
    const response = await axios.post<TranscribeResponse>(
        `${WHISPER_BASE_URL}/transcribe-url`,
        null,
        {
            params: {
                url,
                skip_llm: skipLlm,
                whisper_model: whisperModel,
                video_title: videoTitle,
                thumbnail_url: thumbnailUrl,
                duration: duration
            }
        }
    );

    return response.data;
}



/**
 * 获取任务列表
 * @param limit 返回数量
 * @returns 任务列表
 */
export async function getTasks(limit: number = 50): Promise<TaskStatusResponse[]> {
    const response = await axios.get<TaskStatusResponse[]>(
        `${WHISPER_BASE_URL}/tasks`,
        {
            params: { limit }
        }
    );

    return response.data;
}

export async function pinTask(taskId: number): Promise<void> {
    await axios.post(`${WHISPER_BASE_URL}/tasks/${taskId}/pin`);
}

export async function unpinTask(taskId: number): Promise<void> {
    await axios.post(`${WHISPER_BASE_URL}/tasks/${taskId}/unpin`);
}

export async function deleteTask(taskId: number): Promise<void> {
    await axios.delete(`${WHISPER_BASE_URL}/tasks/${taskId}`);
}

export async function retryTask(taskId: number): Promise<void> {
    await axios.post(`${WHISPER_BASE_URL}/tasks/${taskId}/retry`);
}
