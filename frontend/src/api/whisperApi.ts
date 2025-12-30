/**
 * Whisper API service for audio transcription
 */

interface TranscribeResponse {
    status: string;
    task_id: number;
    message: string;
}

interface TaskStatusResponse {
    id: number;
    filename: string;
    status: 'queued' | 'processing' | 'completed' | 'failed';
    result: string | null;
    created_at: string;
    error?: string;
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

    const url = new URL(`${WHISPER_BASE_URL}/transcribe`, window.location.origin);
    if (skipLlm) {
        url.searchParams.set('skip_llm', 'true');
    }

    const response = await fetch(url.pathname + url.search, {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        throw new Error(`Transcribe request failed: ${response.statusText}`);
    }

    return response.json();
}

/**
 * 查询任务状态
 * @param taskId 任务 ID
 * @returns 任务状态响应
 */
export async function getTaskStatus(taskId: number): Promise<TaskStatusResponse> {
    const response = await fetch(`${WHISPER_BASE_URL}/task/${taskId}`);

    if (!response.ok) {
        throw new Error(`Get task status failed: ${response.statusText}`);
    }

    return response.json();
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
            return taskStatus.result || '';
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
