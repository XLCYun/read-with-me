#!/usr/bin/env python3
"""
Parse markdown document structure for read-with-me skill.

Usage:
    python parse_markdown.py <file> --overview                    # Show document structure
    python parse_markdown.py <file> --chapter N                   # Show all paragraphs in chapter N
    python parse_markdown.py <file> --chapter N --paragraph M     # Show specific paragraph
    python parse_markdown.py <file> --chapter N --paragraph M-R   # Show paragraphs M to R
    python parse_markdown.py <file> --chapter N --paragraph M,N,P # Show specific paragraphs
    python parse_markdown.py <file> --chapter N --paragraph all   # Show all paragraphs
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


def parse_paragraph_spec(spec: str, max_paragraph: int) -> list[int]:
    """
    Parse paragraph specification into list of paragraph numbers.

    Supports:
    - "3" -> [3]
    - "2-5" -> [2, 3, 4, 5]
    - "1,3,5" -> [1, 3, 5]
    - "all" -> [1, 2, ..., max_paragraph]
    """
    spec = spec.strip().lower()

    if spec == 'all':
        return list(range(1, max_paragraph + 1))

    if '-' in spec:
        parts = spec.split('-', 1)
        try:
            start = int(parts[0])
            end = int(parts[1])
            if start < 1 or end > max_paragraph or start > end:
                print(f"Error: Invalid range {spec}. Must be between 1 and {max_paragraph}.")
                sys.exit(1)
            return list(range(start, end + 1))
        except ValueError:
            print(f"Error: Invalid range format '{spec}'. Use N-M (e.g., 2-5).")
            sys.exit(1)

    if ',' in spec:
        try:
            nums = [int(x.strip()) for x in spec.split(',')]
            for n in nums:
                if n < 1 or n > max_paragraph:
                    print(f"Error: Paragraph {n} not found. Must be between 1 and {max_paragraph}.")
                    sys.exit(1)
            return nums
        except ValueError:
            print(f"Error: Invalid format '{spec}'. Use N,M,P (e.g., 1,3,5).")
            sys.exit(1)

    try:
        num = int(spec)
        if num < 1 or num > max_paragraph:
            print(f"Error: Paragraph {num} not found. Must be between 1 and {max_paragraph}.")
            sys.exit(1)
        return [num]
    except ValueError:
        print(f"Error: Invalid paragraph specification '{spec}'.")
        sys.exit(1)


def show_paragraphs(chapters: list[dict], chapter_num: int, paragraph_spec: str) -> None:
    """Display specific paragraph(s) based on specification."""
    if chapter_num < 1 or chapter_num > len(chapters):
        print(f"Error: Chapter {chapter_num} not found. Document has {len(chapters)} chapters.")
        sys.exit(1)

    chapter = chapters[chapter_num - 1]

    if len(chapter['paragraphs']) == 0:
        print(f"Error: Chapter {chapter_num} '{chapter['title']}' has no content (section header only).")
        print("Use --overview to see which chapters have content.")
        sys.exit(1)

    paragraph_nums = parse_paragraph_spec(paragraph_spec, len(chapter['paragraphs']))

    # Show requested paragraphs
    for i, para_num in enumerate(paragraph_nums):
        para = chapter['paragraphs'][para_num - 1]
        print(f"Chapter {chapter_num}, Paragraph {para_num}:")
        print("-" * 40)
        print(para)
        print("-" * 40)
        if i < len(paragraph_nums) - 1:
            print()


def main():
    # Fix Windows console encoding for Unicode output
    sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description='Parse markdown document structure')
    parser.add_argument('file', help='Path to markdown file')
    parser.add_argument('--overview', action='store_true', help='Show document structure overview')
    parser.add_argument('--chapter', type=int, help='Chapter number to display')
    parser.add_argument('--paragraph', type=str, help='Paragraph(s) to display: N, N-M, N,M,P, or "all"')
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
        show_paragraphs(chapters, args.chapter, args.paragraph)
    elif args.chapter:
        show_chapter(chapters, args.chapter)
    else:
        # Default: show overview
        show_overview(chapters)


if __name__ == '__main__':
    main()
