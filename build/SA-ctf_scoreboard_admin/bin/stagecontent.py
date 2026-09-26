#!/usr/bin/env python3
"""Download staged CTF CSVs into the admin app lookup directory."""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import splunk.Intersplunk
from splunk.appserver.mrsparkle.lib.util import make_splunkhome_path

LOOKUPS_DIR = Path(make_splunkhome_path(["etc", "apps", "SA-ctf_scoreboard_admin", "lookups"]))
FIELDS = {
    "ctf_users_staged": "ctf_users_staged.csv",
    "ctf_questions_staged": "ctf_questions_staged.csv",
    "ctf_answers_staged": "ctf_answers_staged.csv",
    "ctf_hints_staged": "ctf_hints_staged.csv",
}
MAX_BYTES = 50 * 1024 * 1024


def _download(url: str, destination: Path) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"Unsupported URL scheme for {url!r}")
    request = Request(url, headers={"User-Agent": "SA-ctf_scoreboard_admin/10.4"})
    with urlopen(request, timeout=30) as response:
        length = response.headers.get("Content-Length")
        if length and int(length) > MAX_BYTES:
            raise ValueError(f"Staged file exceeds {MAX_BYTES} bytes")
        with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as tmp:
            copied = 0
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                copied += len(chunk)
                if copied > MAX_BYTES:
                    raise ValueError(f"Staged file exceeds {MAX_BYTES} bytes")
                tmp.write(chunk)
            temp_name = tmp.name
    os.replace(temp_name, destination)


def main() -> None:
    _, options = splunk.Intersplunk.getKeywordsAndOptions()
    missing = [name for name in FIELDS if not options.get(name)]
    if missing:
        splunk.Intersplunk.generateErrorResults("Missing required options: " + ", ".join(missing))
        sys.exit(1)

    LOOKUPS_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    try:
        for name, filename in FIELDS.items():
            url = options[name]
            _download(url, LOOKUPS_DIR / filename)
            results.append({"_time": time.time(), "_raw": url, "lookup": filename, "status": "staged"})
        splunk.Intersplunk.outputResults(results)
    except Exception as exc:
        splunk.Intersplunk.generateErrorResults(f"stagecontent failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
