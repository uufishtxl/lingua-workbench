import { defineConfig } from '@playwright/test';
import { CONFIG } from './src/config';

export default defineConfig({
    use: {
        baseURL: CONFIG.baseURL,
        // 使用 Chromium 浏览器
        browserName: 'chromium',
        // 截图时不显示浏览器窗口（可通过 --headed 参数覆盖）
        headless: true,
        // 视口大小
        viewport: CONFIG.viewport,
        // 设备像素比
        deviceScaleFactor: CONFIG.deviceScaleFactor,
    },
    // 截图输出目录
    outputDir: CONFIG.outputDir,
});
