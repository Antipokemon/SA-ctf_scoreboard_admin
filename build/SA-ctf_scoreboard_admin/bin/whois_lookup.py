#!/usr/bin/env python3
"""Legacy external lookup retained for the optional geo scoring dashboard."""
from __future__ import annotations

import csv
import sys
from urllib.parse import quote
from urllib.request import Request, urlopen

LOCATION_URL = "http://adam.kahtava.com/services/whois.xml?query="


def lookup(ip: str) -> str:
    try:
        req = Request(LOCATION_URL + quote(ip), headers={"User-Agent": "SA-ctf_scoreboard_admin/10.4"})
        with urlopen(req, timeout=10) as response:
            return response.read().decode("utf-8", errors="replace")
    except Exception:
        return ""


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python whois_lookup.py [ip field] [whois field]", file=sys.stderr)
        return 1
    ipf, whoisf = sys.argv[1:3]
    reader = csv.DictReader(sys.stdin)
    if not reader.fieldnames or ipf not in reader.fieldnames or whoisf not in reader.fieldnames:
        print("IP and whois fields must exist in CSV data", file=sys.stderr)
        return 1
    writer = csv.DictWriter(sys.stdout, fieldnames=reader.fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in reader:
        if row.get(ipf) and not row.get(whoisf):
            row[whoisf] = lookup(row[ipf])
        writer.writerow(row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
