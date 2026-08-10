import apiClient from './axios'

// --- Types ---
export interface Textbook {
  id: number
  name: string
  grade: string
  semester: string
  pdf_file: string
  pdf_url: string | null
  parsed_at: string | null
  created_at: string
}

// --- API ---
export async function listTextbooks(): Promise<Textbook[]> {
  const resp = await apiClient.get<{ results: Textbook[] }>('/v1/textbooks/')
  return resp.data.results
}

export async function uploadTextbook(formData: FormData): Promise<Textbook> {
  const resp = await apiClient.post<Textbook>('/v1/textbooks/', formData)
  return resp.data
}

// --- CorpusTask (S2) ---
export type TaskRunStatus = 'pending' | 'running' | 'done' | 'error'

export interface CorpusTask {
  id: number
  name: string
  textbook: number
  textbook_name: string
  unit: number
  status: 'draft' | 'proofreading' | 'completed'
  stage: number
  created_at: string
  updated_at: string
  extract_status: TaskRunStatus
  extract_error: string
  bucket_status: TaskRunStatus
  bucket_error: string
  kp_status: TaskRunStatus
  kp_error: string
  tts_audio_url: string
  tts_status: TaskRunStatus
  tts_error: string
  paper_status: TaskRunStatus
  paper_error: string
  // ---- Stage 1 总览统计（#26） ----
  total_chars: number
  page_start: number | null
  page_end: number | null
  module_count: number
  words_count: number
  modules_present: string[]
  // ---- KP（#28） ----
  kp_progress: number
  knowledge_points: Record<string, string> | null
}

export interface CorpusTaskStats {
  total: number
  completed: number
  in_progress: number
  units_covered: number
}

export async function createCorpusTask(payload: { textbook: number; unit: number }): Promise<CorpusTask> {
  const resp = await apiClient.post<CorpusTask>('/v1/corpus-tasks/', payload)
  return resp.data
}

export async function getCorpusTask(id: number): Promise<CorpusTask> {
  const resp = await apiClient.get<CorpusTask>(`/v1/corpus-tasks/${id}/`)
  return resp.data
}

export async function listCorpusTasks(): Promise<CorpusTask[]> {
  const resp = await apiClient.get<{ results: CorpusTask[] }>('/v1/corpus-tasks/')
  return resp.data.results
}

export async function getCorpusTaskStats(): Promise<CorpusTaskStats> {
  const resp = await apiClient.get<CorpusTaskStats>('/v1/corpus-tasks/stats/')
  return resp.data
}

export async function getCorpusTaskModules(id: number): Promise<Record<string, string | null>> {
  const resp = await apiClient.get<Record<string, string | null>>(`/v1/corpus-tasks/${id}/modules/`)
  return resp.data
}

export async function triggerBucket(id: number): Promise<CorpusTask> {
  const resp = await apiClient.post<CorpusTask>(`/v1/corpus-tasks/${id}/bucket/`)
  return resp.data
}

export async function deleteCorpusTask(id: number): Promise<void> {
  await apiClient.delete(`/v1/corpus-tasks/${id}/`)
}

// --- 学习页（#34） ---
export interface TtsTimestamp {
  text: string
  start: number | null
  end: number | null
}
export interface TtsData {
  tts_audio_url: string
  tts_timestamps: Record<string, TtsTimestamp[]>
}
export async function getTtsData(id: number): Promise<TtsData> {
  const resp = await apiClient.get<TtsData>(`/v1/corpus-tasks/${id}/tts-data/`)
  return resp.data
}

export async function updateTtsSlices(
  id: number,
  tts_timestamps: Record<string, TtsTimestamp[]>,
): Promise<TtsData> {
  const resp = await apiClient.put<TtsData>(`/v1/corpus-tasks/${id}/tts-slices/`, { tts_timestamps })
  return resp.data
}

export async function updateCorpusTask(id: number, payload: Partial<CorpusTask>): Promise<CorpusTask> {
  const resp = await apiClient.patch<CorpusTask>(`/v1/corpus-tasks/${id}/`, payload)
  return resp.data
}

export async function completeCorpusTask(id: number): Promise<CorpusTask> {
  const resp = await apiClient.post<CorpusTask>(`/v1/corpus-tasks/${id}/complete/`)
  return resp.data
}

// --- S7 AI 修复 / 重新生成（#29）---
export interface FixModuleResult {
  module_key: string
  old_content: unknown
  new_content: unknown
}
export async function fixModule(id: number, payload: { module_key: string; instruction?: string }): Promise<FixModuleResult> {
  // LLM 全量重归整模块可能耗时 >60s，单独加长 timeout
  const resp = await apiClient.post<FixModuleResult>(`/v1/corpus-tasks/${id}/fix-module/`, payload, { timeout: 180000 })
  return resp.data
}
export async function applyModule(id: number, payload: { module_key: string; content: unknown }): Promise<CorpusTask> {
  const resp = await apiClient.post<CorpusTask>(`/v1/corpus-tasks/${id}/apply-module/`, payload)
  return resp.data
}
export interface RegenerateKpResult {
  kp_key: string
  old_content: string
  new_content: string
}
export async function regenerateKp(id: number, payload: { kp_key: string; instruction?: string }): Promise<RegenerateKpResult> {
  const resp = await apiClient.post<RegenerateKpResult>(`/v1/corpus-tasks/${id}/regenerate-kp/`, payload, { timeout: 180000 })
  return resp.data
}
export async function applyKp(id: number, payload: { kp_key: string; content: string }): Promise<CorpusTask> {
  const resp = await apiClient.post<CorpusTask>(`/v1/corpus-tasks/${id}/apply-kp/`, payload)
  return resp.data
}
