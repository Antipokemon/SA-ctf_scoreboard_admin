#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import configparser
import csv
import datetime as dt
import json
import os
import ssl
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from xml.etree import ElementTree

APPS = ["SA-ctf_scoreboard", "SA-ctf_scoreboard_admin"]
BLACKLIST = {
    "SavedSearchHistory", "user_realnames", "ta_builder_meta_collection",
    "SearchHeadClusterHealthStates", "SamlIdpCerts", "SearchHeadClusterMemberInfo",
}


def load_config() -> configparser.ConfigParser:
    splunk_home = os.environ.get("SPLUNK_HOME")
    if not splunk_home:
        raise RuntimeError("SPLUNK_HOME is not set")
    path = Path(splunk_home) / "etc/apps/SA-ctf_scoreboard_admin/bin/backuprestore.config"
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


def collection_names(xml_bytes: bytes, app: str) -> list[str]:
    root = ElementTree.fromstring(xml_bytes)
    names = []
    for elem in root:
        if not elem.tag.endswith("entry"):
            continue
        title = None
        belongs = False
        for child in elem:
            if child.tag.endswith("title"):
                title = child.text
            elif child.tag.endswith("id") and child.text and app in child.text:
                belongs = True
        if title and belongs and title not in BLACKLIST:
            names.append(title)
    return names


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-j", "--json", action="store_true", help="also write JSON backups")
    args = parser.parse_args()
    cfg = load_config()
    base = Path(cfg["BackupRestore"].get("BACKUPDIR", "/tmp")) / dt.datetime.now().strftime("%Y%m%d%H%M%S")
    base.mkdir(parents=True, exist_ok=True)

    for app in APPS:
        appdir = base / app
        appdir.mkdir(parents=True, exist_ok=True)
        listing = request(cfg, f"/servicesNS/nobody/{app}/storage/collections/config")
        for name in collection_names(listing, app):
            payload = request(cfg, f"/servicesNS/nobody/{app}/storage/collections/data/{name}?output_mode=json")
            rows = json.loads(payload.decode("utf-8"))
            if not isinstance(rows, list):
                raise RuntimeError(f"Unexpected KV Store response for {app}/{name}")
            if rows:
                keys = sorted({k for row in rows for k in row.keys()})
                with (appdir / f"{name}.csv").open("w", newline="", encoding="utf-8") as fh:
                    writer = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
                    writer.writeheader(); writer.writerows(rows)
            else:
                (appdir / f"{name}.csv").write_text("", encoding="utf-8")
            if args.json:
                (appdir / f"{name}.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"backed up {app}/{name}")
    print(base)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
