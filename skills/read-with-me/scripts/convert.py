#!/usr/bin/env python3
"""
Convert documents to markdown using MarkItDown.

Usage:
    python convert.py <file>                    # Output: <file>.md (same directory)
    python convert.py <file> -o <output.md>     # Output: specified path

Supports: PDF, Word, Excel, PowerPoint, HTML, and other formats supported by MarkItDown.
Passes through .md and .txt files without conversion.
"""

import argparse
import sys
from pathlib import Path


PASSTHROUGH_EXTENSIONS = {'.md', '.txt', '.markdown', '.text'}


def main():
    # Fix Windows console encoding for Unicode output
    sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description='Convert documents to markdown using MarkItDown')
    parser.add_argument('file', help='Path to document file')
    parser.add_argument('-o', '--output', help='Output file path (default: same name with .md extension)')

    args = parser.parse_args()

    input_path = Path(args.file)
    if not input_path.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    # Passthrough for markdown/txt files
    if input_path.suffix.lower() in PASSTHROUGH_EXTENSIONS:
        if args.output:
            # Copy to specified output
            output_path = Path(args.output)
            output_path.write_text(input_path.read_text(encoding='utf-8'), encoding='utf-8')
            print(f"PASSED_THROUGH:{output_path}")
        else:
            print(f"PASSED_THROUGH:{input_path}")
        return

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.with_suffix('.md')

    # Convert using MarkItDown
    try:
        from markitdown import MarkItDown
    except ImportError:
        print("Error: markitdown package is not installed. Install it with: pip install markitdown", file=sys.stderr)
        sys.exit(1)

    try:
        md = MarkItDown()
        result = md.convert(str(input_path))
        output_path.write_text(result.text_content, encoding='utf-8')
        print(f"CONVERTED:{output_path}")
    except Exception as e:
        print(f"Error converting file: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
