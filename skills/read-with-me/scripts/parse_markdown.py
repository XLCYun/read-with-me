#!/usr/bin/env python3
"""
Parse markdown document structure for read-with-me skill.

Usage:
    python parse_markdown.py <file> --overview                              # Show document structure
    python parse_markdown.py <file> --chapter N                             # Show all sections in chapter N
    python parse_markdown.py <file> --chapter N --section M                 # Show all paragraphs in section M
    python parse_markdown.py <file> --chapter N --section M --paragraph P   # Show specific paragraph
    python parse_markdown.py <file> --chapter N --section M --paragraph P-R # Show paragraphs P to R
    python parse_markdown.py <file> --chapter N --section M --paragraph all # Show all paragraphs
"""

import argparse
import json
import re
import sys
from pathlib import Path


def parse_markdown(content: str) -> list[dict]:
    """
    Parse markdown into a hierarchical structure.

    Returns list of chapters, each containing:
    - title: chapter title
    - level: heading level (1)
    - sections: list of sections, each containing:
        - title: section title
        - level: heading level (2)
        - paragraphs: list of paragraph texts

    Fallback: if no # headings exist, treat ## as chapters and ### as sections.
    """
    lines = content.split('\n')
    heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$')

    # First pass: detect if document has any # (level 1) headings
    has_h1 = any(heading_pattern.match(line) and len(heading_pattern.match(line).group(1)) == 1 for line in lines)

    # Determine chapter/section levels based on document structure
    if has_h1:
        chapter_level = 1
        section_level = 2
    else:
        chapter_level = 2
        section_level = 3

    chapters: list[dict] = []
    current_chapter = None
    current_section = None
    current_paragraph_lines: list[str] = []

    def flush_paragraph():
        nonlocal current_paragraph_lines
        if current_paragraph_lines:
            text = '\n'.join(current_paragraph_lines).strip()
            if text and current_section is not None:
                current_section['paragraphs'].append(text)
            current_paragraph_lines = []

    def ensure_section():
        """Ensure current chapter has a section. Create Section 0 if needed."""
        nonlocal current_section
        if current_chapter is None:
            return
        if current_section is None:
            current_section = {
                'title': 'Section 0',
                'level': section_level,
                'paragraphs': []
            }
            current_chapter['sections'].append(current_section)

    def start_new_chapter(title: str, level: int):
        nonlocal current_chapter, current_section
        flush_paragraph()
        current_chapter = {
            'title': title,
            'level': level,
            'sections': []
        }
        chapters.append(current_chapter)
        current_section = None

    def start_new_section(title: str, level: int):
        nonlocal current_section
        flush_paragraph()
        if current_chapter is None:
            start_new_chapter("Introduction", chapter_level)
        current_section = {
            'title': title,
            'level': level,
            'paragraphs': []
        }
        current_chapter['sections'].append(current_section)

    for line in lines:
        heading_match = heading_pattern.match(line)

        if heading_match:
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()

            if level == chapter_level:
                start_new_chapter(title, level)
            elif level == section_level:
                start_new_section(title, level)
            else:
                # Deeper headings (###, ####, etc.) treated as paragraph content
                ensure_section()
                current_paragraph_lines.append(line)
        elif line.strip() == '':
            flush_paragraph()
        else:
            ensure_section()
            current_paragraph_lines.append(line)

    flush_paragraph()

    # If document has content but no chapters were created, wrap everything
    if not chapters and any(s['paragraphs'] for ch in chapters for s in ch['sections']):
        pass  # Shouldn't happen due to ensure_section logic, but just in case

    return chapters


def count_totals(chapters: list[dict]) -> tuple[int, int, int]:
    """Count total sections and paragraphs across all chapters."""
    total_sections = 0
    total_paragraphs = 0
    for ch in chapters:
        total_sections += len(ch['sections'])
        for sec in ch['sections']:
            total_paragraphs += len(sec['paragraphs'])
    return len(chapters), total_sections, total_paragraphs


def show_overview(chapters: list[dict]) -> None:
    """Display document structure overview as an indented tree."""
    n_chapters, n_sections, n_paragraphs = count_totals(chapters)

    print("=" * 60)
    print("DOCUMENT OVERVIEW")
    print("=" * 60)
    print(f"\nTotal chapters: {n_chapters}")
    print(f"Total sections: {n_sections}")
    print(f"Total paragraphs: {n_paragraphs}")

    print("\n" + "-" * 60)
    print("CHAPTER STRUCTURE:")
    print("-" * 60)

    for i, chapter in enumerate(chapters, 1):
        sec_count = len(chapter['sections'])
        para_count = sum(len(s['paragraphs']) for s in chapter['sections'])
        print(f"[{i}] {chapter['title']} ({sec_count} sections, {para_count} paragraphs)")

        for j, section in enumerate(chapter['sections']):
            s_para_count = len(section['paragraphs'])
            label = f"[{j}]" if section['title'] == 'Section 0' else f"[{j}]"
            status = f"({s_para_count} paragraphs)" if s_para_count > 0 else "(empty)"
            print(f"    {label} {section['title']} {status}")

    print("-" * 60)
    print("\nTip: Use --chapter N --section M --paragraph P to read specific content.")
    print("     Sections with '(empty)' are heading-only with no content.")


def show_chapter(chapters: list[dict], chapter_num: int) -> None:
    """Display all sections in a chapter."""
    if chapter_num < 1 or chapter_num > len(chapters):
        print(f"Error: Chapter {chapter_num} not found. Document has {len(chapters)} chapters.")
        sys.exit(1)

    chapter = chapters[chapter_num - 1]
    total_paras = sum(len(s['paragraphs']) for s in chapter['sections'])
    print(f"Chapter {chapter_num}: {chapter['title']}")
    print(f"Sections: {len(chapter['sections'])}, Paragraphs: {total_paras}")
    print("=" * 60)

    for j, section in enumerate(chapter['sections']):
        print(f"\n--- Section {j}: {section['title']} ({len(section['paragraphs'])} paragraphs) ---")
        for k, para in enumerate(section['paragraphs'], 1):
            print(f"\n  [Paragraph {k}]")
            print(f"  {para}")

    print("\n" + "=" * 60)


def show_section(chapters: list[dict], chapter_num: int, section_num: int) -> None:
    """Display all paragraphs in a section."""
    if chapter_num < 1 or chapter_num > len(chapters):
        print(f"Error: Chapter {chapter_num} not found. Document has {len(chapters)} chapters.")
        sys.exit(1)

    chapter = chapters[chapter_num - 1]

    if section_num < 0 or section_num >= len(chapter['sections']):
        print(f"Error: Section {section_num} not found in Chapter {chapter_num}. "
              f"It has {len(chapter['sections'])} sections (0-{len(chapter['sections'])-1}).")
        sys.exit(1)

    section = chapter['sections'][section_num]

    if len(section['paragraphs']) == 0:
        print(f"Chapter {chapter_num}, Section {section_num}: {section['title']}")
        print("(empty section - no content)")
        return

    print(f"Chapter {chapter_num}, Section {section_num}: {section['title']}")
    print(f"Paragraphs: {len(section['paragraphs'])}")
    print("=" * 60)

    for i, para in enumerate(section['paragraphs'], 1):
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


def show_paragraphs(chapters: list[dict], chapter_num: int, section_num: int, paragraph_spec: str) -> None:
    """Display specific paragraph(s) from a section."""
    if chapter_num < 1 or chapter_num > len(chapters):
        print(f"Error: Chapter {chapter_num} not found. Document has {len(chapters)} chapters.")
        sys.exit(1)

    chapter = chapters[chapter_num - 1]

    if section_num < 0 or section_num >= len(chapter['sections']):
        print(f"Error: Section {section_num} not found in Chapter {chapter_num}. "
              f"It has {len(chapter['sections'])} sections (0-{len(chapter['sections'])-1}).")
        sys.exit(1)

    section = chapter['sections'][section_num]

    if len(section['paragraphs']) == 0:
        print(f"Error: Section {section_num} '{section['title']}' has no content.")
        sys.exit(1)

    paragraph_nums = parse_paragraph_spec(paragraph_spec, len(section['paragraphs']))

    for i, para_num in enumerate(paragraph_nums):
        para = section['paragraphs'][para_num - 1]
        print(f"Chapter {chapter_num}, Section {section_num}, Paragraph {para_num}:")
        print("-" * 40)
        print(para)
        print("-" * 40)
        if i < len(paragraph_nums) - 1:
            print()


def main():
    sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description='Parse markdown document structure')
    parser.add_argument('file', help='Path to markdown file')
    parser.add_argument('--overview', action='store_true', help='Show document structure overview')
    parser.add_argument('--chapter', type=int, help='Chapter number to display')
    parser.add_argument('--section', type=int, help='Section number within chapter')
    parser.add_argument('--paragraph', type=str, help='Paragraph(s) to display: N, N-M, N,M,P, or "all"')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File not found: {args.file}")
        sys.exit(1)

    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

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
            chapter_data = {
                'number': i,
                'title': ch['title'],
                'level': ch['level'],
                'sections': []
            }
            for j, sec in enumerate(ch['sections']):
                chapter_data['sections'].append({
                    'number': j,
                    'title': sec['title'],
                    'level': sec['level'],
                    'paragraph_count': len(sec['paragraphs'])
                })
            result['chapters'].append(chapter_data)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    # Determine action
    if args.overview:
        show_overview(chapters)
    elif args.chapter is not None and args.section is not None and args.paragraph:
        show_paragraphs(chapters, args.chapter, args.section, args.paragraph)
    elif args.chapter is not None and args.section is not None:
        show_section(chapters, args.chapter, args.section)
    elif args.chapter is not None:
        show_chapter(chapters, args.chapter)
    else:
        show_overview(chapters)


if __name__ == '__main__':
    main()
