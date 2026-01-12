/**
 * auth.ts - 认证辅助模块
 * 
 * 通过注入 localStorage 中的 Pinia 持久化 token 来模拟登录状态
 */
import { Page } from 'playwright';
import * as fs from 'fs';
import * as path from 'path';

interface AuthState {
    accessToken: string;
    userEmail: string;
}

/**
 * 设置认证状态到 localStorage
 * 
 * @param page - Playwright Page 对象
 * @param accessToken - JWT access token
 * @param userEmail - 用户邮箱
 */
export async function setAuthState(
    page: Page,
    accessToken: string,
    userEmail: string
): Promise<void> {
    // Pinia persist 存储格式 (based on authStore.ts)
    const piniaAuthState = JSON.stringify({
        accessToken,
        userEmail,
        isRefreshing: false,
    });

    await page.evaluate((state: string) => {
        // Pinia persist 默认使用 store id 作为 key
        (window as any).localStorage.setItem('auth', state);
    }, piniaAuthState);
}

/**
 * 从配置文件读取认证信息
 */
export function getAuthCredentials(): AuthState {
    const configPath = path.resolve(__dirname, '../../auth.config.json');

    if (!fs.existsSync(configPath)) {
        throw new Error(
            `找不到配置文件: ${configPath}\n` +
            '请创建 auth.config.json 文件，内容为：\n' +
            '{\n' +
            '  "accessToken": "你的token",\n' +
            '  "userEmail": "your-email@example.com"\n' +
            '}'
        );
    }

    const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));

    if (!config.accessToken || config.accessToken === '在这里粘贴你的 token') {
        throw new Error(
            '请在 auth.config.json 中填入有效的 accessToken。\n' +
            '获取方法：登录前端后，在浏览器 DevTools Console 运行：\n' +
            '  JSON.parse(localStorage.getItem("auth")).accessToken'
        );
    }

    return {
        accessToken: config.accessToken,
        userEmail: config.userEmail || 'test@example.com',
    };
}

