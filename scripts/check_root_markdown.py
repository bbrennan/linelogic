#!/usr/bin/env python3
"""Fail if new Markdown files appear in the repo root.

This repo intentionally keeps documentation under docs/ (and other top-level
folders). Root-level Markdown is limited to a small allowlist.

Usage:
  python scripts/check_root_markdown.py
"""

from __future__ import annotations

from pathlib import Path


ALLOWED_ROOT_MARKDOWN = {
    "README.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
}


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    root_md = sorted(p.name for p in repo_root.glob("*.md"))

    disallowed = [name for name in root_md if name not in ALLOWED_ROOT_MARKDOWN]
    if not disallowed:
        return 0

    allowed_sorted = ", ".join(sorted(ALLOWED_ROOT_MARKDOWN))
    disallowed_sorted = "\n".join(f"- {name}" for name in disallowed)

    msg = (
        "Root-level Markdown files are not allowed (prevents 'file swamp').\n"
        "Move docs into docs/ (or an appropriate folder) instead.\n\n"
        f"Allowed root Markdown: {allowed_sorted}\n\n"
        "Disallowed root Markdown found:\n"
        f"{disallowed_sorted}\n"
    )
    raise SystemExit(msg)


if __name__ == "__main__":
    raise SystemExit(main())
