#!/usr/bin/env python3
"""
Download documents for read-with-me skill.

Usage:
    python download.py <url> [--output-dir DIR]

Supports:
    - arxiv links (e.g., https://arxiv.org/abs/2301.00001)
    - Direct PDF/document URLs
"""

import argparse
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path
from html.parser import HTMLParser


class ArxivTitleParser(HTMLParser):
    """Parse arxiv page to extract paper title."""

    def __init__(self):
        super().__init__()
        self.in_title = False
        self.title = ""

    def handle_starttag(self, tag, attrs):
        if tag == 'title':
            self.in_title = True

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data


def sanitize_filename(name: str, max_length: int = 100) -> str:
    """
    Sanitize a string for use as a filename.

    Replace characters that are invalid in filenames.
    Also strip leading/trailing whitespace and dots.
    """
    # Replace invalid characters with underscore
    invalid_chars = r'[/\:*?"<>|]'
    sanitized = re.sub(invalid_chars, '_', name)

    # Collapse multiple underscores
    sanitized = re.sub(r'_+', '_', sanitized)

    # Strip leading/trailing whitespace, dots, and underscores
    sanitized = sanitized.strip(' ._-')

    # Truncate to max length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip(' ._-')

    return sanitized


def extract_arxiv_id(url: str) -> Optional[str]:
    """
    Extract arxiv ID from various arxiv URL formats.

    Supported formats:
    - https://arxiv.org/abs/2301.00001
    - https://arxiv.org/abs/2301.00001v1
    - https://arxiv.org/pdf/2301.00001.pdf
    - 2301.00001
    """
    patterns = [
        r'arxiv\.org/abs/(\d+\.\d+(?:v\d+)?)',
        r'arxiv\.org/pdf/(\d+\.\d+(?:v\d+)?)\.pdf',
        r'^(\d+\.\d+(?:v\d+)?)$',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


def get_arxiv_title(arxiv_id: str) -> str:
    """Fetch paper title from arxiv."""
    url = f"https://arxiv.org/abs/{arxiv_id}"

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode('utf-8')

        parser = ArxivTitleParser()
        parser.feed(html)

        # Title format is usually "arXiv:XXXX.XXXXX [category] Title"
        title = parser.title
        # Remove arxiv ID prefix if present
        title = re.sub(r'^arXiv:\d+\.\d+(?:v\d+)?\s*(?:\[[\w.-]+\]\s*)?', '', title)
        # Remove "Abstract:" prefix if present
        title = re.sub(r'^Abstract:\s*', '', title)
        # Clean up
        title = title.strip()

        if title:
            return title

    except Exception as e:
        print(f"Warning: Could not fetch title from arxiv: {e}", file=sys.stderr)

    return ""


def download_file(url: str, output_path: Path) -> bool:
    """Download a file from URL."""
    try:
        print(f"Downloading: {url}")
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=60) as response:
            total_size = response.headers.get('content-length')
            total_size = int(total_size) if total_size else None

            downloaded = 0
            block_size = 8192

            with open(output_path, 'wb') as f:
                while True:
                    chunk = response.read(block_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)

                    if total_size:
                        percent = (downloaded / total_size) * 100
                        print(f"\rProgress: {percent:.1f}% ({downloaded}/{total_size} bytes)", end='', flush=True)

            print(f"\nSaved to: {output_path}")
            return True

    except urllib.error.URLError as e:
        print(f"Error downloading: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False


def handle_arxiv(url: str, output_dir: Path) -> Optional[Path]:
    """Handle arxiv URL - download PDF with proper naming."""
    arxiv_id = extract_arxiv_id(url)

    if not arxiv_id:
        print(f"Error: Could not extract arxiv ID from: {url}", file=sys.stderr)
        return None

    print(f"Detected arxiv paper: {arxiv_id}")

    # Get paper title
    title = get_arxiv_title(arxiv_id)
    if title:
        print(f"Paper title: {title}")
        sanitized_title = sanitize_filename(title)
        filename = f"{arxiv_id}_{sanitized_title}.pdf"
    else:
        filename = f"{arxiv_id}.pdf"

    output_path = output_dir / filename

    # Download PDF
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    if download_file(pdf_url, output_path):
        return output_path

    return None


def handle_url(url: str, output_dir: Path) -> Optional[Path]:
    """Handle generic URL - download file."""
    # Try to get filename from URL
    filename = url.split('/')[-1].split('?')[0]
    if not filename or '.' not in filename:
        filename = "downloaded_document.pdf"

    # Sanitize filename
    filename = sanitize_filename(filename)
    output_path = output_dir / filename

    if download_file(url, output_path):
        return output_path

    return None


def main():
    parser = argparse.ArgumentParser(description='Download documents for read-with-me')
    parser.add_argument('url', help='URL to download (arxiv link or direct URL)')
    parser.add_argument('--output-dir', '-o', default='.', help='Output directory (default: current directory)')

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    url = args.url.strip()

    # Determine if this is an arxiv link
    if 'arxiv.org' in url or re.match(r'^\d+\.\d+$', url):
        result = handle_arxiv(url, output_dir)
    else:
        result = handle_url(url, output_dir)

    if result:
        print(f"\nSuccess! File saved to: {result}")
        # Output the path for programmatic use
        print(f"PATH:{result}")
    else:
        print("\nFailed to download document.", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
