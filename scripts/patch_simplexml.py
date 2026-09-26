#!/usr/bin/env python3
from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT_RE = re.compile(r"<(dashboard|form)(\s|>)")
VERSION_RE = re.compile(r"<(dashboard|form)\b([^>]*)\bversion=([\"'])[^\"']*\3([^>]*)>")


def patch(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if not ROOT_RE.search(text):
        return False
    if re.search(r"<(dashboard|form)\b[^>]*\bversion=[\"']1\.1[\"']", text):
        return False
    if re.search(r"<(dashboard|form)\b[^>]*\bversion=[\"'][^\"']+[\"']", text):
        new = re.sub(r"(<(?:dashboard|form)\b[^>]*\bversion=)[\"'][^\"']+[\"']", r'\1"1.1"', text, count=1)
    else:
        new = re.sub(r"<(dashboard|form)\b", r'<\1 version="1.1"', text, count=1)
    path.write_text(new, encoding="utf-8")
    return True


def main() -> int:
    root = Path(sys.argv[1])
    count = 0
    for path in (root / "default/data/ui/views").glob("*.xml"):
        count += int(patch(path))
    print(f"patched {count} Simple XML views")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
