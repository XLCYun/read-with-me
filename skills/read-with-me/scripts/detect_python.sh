#!/usr/bin/env bash
# One-time Python environment detector.
# Outputs the working Python invocation command for the agent to reuse.
# Usage: bash scripts/detect_python.sh
# Output: "python", "python3", or "uv run python"

set -euo pipefail

# Test 1: uv run python
if command -v uv &>/dev/null && uv run python -c "import sys; sys.exit(0)" &>/dev/null; then
  echo "uv run python"
  exit 0
fi

# Test 2: python3
if command -v python3 &>/dev/null && python3 -c "import sys; sys.exit(0)" &>/dev/null; then
  echo "python3"
  exit 0
fi

# Test 3: python
if command -v python &>/dev/null && python -c "import sys; sys.exit(0)" &>/dev/null; then
  echo "python"
  exit 0
fi

echo "ERROR: No working Python found. Install Python 3.10+ or uv." >&2
exit 1
