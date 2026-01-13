/**
 * config.ts - 共享配置
 * 
 * 集中管理所有截图脚本的配置项
 */
import * as path from 'path';

export const CONFIG = {
    // === 基础配置 ===
    baseURL: 'http://localhost:5173',

    // === 截图目标 ===
    /** AudioChunk 的 ID（URL 中 /slicer/workbench/{id}） */
    workbenchId: 15,

    // === 截图设置 ===
    /** 截图输出目录 */
    outputDir: path.resolve(__dirname, '../screenshots'),

    /** 视口大小 */
    viewport: { width: 1920, height: 1080 },

    /** 设备像素比（200% 缩放 = 2） */
    deviceScaleFactor: 2,

    // === 超时设置 ===
    /** 转录等待超时（毫秒） */
    transcriptionTimeout: 30000,

    /** AI 分析等待超时（毫秒） */
    aiAnalysisTimeout: 60000,

    // === 交互配置 ===
    /** Stage 4 要选中的文本（用于高亮演示） */
    textToSelect: 'tell them',

    /** Stage 7 要输入的发音 */
    soundInput: 'tel[th]uhm',
};

export default CONFIG;
