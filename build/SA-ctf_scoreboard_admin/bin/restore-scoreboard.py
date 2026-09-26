#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import configparser
import csv
import json
import os
import ssl
import sys
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
from xml.etree import ElementTree

APPS = ["SA-ctf_scoreboard", "SA-ctf_scoreboard_admin"]
BLACKLIST = {"SavedSearchHistory", "user_realnames", "ta_builder_meta_collection", "SearchHeadClusterHealthStates"}


def load_config() -> configparser.ConfigParser:
    home = os.environ.get("SPLUNK_HOME")
    if not home:
        raise RuntimeError("SPLUNK_HOME is not set")
    path = Path(home) / "etc/apps/SA-ctf_scoreboard_admin/bin/backuprestore.config"
    cfg = configparser.ConfigParser()
    if not cfg.read(path):
        raise RuntimeError(f"Could not read config file: {path}")
    return cfg


def request(cfg, path: str, method: str = "GET", data: bytes | None = None, content_type: str | None = None) -> bytes:
    c = cfg["BackupRestore"]
    url = f"{c.get('SCHEME', 'https')}://{c.get('HOST', '127.0.0.1')}:{c.get('PORT', '8089')}{path}"
    auth = base64.b64encode(f"{c['USER']}:{c['PASS']}".encode()).decode()
    headers = {"Authorization": f"Basic {auth}"}
    if content_type:
        headers["Content-Type"] = content_type
    verify = c.getboolean("VERIFYCERT", fallback=False)
    context = None if verify else ssl._create_unverified_context()
    with urlopen(Request(url, data=data, headers=headers, method=method), context=context, timeout=60) as response:
        return response.read()


def existing_collections(xml_bytes: bytes) -> set[str]:
    root = ElementTree.fromstring(xml_bytes)
    out = set()
    for elem in root:
        if elem.tag.endswith("entry"):
            for child in elem:
                if child.tag.endswith("title") and child.text:
                    out.add(child.text)
    return out


def load_rows(path: Path, use_json: bool) -> list[dict]:
    if use_json:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError(f"{path} does not contain a JSON array")
        return data
    if path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--backupdir", required=True, type=Path)
    parser.add_argument("-j", "--json", action="store_true", help="restore JSON instead of CSV")
    args = parser.parse_args()
    cfg = load_config()
    ext = ".json" if args.json else ".csv"

    for app in APPS:
        appdir = args.backupdir / app
        if not appdir.is_dir():
            print(f"skipping missing {appdir}")
            continue
        existing = existing_collections(request(cfg, f"/servicesNS/nobody/{app}/storage/collections/config"))
        for path in sorted(appdir.glob(f"*{ext}")):
            name = path.stem
            if name in BLACKLIST or name not in existing:
                continue
            endpoint = f"/servicesNS/nobody/{app}/storage/collections/data/{quote(name, safe='')}"
            request(cfg, endpoint, method="DELETE")
            rows = load_rows(path, args.json)
            if rows:
                request(cfg, endpoint + "/batch_save", method="POST", data=json.dumps(rows).encode("utf-8"), content_type="application/json")
            print(f"restored {app}/{name}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
