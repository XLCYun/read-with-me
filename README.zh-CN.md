# Read With Me

[English](README.md)

AI 驱动的文档阅读伴侣 skill。逐章逐段阅读文档，支持翻译、讨论和自动笔记。

## 功能特性

- **多格式支持** -- PDF、Word、TXT、Markdown 及 arxiv 论文
- **交互式阅读** -- AI 逐段讲解，回答问题，深入讨论
- **翻译** -- 可选双语对照输出，支持任意目标语言
- **自动笔记** -- 讨论要点自动保存到笔记文件
- **进度追踪** -- 支持从上次阅读位置继续
- **arxiv 集成** -- 通过链接或裸 ID（如 `2301.00001`）下载论文

## 前置要求

- Python 3.10+
- 支持 skill 的 agent 框架（如 [Claude Code](https://docs.anthropic.com/en/docs/claude-code)、Copilot CLI、Gemini CLI 等）
- `markitdown` 包（用于 PDF/Word 转换）：
  ```bash
  pip install markitdown
  ```

## 安装

### 通过 `npx skills`（推荐）

```bash
npx skills add XLCYun/read-with-me
```

自动安装到你的 agent 框架的 skill 目录（Claude Code、Cursor、Codex 等）。详见 [skills.sh](https://skills.sh/)。

### 手动安装

克隆仓库并安装到你的 agent skill 目录：

```bash
git clone https://github.com/XLCYun/read-with-me.git
```

然后将 `skills/read-with-me` 复制或软链接到你的 agent 框架的 skill 目录。具体路径请参考对应框架的文档。

## 使用

通过文件路径或链接调用 skill：

```
/read-with-me path/to/document.pdf
/read-with-me path/to/document.md
/read-with-me https://arxiv.org/abs/2301.00001
/read-with-me 2301.00001
```

AI 将会：

1. 下载/转换文档为 Markdown
2. 解析文档结构并展示概览
3. 询问翻译偏好和起始位置
4. 逐段引导阅读并提供讲解
5. 自动保存讨论笔记

## 工作原理

### 输入类型

| 输入 | 处理方式 |
|------|----------|
| arxiv 链接或裸 ID | 下载 PDF，命名为 `{id}_{title}.pdf` |
| PDF 下载链接 | 下载文件 |
| 本地文件（PDF、Word 等） | 通过 MarkItDown 转换为 Markdown |
| 本地文件（TXT/Markdown） | 直接使用 |

### 阅读循环

每个段落 AI 会：

1. 展示段落内容
2. 如启用翻译则提供译文
3. 提供解读和上下文
4. 等待你的提问或输入"next"继续
5. 如有讨论则保存笔记

### 生成文件

| 文件 | 用途 |
|------|------|
| `{filename}.notes.md` | 自动保存的讨论笔记 |
| `{filename}.progress.json` | 阅读进度，用于断点续读 |

### 笔记格式

```markdown
## Chapter X, Paragraph Y

**Summary**: 段落内容简述

**Discussion Points**:
- 讨论要点 1
- 讨论要点 2

**Key Takeaway**: 核心洞察或结论
```

## 脚本

| 脚本 | 用途 |
|------|------|
| `scripts/download.py` | 从 URL 下载文件（支持 arxiv） |
| `scripts/convert.py` | 通过 MarkItDown 将文档转换为 Markdown |
| `scripts/parse_markdown.py` | 解析 Markdown 结构，提取章节/段落 |

### parse_markdown.py

```bash
# 文档概览
python scripts/parse_markdown.py document.md --overview

# 读取指定章节
python scripts/parse_markdown.py document.md --chapter 2

# 读取指定段落
python scripts/parse_markdown.py document.md --chapter 2 --paragraph 3

# 读取段落范围
python scripts/parse_markdown.py document.md --chapter 2 --paragraph 3-7

# JSON 输出
python scripts/parse_markdown.py document.md --overview --json
```

### download.py

```bash
# arxiv 论文
python scripts/download.py https://arxiv.org/abs/2301.00001

# 裸 arxiv ID
python scripts/download.py 2301.00001

# 通用 URL
python scripts/download.py https://example.com/paper.pdf

# 指定输出目录
python scripts/download.py 2301.00001 -o ./papers
```

### convert.py

```bash
# 将 PDF 转换为 Markdown
python scripts/convert.py paper.pdf

# 指定输出路径
python scripts/convert.py paper.pdf -o output.md
```

## 许可证

MIT -- 详见 [LICENSE](LICENSE)。

## 作者

XLCYun
