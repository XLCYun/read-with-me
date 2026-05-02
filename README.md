# Read With Me

[中文版](README.zh-CN.md)

An AI-powered document reading companion skill. Read documents chapter by chapter, paragraph by paragraph, with translation, discussion, and automatic note-taking.

## Features

- **Multi-format support** -- PDF, Word, TXT, Markdown, and arxiv papers
- **Interactive reading** -- AI explains each paragraph, answers questions, and discusses content
- **Translation** -- Optional bilingual output for any target language
- **Auto-notes** -- Discussion points are automatically saved to a notes file
- **Progress tracking** -- Resume reading from where you left off
- **arxiv integration** -- Download papers by URL or bare ID (e.g., `2301.00001`)

## Prerequisites

- Python 3.10+
- An agent harness that supports skills (e.g., [Claude Code](https://docs.anthropic.com/en/docs/claude-code), Copilot CLI, Gemini CLI, etc.)
- `markitdown` package (for PDF/Word conversion):
  ```bash
  pip install markitdown
  ```

## Installation

### Via `npx skills` (recommended)

```bash
npx skills add XLCYun/read-with-me
```

This will automatically install the skill into your agent framework's skills directory (Claude Code, Cursor, Codex, etc.). See [skills.sh](https://skills.sh/) for more details.

### Manual

Clone the repository and install it into your agent's skills directory:

```bash
git clone https://github.com/XLCYun/read-with-me.git
```

Then copy or symlink `skills/read-with-me` into your agent harness's skills directory. Refer to your agent framework's documentation for where skills are loaded from.

## Usage

Invoke the skill with a file path or URL:

```
/read-with-me path/to/document.pdf
/read-with-me path/to/document.md
/read-with-me https://arxiv.org/abs/2301.00001
/read-with-me 2301.00001
```

The AI will:

1. Download/convert the document to Markdown
2. Parse the structure and present an overview
3. Ask about translation preferences and starting point
4. Walk you through each paragraph with explanations
5. Save discussion notes automatically

## How It Works

### Input Types

| Input | Handling |
|-------|----------|
| arxiv URL or bare ID | Downloads PDF, names as `{id}_{title}.pdf` |
| PDF download URL | Downloads the file |
| Local file (PDF, Word, etc.) | Converts to Markdown via MarkItDown |
| Local file (TXT/Markdown) | Used directly |

### Reading Loop

For each paragraph the AI will:

1. Display the paragraph content
2. Translate if translation mode is enabled
3. Provide interpretation and context
4. Wait for your questions or a "next" command
5. Save notes if you discussed the paragraph

### Generated Files

| File | Purpose |
|------|---------|
| `{filename}.notes.md` | Auto-saved discussion notes |
| `{filename}.progress.json` | Reading progress for resume |

### Notes Format

```markdown
## Chapter X, Paragraph Y

**Summary**: Brief summary of paragraph content

**Discussion Points**:
- Key point 1 from discussion
- Key point 2 from discussion

**Key Takeaway**: Main insight or conclusion
```

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/download.py` | Download files from URLs (arxiv-aware) |
| `scripts/convert.py` | Convert documents to Markdown via MarkItDown |
| `scripts/parse_markdown.py` | Parse Markdown structure, extract chapters/paragraphs |

### parse_markdown.py

```bash
# Document overview
python scripts/parse_markdown.py document.md --overview

# Read specific chapter
python scripts/parse_markdown.py document.md --chapter 2

# Read specific paragraph
python scripts/parse_markdown.py document.md --chapter 2 --paragraph 3

# Read paragraph range
python scripts/parse_markdown.py document.md --chapter 2 --paragraph 3-7

# JSON output
python scripts/parse_markdown.py document.md --overview --json
```

### download.py

```bash
# arxiv paper
python scripts/download.py https://arxiv.org/abs/2301.00001

# Bare arxiv ID
python scripts/download.py 2301.00001

# Generic URL
python scripts/download.py https://example.com/paper.pdf

# Custom output directory
python scripts/download.py 2301.00001 -o ./papers
```

### convert.py

```bash
# Convert PDF to Markdown
python scripts/convert.py paper.pdf

# Custom output path
python scripts/convert.py paper.pdf -o output.md
```

## License

MIT -- see [LICENSE](LICENSE).

## Author

XLCYun
