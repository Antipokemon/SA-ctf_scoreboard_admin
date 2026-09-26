#!/usr/bin/env python3
"""Return the current competitor ACL state for the questions lookup."""
from __future__ import annotations

import json
import sys

import splunk.Intersplunk
import splunk.rest

ACL_PATH = "/servicesNS/nobody/SA-ctf_scoreboard/configs/conf-transforms/ctf_questions/acl"


def _session_key(settings: dict) -> str:
    key = settings.get("sessionKey") or settings.get("session_key")
    if not key:
        raise RuntimeError("Splunk search command did not provide a session key")
    return key


def _read_acl(session_key: str) -> dict:
    _, content = splunk.rest.simpleRequest(
        ACL_PATH,
        sessionKey=session_key,
        getargs={"output_mode": "json"},
    )
    return json.loads(content)


def main() -> None:
    _, _, settings = splunk.Intersplunk.getOrganizedResults()
    try:
        acl = _read_acl(_session_key(settings))["entry"][0]["acl"]["perms"]
        readers = acl.get("read", [])
        writers = acl.get("write", [])
        splunk.Intersplunk.outputResults([{
            "role": "ctf_competitor",
            "canread": int("ctf_competitor" in readers),
            "canwrite": int("ctf_competitor" in writers),
        }])
    except Exception as exc:
        splunk.Intersplunk.generateErrorResults(f"checkqaccess failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
