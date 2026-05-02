#!/usr/bin/env python3
"""
Parse markdown document structure for read-with-me skill.

Usage:
    python parse_markdown.py <file> --overview          # Show document structure
    python parse_markdown.py <file> --chapter N          # Show all paragraphs in chapter N
    python parse_markdown.py <file> --chapter N --paragraph M  # Show specific paragraph
    python parse_markdown.py <file> --chapter N --paragraph M --range R  # Show M to M+R paragraphs
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional


def parse_markdown(content: str) -> list[dict]:
    """
    Parse markdown into chapters and paragraphs.

    Returns list of chapters, each containing:
    - title: chapter title
    - level: heading level (1-6)
    - paragraphs: list of paragraph texts
    """
    lines = content.split('\n')
    chapters = []
    current_chapter = None
    current_paragraph_lines = []

    # Regex for markdown headings
    heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$')

    def flush_paragraph():
        """Save current paragraph if it has content."""
        nonlocal current_paragraph_lines
        if current_paragraph_lines:
            text = '\n'.join(current_paragraph_lines).strip()
            if text and current_chapter is not None:
                current_chapter['paragraphs'].append(text)
            current_paragraph_lines = []

    def start_new_chapter(title: str, level: int):
        """Start a new chapter."""
        nonlocal current_chapter
        flush_paragraph()
        current_chapter = {
            'title': title,
            'level': level,
            'paragraphs': []
        }
        chapters.append(current_chapter)

    for line in lines:
        heading_match = heading_pattern.match(line)

        if heading_match:
            # This is a heading - start new chapter
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            start_new_chapter(title, level)
        elif line.strip() == '':
            # Empty line - paragraph separator
            flush_paragraph()
        else:
            # Content line
            if current_chapter is None:
                # Content before any heading - create default chapter
                start_new_chapter("Introduction", 0)
            current_paragraph_lines.append(line)

    # Flush last paragraph
    flush_paragraph()

    return chapters


def show_overview(chapters: list[dict]) -> None:
    """Display document structure overview."""
    total_paragraphs = sum(len(ch['paragraphs']) for ch in chapters)

    print("=" * 60)
    print("DOCUMENT OVERVIEW")
    print("=" * 60)
    print(f"\nTotal chapters: {len(chapters)}")
    print(f"Total paragraphs: {total_paragraphs}")
    print("\n" + "-" * 60)
    print("CHAPTER STRUCTURE:")
    print("-" * 60)

    for i, chapter in enumerate(chapters, 1):
        indent = "  " * (chapter['level'] - 1) if chapter['level'] > 0 else ""
        para_count = len(chapter['paragraphs'])
        status = f"({para_count} paragraphs)" if para_count > 0 else "(no content)"
        print(f"{indent}[{i}] {chapter['title']} {status}")

    print("-" * 60)
    print("\nTip: Use --chapter N --paragraph M to read specific content.")
    print("     Chapters with '(no content)' are section headers only.")


def show_chapter(chapters: list[dict], chapter_num: int) -> None:
    """Display all paragraphs in a chapter."""
    if chapter_num < 1 or chapter_num > len(chapters):
        print(f"Error: Chapter {chapter_num} not found. Document has {len(chapters)} chapters.")
        sys.exit(1)

    chapter = chapters[chapter_num - 1]
    print(f"Chapter {chapter_num}: {chapter['title']}")
    print(f"Paragraphs: {len(chapter['paragraphs'])}")
    print("=" * 60)

    for i, para in enumerate(chapter['paragraphs'], 1):
        print(f"\n--- Paragraph {i} ---")
        print(para)

    print("\n" + "=" * 60)


def show_paragraph(chapters: list[dict], chapter_num: int, paragraph_num: int, range_count: int = 1) -> None:
    """Display specific paragraph(s)."""
    if chapter_num < 1 or chapter_num > len(chapters):
        print(f"Error: Chapter {chapter_num} not found. Document has {len(chapters)} chapters.")
        sys.exit(1)

    chapter = chapters[chapter_num - 1]

    if len(chapter['paragraphs']) == 0:
        print(f"Error: Chapter {chapter_num} '{chapter['title']}' has no content (section header only).")
        print("Use --overview to see which chapters have content.")
        sys.exit(1)

    if paragraph_num < 1 or paragraph_num > len(chapter['paragraphs']):
        print(f"Error: Paragraph {paragraph_num} not found in chapter {chapter_num}. Chapter has {len(chapter['paragraphs'])} paragraphs.")
        sys.exit(1)

    # Show requested range of paragraphs
    for i in range(paragraph_num, min(paragraph_num + range_count, len(chapter['paragraphs']) + 1)):
        para = chapter['paragraphs'][i - 1]
        print(f"Chapter {chapter_num}, Paragraph {i}:")
        print("-" * 40)
        print(para)
        print("-" * 40)
        if i < paragraph_num + range_count - 1 and i < len(chapter['paragraphs']):
            print()


def main():
    # Fix Windows console encoding for Unicode output
    sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description='Parse markdown document structure')
    parser.add_argument('file', help='Path to markdown file')
    parser.add_argument('--overview', action='store_true', help='Show document structure overview')
    parser.add_argument('--chapter', type=int, help='Chapter number to display')
    parser.add_argument('--paragraph', type=int, help='Paragraph number to display')
    parser.add_argument('--range', type=int, default=1, help='Number of paragraphs to show (default: 1)')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    # Read file
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File not found: {args.file}")
        sys.exit(1)

    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

    # Parse markdown
    chapters = parse_markdown(content)

    if not chapters:
        print("Warning: No content found in document.")
        sys.exit(0)

    # JSON output mode
    if args.json:
        result = {
            'file': str(file_path),
            'chapters': []
        }
        for i, ch in enumerate(chapters, 1):
            result['chapters'].append({
                'number': i,
                'title': ch['title'],
                'level': ch['level'],
                'paragraph_count': len(ch['paragraphs'])
            })
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    # Determine action
    if args.overview:
        show_overview(chapters)
    elif args.chapter and args.paragraph:
        show_paragraph(chapters, args.chapter, args.paragraph, args.range)
    elif args.chapter:
        show_chapter(chapters, args.chapter)
    else:
        # Default: show overview
        show_overview(chapters)


if __name__ == '__main__':
    main()
