/**
 * screenshot.ts - Playwright 多阶段截图脚本
 * 
 * 前置条件：先手动在浏览器中创建一个音频切片，然后运行此脚本
 * 
 * 截图阶段：
 * 1. SliceCard 初始状态（有波形，无文本）
 * 2. 点击转录按钮后，获取文本
 * 3. 点击编辑按钮，进入编辑模式
 * 4. 退出编辑，选中文本进行高亮
 */
import { chromium, Page, Locator, Browser, BrowserContext } from 'playwright';
import * as path from 'path';
import { setAuthState, getAuthCredentials } from './utils/auth';
import { CONFIG } from './config';
import * as fs from 'fs';

// 运行时的输出目录（带日期的子文件夹）
let sessionOutputDir: string;

/**
 * 初始化输出目录（按日期创建子文件夹）
 */
function initOutputDir(): string {
    const now = new Date();
    const datestamp = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}`;
    const dir = path.join(CONFIG.outputDir, datestamp);

    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
    }

    console.log(`📁 输出目录: ${dir}`);
    return dir;
}

/**
 * 截取 SliceCard 截图
 */
async function captureSliceCard(sliceCard: Locator, stage: string): Promise<string> {
    // 简单的阶段命名，不带时间戳
    const filename = `${stage}.png`;
    const outputPath = path.join(sessionOutputDir, filename);

    await sliceCard.screenshot({
        path: outputPath,
        type: 'png',
    });

    console.log(`✅ [${stage}] → ${filename}`);
    return outputPath;
}

/**
 * 等待页面完全加载
 */
async function waitForPageReady(page: Page): Promise<void> {
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
}

/**
 * 查找第一个 SliceCard（在 "Selected Regions" 区域的 grid 内）
 * 
 * 页面结构：
 * - el-card (波形容器)
 * - el-card (Selected Regions 容器)
 *   - div.grid
 *     - el-card (SliceCard) ← 目标
 */
async function findFirstSliceCard(page: Page): Promise<Locator> {
    // 等待 "Selected Regions" 区域加载
    await page.waitForSelector('text=Selected Regions', { timeout: 10000 });

    // 等待 grid 内的 SliceCard 出现
    // SliceCard 在 .grid 容器内，且包含时间戳样式 .bg-sky-100
    await page.waitForSelector('.grid .el-card', { timeout: 10000 });

    const sliceCards = page.locator('.grid .el-card');

    const count = await sliceCards.count();

    if (count === 0) {
        throw new Error('未找到任何 SliceCard，请先在浏览器中手动创建一个音频切片');
    }

    console.log(`找到 ${count} 个 SliceCard，使用第一个`);
    return sliceCards.first();
}

/**
 * Stage 1: 截取初始状态
 */
async function stage1_InitialState(page: Page, sliceCard: Locator): Promise<void> {
    console.log('\n📸 Stage 1: 初始状态截图...');
    await sliceCard.scrollIntoViewIfNeeded();
    await page.waitForTimeout(500);
    await captureSliceCard(sliceCard, '01_initial');
}

/**
 * Stage 2: 点击转录按钮，等待文本
 */
async function stage2_Transcription(page: Page, sliceCard: Locator): Promise<void> {
    console.log('\n📸 Stage 2: 转录文本...');

    // 找到转录按钮（ArcticonsLiveTranscribe 图标的按钮）
    const transcribeBtn = sliceCard.locator('button:has(.i-arcticons-live-transcribe), button:has(svg)').first();

    // 检查按钮是否存在
    if (await transcribeBtn.count() === 0) {
        console.log('⚠️ 未找到转录按钮，跳过此阶段');
        return;
    }

    // 点击转录
    await transcribeBtn.click();
    console.log('   点击转录按钮，等待文本出现...');

    // 智能等待：检测文本区域是否有内容
    try {
        await page.waitForFunction(
            (selector) => {
                const card = document.querySelector(selector);
                if (!card) return false;
                const textArea = card.querySelector('.text-display-area');
                if (!textArea) return false;
                const text = textArea.textContent?.trim() || '';
                // 文本长度 > 5 表示转录完成（排除空白或占位符）
                return text.length > 5;
            },
            '.grid .el-card',
            { timeout: CONFIG.transcriptionTimeout }
        );
        console.log('   ✅ 转录完成！');
    } catch {
        console.log('   ⚠️ 转录等待超时，继续截图...');
    }

    await captureSliceCard(sliceCard, '02_transcribed');
}

/**
 * Stage 3: 点击编辑按钮，进入编辑模式
 */
async function stage3_EditMode(page: Page, sliceCard: Locator): Promise<void> {
    console.log('\n📸 Stage 3: 编辑模式...');

    // 找到编辑按钮（Edit 图标）
    const editBtn = sliceCard.locator('.is-edit');

    if (await editBtn.count() === 0) {
        console.log('⚠️ 未找到编辑按钮，跳过此阶段');
        return;
    }

    await editBtn.click();
    await page.waitForTimeout(500);

    await captureSliceCard(sliceCard, '03_edit_mode');
}

/**
 * Stage 4: 退出编辑，选中文本高亮
 */
async function stage4_TextHighlight(page: Page, sliceCard: Locator): Promise<void> {
    console.log('\n📸 Stage 4: 文本高亮...');

    // 点击取消按钮退出编辑模式
    // SliceCard.vue: .input__icons 内第二个按钮是取消按钮
    const cancelBtn = sliceCard.locator('.input__icons .el-button').nth(1);

    if (await cancelBtn.count() > 0) {
        console.log('   点击取消按钮退出编辑模式...');
        await cancelBtn.click();
        await page.waitForTimeout(500);
    } else {
        console.log('⚠️ 未找到取消按钮，可能不在编辑模式');
    }

    // 选中文本区域中的部分文本
    const textArea = sliceCard.locator('.text-display-area');
    if (await textArea.count() === 0) {
        console.log('⚠️ 未找到文本区域，跳过此阶段');
        return;
    }

    // 选中指定的文本
    const textToSelect = CONFIG.textToSelect;
    console.log(`   选中文本: "${textToSelect}"`);

    const found = await textArea.evaluate((el, searchText) => {
        const text = el.textContent || '';
        const startIndex = text.indexOf(searchText);

        if (startIndex === -1) {
            return false;
        }

        // 遍历文本节点找到正确的位置
        const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
        let currentOffset = 0;
        let startNode: Text | null = null;
        let startOffset = 0;
        let endNode: Text | null = null;
        let endOffset = 0;

        while (walker.nextNode()) {
            const node = walker.currentNode as Text;
            const nodeLength = node.textContent?.length || 0;

            // 查找开始位置
            if (!startNode && currentOffset + nodeLength > startIndex) {
                startNode = node;
                startOffset = startIndex - currentOffset;
            }

            // 查找结束位置
            if (startNode && currentOffset + nodeLength >= startIndex + searchText.length) {
                endNode = node;
                endOffset = startIndex + searchText.length - currentOffset;
                break;
            }

            currentOffset += nodeLength;
        }

        if (startNode && endNode) {
            const range = document.createRange();
            const selection = window.getSelection();
            range.setStart(startNode, startOffset);
            range.setEnd(endNode, endOffset);
            selection?.removeAllRanges();
            selection?.addRange(range);
            return true;
        }

        return false;
    }, textToSelect);

    if (!found) {
        console.log(`   ⚠️ 未找到文本 "${textToSelect}"，尝试选中前10个字符`);
        await textArea.evaluate((el) => {
            const range = document.createRange();
            const selection = window.getSelection();
            const textNode = el.querySelector('span') || el;
            if (textNode.firstChild) {
                range.setStart(textNode.firstChild, 0);
                range.setEnd(textNode.firstChild, Math.min(10, textNode.firstChild.textContent?.length || 0));
                selection?.removeAllRanges();
                selection?.addRange(range);
            }
        });
    }

    // 触发 mouseup 以显示高亮图标
    await textArea.dispatchEvent('mouseup');
    await page.waitForTimeout(500);

    await captureSliceCard(sliceCard, '04_text_selected');

    // 如果看到高亮按钮，点击它
    const highlighterBtn = sliceCard.locator('.highlighter-icon');
    if (await highlighterBtn.count() > 0) {
        await highlighterBtn.click();
        await page.waitForTimeout(500);
        await captureSliceCard(sliceCard, '05_highlighted');
    }
}

/**
 * Stage 5: 点击高亮文本，进入笔记编辑模式
 */
async function stage5_EnterHighlightEditor(page: Page, sliceCard: Locator): Promise<void> {
    console.log('\n📸 Stage 5: 进入高亮编辑模式...');

    // 等待 HighlightEditor 出现（dark-editor 类）
    await page.waitForTimeout(500);

    const highlightEditor = sliceCard.locator('.dark-editor');
    if (await highlightEditor.count() > 0) {
        await captureSliceCard(sliceCard, '06_highlight_editor');
    } else {
        console.log('⚠️ HighlightEditor 未出现');
    }
}

/**
 * Stage 6: 点击 AI 按钮，等待分析结果
 */
async function stage6_AIAnalysis(page: Page, sliceCard: Locator): Promise<void> {
    console.log('\n📸 Stage 6: AI 分析...');

    // 点击第一个 ✨ 按钮（Sound Script 分析）
    // 需要先滚动到 HighlightEditor 可见，然后强制点击绕过遮挡
    const highlightEditor = sliceCard.locator('.dark-editor');
    if (await highlightEditor.count() > 0) {
        await highlightEditor.scrollIntoViewIfNeeded();
    }

    const aiBtn = sliceCard.locator('.dark-editor .dict-ai-btn').first();

    if (await aiBtn.count() === 0) {
        console.log('⚠️ 未找到 AI 按钮');
        return;
    }

    // 使用 force: true 绕过元素遮挡检查
    await aiBtn.click({ force: true });
    console.log('   等待 AI 分析结果...');

    // 等待 loading 状态消失（最多等 60 秒）
    await page.waitForFunction(
        (selector) => {
            const btn = document.querySelector(selector);
            return btn && !btn.classList.contains('is-loading');
        },
        '.dict-ai-btn',
        { timeout: 60000 }
    ).catch(() => console.log('   AI 分析超时，继续...'));

    await page.waitForTimeout(500);
    await captureSliceCard(sliceCard, '07_ai_result');
}

/**
 * Stage 7: 切换到 Sound 模式，编辑发音
 */
async function stage7_SoundScriptEdit(page: Page, sliceCard: Locator): Promise<void> {
    console.log('\n📸 Stage 7: Sound Script 编辑...');

    // 点击模式切换按钮（i-tabler-notes → i-tabler-abc）
    const modeToggleBtn = sliceCard.locator('.mode-toggle-btn');
    if (await modeToggleBtn.count() > 0) {
        await modeToggleBtn.click();
        await page.waitForTimeout(300);
    }

    // 点击第一个 segment（.segment-sound-item）
    const firstSegment = sliceCard.locator('.segment-sound-item').first();
    if (await firstSegment.count() > 0) {
        await firstSegment.click();
        await page.waitForTimeout(300);
    }

    // 在输入框中输入发音 "tel[th]uhm"
    const noteInput = sliceCard.locator('.note-input textarea');
    if (await noteInput.count() > 0) {
        await noteInput.fill('tel[th]uhm');
        await page.waitForTimeout(200);
    }

    // 点击保存按钮
    const saveBtn = sliceCard.locator('.save-note-btn-inline');
    if (await saveBtn.count() > 0) {
        await saveBtn.click();
        await page.waitForTimeout(300);
    }

    await captureSliceCard(sliceCard, '08_sound_edited');
}

/**
 * Stage 8: 切换回 Note 模式
 */
async function stage8_BackToNoteMode(page: Page, sliceCard: Locator): Promise<void> {
    console.log('\n📸 Stage 8: 切换回 Note 模式...');

    // 再次点击模式切换按钮
    const modeToggleBtn = sliceCard.locator('.mode-toggle-btn');
    if (await modeToggleBtn.count() > 0) {
        await modeToggleBtn.click();
        await page.waitForTimeout(300);
    }

    await captureSliceCard(sliceCard, '09_note_mode');
}

/**
 * 主流程
 */
async function main(): Promise<void> {
    const isHeaded = process.argv.includes('--headed');

    console.log('🚀 启动 Playwright 多阶段截图工具...');
    console.log(`   模式: ${isHeaded ? 'Headed (调试)' : 'Headless'}`);
    console.log('   ⚠️ 请确保已在浏览器中手动创建了音频切片\n');

    const browser = await chromium.launch({ headless: !isHeaded });
    const context = await browser.newContext({
        viewport: { width: 1280, height: 720 },
        deviceScaleFactor: CONFIG.deviceScaleFactor,
        // 绕过缓存，确保获取最新内容
        bypassCSP: true,
    });
    const page = await context.newPage();

    // 禁用缓存
    await page.route('**/*', route => route.continue());
    await context.clearCookies();

    try {
        // 初始化输出目录
        sessionOutputDir = initOutputDir();

        // 认证
        console.log('📝 设置认证状态...');
        await page.goto(CONFIG.baseURL);
        const { accessToken, userEmail } = getAuthCredentials();
        await setAuthState(page, accessToken, userEmail);

        // 导航到 workbench
        const targetURL = `${CONFIG.baseURL}/slicer/workbench/${CONFIG.workbenchId}`;
        console.log(`🔗 导航到: ${targetURL}`);
        await page.goto(targetURL);
        await waitForPageReady(page);

        // 查找 SliceCard
        const sliceCard = await findFirstSliceCard(page);

        // 执行各阶段截图
        await stage1_InitialState(page, sliceCard);
        await stage2_Transcription(page, sliceCard);
        await stage3_EditMode(page, sliceCard);
        await stage4_TextHighlight(page, sliceCard);
        await stage5_EnterHighlightEditor(page, sliceCard);
        await stage6_AIAnalysis(page, sliceCard);
        await stage7_SoundScriptEdit(page, sliceCard);
        await stage8_BackToNoteMode(page, sliceCard);

        console.log('\n🎉 所有阶段截图完成！');

    } catch (error) {
        console.error('❌ 截图失败:', error);
        const errorScreenshot = path.join(CONFIG.outputDir, 'error-screenshot.png');
        await page.screenshot({ path: errorScreenshot, fullPage: true });
        console.log(`   错误截图已保存: ${errorScreenshot}`);
        throw error;
    } finally {
        await browser.close();
    }
}

main().catch((error) => {
    console.error(error);
    process.exit(1);
});
