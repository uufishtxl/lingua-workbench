#!/usr/bin/env node
/**
 * 从 notes-frontend.md 生成知识图谱 Mermaid 代码
 * 
 * 用法：
 *   node generate-knowledge-chart.js
 * 
 * 输出：
 *   knowledge-chart.md（包含 Mermaid 图）
 */

const fs = require('fs');
const path = require('path');

const NOTES_FILE = path.join(__dirname, 'notes-frontend.md');
const OUTPUT_DIR = 'C:\\projects\\my-tech-notebook\\knowledge_charts';
const OUTPUT_FILE = path.join(OUTPUT_DIR, 'frontend-knowledge-chart.md');

function parseNotes(content) {
    const sections = [];
    const lines = content.split('\n');

    let currentSection = null;

    for (const line of lines) {
        // 解析 ## 数字. 标题 格式
        const sectionMatch = line.match(/^## (?:(\d+)\. )?(.+)$/);
        if (sectionMatch) {
            const num = sectionMatch[1] || sections.filter(s => !s.isQuickRef).length + 1;
            currentSection = {
                id: `s${num}`,
                title: sectionMatch[2],
                keywords: []
            };
            sections.push(currentSection);
            continue;
        }

        // 解析速查表中的知识点（只在没进入详细章节时）
        if (!currentSection) {
            const tableMatch = line.match(/^\| \*\*(.+?)\*\* \|/);
            if (tableMatch) {
                sections.push({
                    id: `k${sections.length}`,
                    title: tableMatch[1],
                    keywords: [],
                    isQuickRef: true
                });
            }
        }
    }

    return sections;
}

function generateMermaid(sections) {
    let mermaid = '```mermaid\nflowchart TB\n';

    // 添加子图：速查表
    mermaid += '  subgraph QuickRef["📌 知识点速查"]\n';
    const quickRefs = sections.filter(s => s.isQuickRef);
    quickRefs.forEach(s => {
        mermaid += `    ${s.id}["${s.title}"]\n`;
    });
    mermaid += '  end\n\n';

    // 添加子图：详细章节
    mermaid += '  subgraph Details["📖 详细章节"]\n';
    const details = sections.filter(s => !s.isQuickRef);
    details.forEach(s => {
        mermaid += `    ${s.id}["${s.title}"]\n`;
    });
    mermaid += '  end\n\n';

    // 添加关联（速查表 -> 详细章节）
    mermaid += '  %% 关联\n';
    quickRefs.forEach((qr, i) => {
        // 简单匹配：如果标题相似就连接
        details.forEach(d => {
            if (d.title.toLowerCase().includes(qr.title.toLowerCase().split(' ')[0])) {
                mermaid += `  ${qr.id} --> ${d.id}\n`;
            }
        });
    });

    mermaid += '```\n';
    return mermaid;
}

function main() {
    console.log('📖 读取笔记文件...');
    const content = fs.readFileSync(NOTES_FILE, 'utf-8');

    console.log('🔍 解析知识点...');
    const sections = parseNotes(content);
    console.log(`   找到 ${sections.length} 个知识点`);

    console.log('📊 生成 Mermaid 图...');
    const mermaid = generateMermaid(sections);

    const output = `# 知识图谱

> 自动生成于 ${new Date().toLocaleString('zh-CN')}

${mermaid}

## 使用方法

1. 在 VS Code 中安装 "Markdown Preview Mermaid Support" 插件
2. 或者在 Obsidian 中直接预览
3. 或者粘贴到 [Mermaid Live Editor](https://mermaid.live)
`;

    fs.writeFileSync(OUTPUT_FILE, output);
    console.log(`✅ 已生成: ${OUTPUT_FILE}`);
}

main();
