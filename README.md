# SA-ctf_scoreboard_admin — Splunk Enterprise 10.4 compatibility fork

This repository is a reproducible compatibility layer for Splunk's deprecated
`SA-ctf_scoreboard_admin` app. It is intended to be deployed with the matching
Splunk 10.4 compatibility fork of `SA-ctf_scoreboard`.

Upstream: `splunk/SA-ctf_scoreboard_admin`

Pinned upstream commit:

```text
7a694a52faed46160dd4e0cebf76dece149f066e
```

## What changed

- Replaced the old vendored Splunk Python SDK dependency for custom commands with
  Splunk's built-in legacy `Intersplunk` command protocol.
- Converted `checkqaccess`, `toggleqaccess`, and `stagecontent` to Python 3.9/3.13.
- Converted `backup-scoreboard.py` and `restore-scoreboard.py` from Python 2 to
  Python 3 without requiring the third-party `requests` package.
- Converted `whois_lookup.py` to Python 3.
- Removed the dead `whoisLookupRedis` transform, which referenced a file that is
  not present in the upstream repository.
- Sets the external WHOIS lookup to `python.version = python3`.
- Converts all Simple XML `<dashboard>` and `<form>` roots to `version="1.1"`
  when the app is built.
- Removes the upstream `bin/splunklib` copy from the generated app.
- Sets the compatibility app version to `10.4.1`.
- Adds tests and GitHub Actions packaging.

## Build the complete installable app

Requirements: `bash`, `curl`, `tar`, and Python 3.

```bash
make package
```

The build downloads the exact pinned upstream source, applies this compatibility
layer, validates the maintained Python, updates Simple XML, and creates:

```text
dist/SA-ctf_scoreboard_admin-10.4.1.tar.gz
```

Install that tarball through Splunk Web or extract it under `$SPLUNK_HOME/etc/apps`.

## Local validation

```bash
make test
```

## Backup/restore configuration

The upstream `bin/backuprestore.config.example` remains in the generated app.
Copy it to `bin/backuprestore.config` and set the REST API credentials and backup
path before using the utilities:

```bash
cp $SPLUNK_HOME/etc/apps/SA-ctf_scoreboard_admin/bin/backuprestore.config.example \
   $SPLUNK_HOME/etc/apps/SA-ctf_scoreboard_admin/bin/backuprestore.config
```

Then run, for example:

```bash
$SPLUNK_HOME/bin/splunk cmd python3 \
  $SPLUNK_HOME/etc/apps/SA-ctf_scoreboard_admin/bin/backup-scoreboard.py -j
```

Restore:

```bash
$SPLUNK_HOME/bin/splunk cmd python3 \
  $SPLUNK_HOME/etc/apps/SA-ctf_scoreboard_admin/bin/restore-scoreboard.py \
  -d /path/to/backup
```

## Pairing with the participant app

This admin app provides the protected answers/hints KV stores expected by
`SA-ctf_scoreboard`. Install both compatibility builds on the same Splunk
instance unless you deliberately redesign the REST/KV-store topology.

The participant controller still requires its
`appserver/controllers/scoreboard_controller.config` service account settings.

## Important compatibility note

Splunk 10.4 still supports the functionality needed by this app, but this is an
unsupported community compatibility fork of software Splunk deprecated in 2022.
Custom CherryPy controller use is in the participant app, not this admin app, and
is itself deprecated in Splunk 10.4 for future removal. Plan to test the complete
question/answer/hint/scoring workflow before an event.

## License

The upstream project is CC0 1.0 Universal. This compatibility layer follows the
same licensing intent.
