# DITA 笔记

## keyref

### 定义位置：keys.ditamap

keyref 的 key 定义在一个独立的 `.ditamap` 文件中，通常命名为 `keys.ditamap`。

**基本结构：**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE map PUBLIC "-//OASIS//DTD DITA Map//EN" "map.dtd">
<map id="keys">
  <title>Keys Definition</title>
  
  <keydef keys="author_name">
    <topicmeta>
      <keywords><keyword>Edith Tang</keyword></keywords>
    </topicmeta>
  </keydef>
  
  <keydef keys="product_version">
    <topicmeta>
      <keywords><keyword>1.0</keyword></keywords>
    </topicmeta>
  </keydef>
  
</map>
```

**在 bookmap 中引入：**

```xml
<frontmatter>
  <!-- processing-role="resource-only" 表示仅用于资源引用，不出现在输出中 -->
  <mapref href="keys.ditamap" processing-role="resource-only"/>
  ...
</frontmatter>
```

### 引用方式

在 topic 或 map 中使用 `<keyword keyref="key_name"/>` 引用：

```xml
<!-- 在 author 元素中 -->
<author><keyword keyref="author_name"/></author>

<!-- 在段落中 -->
<p>当前版本：<keyword keyref="product_version"/></p>
```

### 缺省值

如果 keyref 没有找到对应的 key，可以使用缺省值。

```XML
<author keyref="authr_name">Edith Tang (Fallback)</author>
```

### keyref vs conref 对比

| 特性 | keyref | conref |
|------|--------|--------|
| **定义位置** | `keys.ditamap` (map 文件) | `warehouse.dita` (topic 文件) |
| **定义方式** | `<keydef keys="...">` | 元素 + `id` 属性 |
| **引用语法** | `<keyword keyref="key_name"/>` | `<ph conref="path#topic/id"/>` |
| **复用内容** | 纯文本值 | 完整元素（含子元素和结构） |
| **适用场景** | 变量替换（版本号、作者名等） | 复用段落、注释、表格等结构化内容 |
| **路径依赖** | 无需路径，全局可用 | 需要相对路径引用源文件 |

**示例对比：**

```xml
<!-- keyref: 只能引用纯文本值 -->
<p>作者：<keyword keyref="author_name"/></p>

<!-- conref: 可以引用整个结构化片段 -->
<note conref="warehouse.dita#warehouse/note_api_required"/>
```

**选择建议：**
- 简单文本变量 → 用 **keyref**
- 复杂结构片段 → 用 **conref**


## Audience 条件处理

### 定义 audience 属性

在需要条件过滤的元素上添加 `audience` 属性：

```xml
<!-- 标记为开发者内容 -->
<step audience="developer">
  <cmd>Set up the backend:</cmd>
  ...
</step>

<!-- 标记为用户内容 -->
<p audience="user">Click the Play button to start.</p>

<!-- 混合受众 -->
<note audience="developer user">This applies to both audiences.</note>
```

### 创建 DITAVAL 过滤文件

**user-only.ditaval** - 排除开发者内容：
```xml
<val>
  <prop action="exclude" att="audience" val="developer"/>
  <prop action="include" att="audience" val="user"/>
</val>
```

**full.ditaval** - 包含所有内容：
```xml
<val>
  <prop action="include" att="audience" val="developer"/>
  <prop action="include" att="audience" val="user"/>
</val>
```

### 在 Oxygen 中使用

1. 打开 **Transformation Scenarios**
2. 选择或复制一个场景（如 PDF/WebHelp）
3. 在 **Filters** 选项卡中选择相应的 `.ditaval` 文件
4. 运行转换

### 命令行使用（DITA-OT）

```bash
# 生成用户文档
dita -i bookmap.ditamap -f html5 --filter=user-only.ditaval

# 生成完整文档
dita -i bookmap.ditamap -f html5 --filter=full.ditaval
```


## 一些文件类型

### Preface

* 在 `ditamap` 中使用 `<preface href="topics/frontmatter/preface.dita"/>` 引入。
* `preface`中的`section`元素在全书目录层级中重要性较低。因为在图书或手册结构中，一般前言/序言被视为一个独立的、介绍性的整体单元。

**注意**：`notices` 一样使用专门的标签，并且`section`元素在全书目录层级中重要性较低。

### `<booklists>` 的默认隐藏

现象：<booklists> 容器内的 <toc>（目录）、<figurelist>（图目录）、<tablelist>（表目录）等元素，它们自身不会作为条目出现在它们所生成的那个主目录中。这是符合逻辑的——目录里不会有一条叫“目录”的条目。

需求：如果你希望这些列表的标题（如“图表目录”）也作为一个章节出现在 PDF 的书签导航或页码目录中，就需要进行自定义。

### `<abstract>` 和 `<shortdesc>` 的处理

这些摘要性内容通常被视为主题元数据的一部分，而非正式章节内容，因此默认也不会生成独立的目录项。

### `<notices>` 的特殊性

包含版权、商标声明等法律文本的 <notices>，其位置和样式通常有固定要求，一般也无需进入主目录。

## 控制哪些内容进入 PDF TOC

* 语义化精准控制：基于属性 (outputclass)
* 呈现层同一控制：自定义 XSLT / CSS

最推荐的是基于 `outputclass` 属性控制：

```XML
<bookmap>
  <frontmatter>
    <booklists outputclass="toc"> 
      <!-- 现在，整个booklists区域可被自定义规则处理 -->
    </booklists>
    <preface outputclass="toc">
      <topicref href="preface.dita"/>
    </preface>
  </frontmatter>
  <chapter href="chapter1.dita"/>
</bookmap>
```

然后，你需要通过以下任一方式实现规则：

- 自定义 XSLT（适用于 DITA-OT 的旧版 PDF 引擎）：创建一个插件，覆盖负责生成目录的 XSLT 文件，识别 @outputclass='toc' 的元素并为其生成 TOC 条目。

- 自定义 CSS（适用于 PDF2 基于 CSS 的引擎）：在自定义 CSS 中为特定类添加 display: block 和 bookmark-level 属性。

- 商用工具配置（如 Oxygen XML Editor）：在“转换场景”的设置界面中，通常有更直观的选项或钩子来配置目录深度，可能无需直接写代码。


### Part 的组织

* `<part>` 作为容器，所有放在它里面的 `<chapter>` 都会作为同级条目出现在 TOC 中。
* DITA-OT 引擎非常智能，当它看到 `<part>`标签时，它会做两件事情：
  1. 自动插入分页：通常会插入一个显眼的“隔页”，这张纸上通常只有大大的标题。
     ![part_page](dita/dita_part_seperator_page.png)
  2. 自动编号：会自动给标题加上前缀。比如你写的是 `Getting Started`，生成的 PDF 上会显示 `Part I. Getting Started`。
```XML
  <part navtitle="Getting Started">
  ```

这里用 `navtitle`是因为不需要正文内容。如果需要，可以创建一个 `concept` 文件，然后用 `href` 引入。

## 其他一些 Tags

### 菜单项组织

```XML
<menucascade><uicontrol>Audio Slicer</uicontrol><uicontrol>Load Source</uicontrol></menucascade>
```

当菜单项单独出现时，也会使用 `<uicontrol>`，而不是 `<b>`，这就体现了 DITA 的设计哲学：这是一门为机器设计的写作标准语言，而不是为视觉设计的。它在告诉机器“这是一个界面上的控件”。作用是：

* **机器翻译**：当翻译工具看到它时，就会去查软件的词汇表 (Glossary)，确保翻译得和软件界面一样
* **自动化索引**：可以配置生成脚本，自动抓取所有的 `<uicontrol>`，生成一个“界面元素索引表”。

### Note 类型

```xml
<info><note type="restriction">Creating new Dramas is currently not available to users.</note></info>
```

**常用 note 类型对照表：**

| type | 用途 | 图标样式 |
|------|------|----------|
| `note` (默认) | 一般性说明 | ℹ️ 信息 |
| `tip` | 使用技巧 | 💡 灯泡 |
| `important` | 重要信息 | ⚠️ 警告 |
| `warning` | 警告（可能导致问题） | ⚠️ 橙色警告 |
| `caution` | 注意（可能导致数据丢失） | 🔶 注意 |
| `danger` | 危险（可能导致人身伤害） | 🔴 危险 |
| `restriction` | 功能限制 | 🚫 禁止 |
| `trouble` | 故障排除提示 | 🔧 工具 |
| `remember` | 需要记住的要点 | 📌 图钉 |
| `attention` | 需要注意的事项 | ⚡ 注意 |
| `fastpath` | 快捷方式 | ⏩ 快进 |
| `other` | 自定义（需配合 `othertype` 属性） | 自定义 |

**示例：**
```xml
<note type="tip">Press Ctrl+S to save quickly.</note>
<note type="warning">This action cannot be undone.</note>
<note type="restriction">Admin access required.</note>
```

### 更多 UI 元素

| 元素 | 用途 | 示例 |
|------|------|------|
| `<uicontrol>` | 界面控件（按钮、菜单项） | `<uicontrol>Save</uicontrol>` |
| `<menucascade>` | 多级菜单路径 | `<menucascade><uicontrol>File</uicontrol><uicontrol>Save</uicontrol></menucascade>` |
| `<wintitle>` | 窗口/对话框标题 | `<wintitle>Settings</wintitle>` |
| `<filepath>` | 文件路径 | `<filepath>/usr/local/bin</filepath>` |
| `<codeph>` | 行内代码 | `<codeph>npm install</codeph>` |
| `<codeblock>` | 代码块 | 多行代码 |
| `<varname>` | 变量名 | `<varname>$HOME</varname>` |
| `<userinput>` | 用户输入 | `<userinput>yes</userinput>` |
| `<systemoutput>` | 系统输出 | `<systemoutput>Done.</systemoutput>` |
