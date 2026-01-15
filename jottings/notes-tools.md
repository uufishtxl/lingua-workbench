# 工具笔记 (Tools Notes)

## Mermaid CLI

官方命令行工具，将 Mermaid 图表转换为 PNG/SVG/PDF。

### 安装

```bash
npm install -g @mermaid-js/mermaid-cli
```

### 基本用法

```bash
# Mermaid 文件 → PNG
mmdc -i input.mmd -o output.png

# 带白色背景
mmdc -i input.mmd -o output.png -b white

# 转 SVG（矢量图，可缩放）
mmdc -i input.mmd -o output.svg

# 转 PDF
mmdc -i input.mmd -o output.pdf
```

### 常用参数

| 参数 | 说明 |
|------|------|
| `-i` | 输入文件（`.mmd` 或 `.md`） |
| `-o` | 输出文件（根据扩展名决定格式） |
| `-b` | 背景色（`white`, `transparent`, `#hex`） |
| `-t` | 主题（`default`, `forest`, `dark`, `neutral`） |
| `-w` | 输出宽度（像素） |
| `-H` | 输出高度（像素） |

### 项目中使用示例

```powershell
# 生成 DITA 文档用的数据流图
mmdc -i "docs\dita\topics\developer\wavesurfer\images\dataflow_audioslicer.mmd" -o "docs\dita\topics\developer\wavesurfer\images\dataflow_audioslicer.png" -b white
```

### 为什么用 CLI 而不是 mermaid.live？

- ✅ **免费** - mermaid.live 导出需要付费
- ✅ **批量处理** - 可脚本化
- ✅ **本地执行** - 不依赖网络
- ✅ **CI/CD 集成** - 可在构建流程中自动生成

### 技术原理

底层使用 Puppeteer（无头 Chrome）渲染图表，质量与网页版完全一致。

---

*最后更新: 2026-01-15*
