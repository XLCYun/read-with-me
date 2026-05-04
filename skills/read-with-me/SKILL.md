---
name: read-with-me
description: Read documents together with AI - supports PDF, Word, TXT, Markdown, arxiv links. Interactive chapter-by-chapter reading with translation, discussion, and auto-notes.
argument-hint: <file-path-or-url>
allowed-tools: Bash(*), Read, Grep, Glob, Write, Edit, WebFetch, mcp__dashscope-webparser__bailian_web_parser
---

# Read With Me

Interactive document reading companion. Read documents chapter by chapter, paragraph by paragraph, with AI-powered translation, discussion, and automatic note-taking.

## Context: $ARGUMENTS

## Supported Input Types

| Input Type | Handling |
|-----------|----------|
| arxiv link (e.g., `https://arxiv.org/abs/2301.00001`) | Auto-download PDF, name as `{arxiv_id}_{sanitized_title}.pdf` |
| arxiv ID (e.g., `2301.00001` or `2301.00001v1`) | Same as above — treated as arxiv shorthand |
| PDF download URL | Auto-download |
| Local file path (PDF, Word, etc.) | Auto-convert via `convert.py` using MarkItDown |
| Local file path (TXT/Markdown) | Direct read |

## Prerequisites

### Python

Python 3.10+ is required. Run the detector at session start:

```bash
bash scripts/detect_python.sh
```

It outputs `python`, `python3`, or `uv run python`. Use that command for all subsequent script calls.

### MarkItDown

The `markitdown` Python package is required for converting PDF, Word, and other document formats to markdown. If not installed, the conversion script will report an error — install it with:

```bash
pip install markitdown
```

## Workflow

### Step 1: Prepare Document

1. Parse the input argument to determine type:
   - If it's an arxiv URL → download PDF using `scripts/download.py`
   - If it's a regular URL → download using `scripts/download.py`
   - If it's a local file → verify it exists

2. Convert to Markdown if needed:
   - PDF/Word/其他格式 → python scripts/convert.py <file> [-o output.md]
   - TXT/Markdown → use directly (convert.py auto-passes through these)

3. Save the markdown file alongside the original (or in current directory for downloads)

### Step 2: Parse Document Structure

Run the parser to get document overview:

```bash
python scripts/parse_markdown.py <markdown-file> --overview
# JSON output: --json
```

This returns a hierarchical structure:
- **Chapters** (`#` headings)
- **Sections** (`##` headings within each chapter)
- **Paragraphs** within each section

Fallback: if no `#` headings exist, `##` becomes chapters and `###` becomes sections.

Present this overview to the user.

### Step 3: Ask for Preferences

**Config loading logic** (check in this order):

1. **Resume with existing config** — If user chose to resume AND `progress.json` has a `"config"` key → load config silently, skip asking.
2. **Resume without config (backward compat)** — If user chose to resume BUT `progress.json` has no `"config"` key → ask preferences, then save config into the existing file.
3. **Start fresh (reset position)** — If user chose to start from beginning AND `progress.json` has a `"config"` key → keep saved config, skip asking. Only reset chapter/section/paragraph.
4. **No progress file** — Ask preferences normally.

When asking preferences:

1. **Translation mode**: Ask if user wants translation enabled, and to which language.
   - If yes, output both original and translation for each paragraph

2. **Reading unit**: Ask if user wants to read by paragraph or by section.
   - `"paragraph"`: read one paragraph at a time, with section header as context
   - `"section"`: read all paragraphs in a section at once

3. **Starting point**: Ask which chapter/section/paragraph to start from (default: beginning)

**Save config immediately** after collecting preferences — update `{filename}.progress.json` with the `"config"` key right away, before any reading begins.

### Step 4: Reading Loop

The reading loop branches based on `config.reading_unit`:

#### Paragraph mode (`reading_unit: "paragraph"`)

For each paragraph:

1. **Fetch the paragraph**:
   ```bash
   python scripts/parse_markdown.py <markdown-file> --chapter <N> --section <M> --paragraph <P>
   # Range: --paragraph 2-5
   # Multiple: --paragraph 1,3,5
   # All: --paragraph all
   ```

2. **Output the paragraph** to the user (with section title as context header)

3. **If translation enabled**: Provide target language translation alongside the original

4. **Provide interpretation**:
   - What this paragraph means
   - Its role in the section/chapter/document structure

5. **Wait for user response**:
   - User may ask questions or discuss
   - Continue discussion until user says "next" / "n" / "continue" / "下一段"

6. **Auto-save notes**: When user moves to next paragraph:
   - **Only write notes if the user asked questions or discussed the chapter or paragraphs.** No discussion = user has no doubts = skip notes.
   - Summarize the discussion and key points from this paragraph
   - If there's content worth noting from discussion, append to `{filename}.notes.md`
   - If user did not engage (no questions, no discussion), do NOT write notes for this paragraph/chapter

7. **Save progress**: Update `{filename}.progress.json`:
   ```json
   {
     "chapter": 3,
     "section": 1,
     "paragraph": 5,
     "last_read": "2026-05-02T10:30:00",
     "config": {
       "translation_enabled": true,
       "target_language": "中文",
       "reading_unit": "paragraph"
     }
   }
   ```

#### Section mode (`reading_unit: "section"`)

For each section:

1. **Fetch the section**:
   ```bash
   python scripts/parse_markdown.py <markdown-file> --chapter <N> --section <M>
   ```

2. **Output all paragraphs** in the section under the section heading

3. **If translation enabled**: Provide target language translation for the section

4. **Provide interpretation**:
   - What this section covers
   - Its role in the chapter/document structure

5. **Wait for user response**:
   - User may ask questions or discuss
   - Continue discussion until user says "next" / "n" / "continue" / "下一段"

6. **Auto-save notes**: Same rules as paragraph mode — only write if user engaged in discussion.

7. **Save progress**: Update `{filename}.progress.json` with `paragraph` set to the last paragraph number in the section:
   ```json
   {
     "chapter": 3,
     "section": 1,
     "paragraph": 8,
     "last_read": "2026-05-02T10:30:00",
     "config": {
       "translation_enabled": true,
       "target_language": "中文",
       "reading_unit": "section"
     }
   }
   ```

#### Mid-session config changes

If user says something like "关掉翻译", "换成日语", "开启翻译", "逐段阅读", "按节阅读" during reading — update config in memory AND immediately persist to `progress.json`. No special syntax needed, interpret natural language intent.

### Step 5: Section and Chapter Transitions

When all paragraphs in a section are done (paragraph mode):
- Show "Section complete" notice
- Move to next section

When all sections in a chapter are done:
- Ask if user wants a chapter summary
- If yes, provide summary of key points from the chapter
- Move to next chapter

### Step 6: Document Completion

When all chapters are done:
- Offer a full document summary
- Show where notes are saved

## File Naming Conventions

For arxiv downloads:
- PDF: `{arxiv_id}_{sanitized_title}.pdf`
- Sanitize title: replace `/\:*?"<>|` with `_`, limit to 100 chars

For all documents:
- Notes: `{filename}.notes.md`
- Progress: `{filename}.progress.json`

## Notes Format

Notes are appended to `{filename}.notes.md` in this format:

```markdown
## Chapter X, Section Y: Section Title, Paragraph Z

**Summary**: [Brief summary of paragraph/section content]

**Discussion Points**:
- [Key point 1 from discussion]
- [Key point 2 from discussion]

**Key Takeaway**: [Main insight or conclusion]
```

## Resume Reading

If `{filename}.progress.json` exists when starting:
- Ask user if they want to resume from where they left off
- If yes, jump to the saved chapter/section/paragraph and load config silently (translation mode, target language, reading unit)
- If no, start from beginning but keep the saved config (only reset chapter/section/paragraph position)
- If the file has no `"config"` key (old format), ask preferences and save config into the existing file
- If the file has no `"section"` key (old format), treat as section 1

## Rules

- **Always output the full original text verbatim for each paragraph.** This is a reading session, not a summary session. The user reads the source material — you provide translation, interpretation, and discussion on top of it. Never replace the original with a paraphrase or summary unless user says otherwise.
- Always wait for user to say "next" before moving to next paragraph
- Keep discussion focused but allow tangents if user is interested
- Notes should be concise, not verbatim transcription
- Translation should be natural, not word-for-word
- If user asks about content from earlier paragraphs, reference the notes file
