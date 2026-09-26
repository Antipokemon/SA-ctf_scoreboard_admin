#!/usr/bin/env python3
"""Toggle competitor read access to the questions lookup."""
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


def _request_acl(session_key: str) -> dict:
    _, content = splunk.rest.simpleRequest(
        ACL_PATH,
        sessionKey=session_key,
        getargs={"output_mode": "json"},
    )
    return json.loads(content)


def main() -> None:
    _, _, settings = splunk.Intersplunk.getOrganizedResults()
    try:
        session_key = _session_key(settings)
        current = _request_acl(session_key)["entry"][0]["acl"]["perms"]
        readers = list(current.get("read", []))
        writers = list(current.get("write", []))

        if "ctf_competitor" in readers:
            readers.remove("ctf_competitor")
        else:
            readers.append("ctf_competitor")
        writers = [role for role in writers if role != "ctf_competitor"]

        _, content = splunk.rest.simpleRequest(
            ACL_PATH,
            method="POST",
            sessionKey=session_key,
            postargs={
                "output_mode": "json",
                "sharing": "global",
                "owner": "nobody",
                "perms.read": ",".join(readers),
                "perms.write": ",".join(writers),
            },
        )
        updated = json.loads(content)["entry"][0]["acl"]["perms"]
        splunk.Intersplunk.outputResults([{
            "role": "ctf_competitor",
            "canread": int("ctf_competitor" in updated.get("read", [])),
            "canwrite": int("ctf_competitor" in updated.get("write", [])),
        }])
    except Exception as exc:
        splunk.Intersplunk.generateErrorResults(f"toggleqaccess failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
