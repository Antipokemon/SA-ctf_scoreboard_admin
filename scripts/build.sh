#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UPSTREAM_COMMIT="$(tr -d '[:space:]' < "$ROOT/UPSTREAM_COMMIT")"
WORK="$ROOT/build"
DIST="$ROOT/dist"
APP="$WORK/SA-ctf_scoreboard_admin"
ARCHIVE="$WORK/upstream.tar.gz"
URL="https://github.com/splunk/SA-ctf_scoreboard_admin/archive/${UPSTREAM_COMMIT}.tar.gz"

rm -rf "$WORK" "$DIST"
mkdir -p "$WORK" "$DIST"

curl -fL --retry 3 --connect-timeout 20 "$URL" -o "$ARCHIVE"
tar -xzf "$ARCHIVE" -C "$WORK"
mv "$WORK/SA-ctf_scoreboard_admin-${UPSTREAM_COMMIT}" "$APP"
rm -f "$ARCHIVE"

# Remove the 2022 vendored Python SDK. Splunk 10.4 supplies the runtime APIs
# used by the maintained scripts in this fork.
rm -rf "$APP/bin/splunklib"

cp -a "$ROOT/overrides/." "$APP/"

# Merge compatibility metadata instead of replacing upstream default.meta.
# ctf_questions is owned by the admin app and must remain system-visible to
# the participant app while answers/hints stay protected.
if [[ -f "$ROOT/metadata/default.meta" ]]; then
    printf '\n' >> "$APP/metadata/default.meta"
    cat "$ROOT/metadata/default.meta" >> "$APP/metadata/default.meta"
fi

python3 "$ROOT/scripts/patch_simplexml.py" "$APP"

# Avoid shipping runtime/generated secrets or caches.
rm -f "$APP/bin/backuprestore.config"
find "$APP" -type d -name '__pycache__' -prune -exec rm -rf {} +
find "$APP" -type f -name '*.pyc' -delete

tar -C "$WORK" -czf "$DIST/SA-ctf_scoreboard_admin-10.4.1.tar.gz" SA-ctf_scoreboard_admin
sha256sum "$DIST/SA-ctf_scoreboard_admin-10.4.1.tar.gz" > "$DIST/SA-ctf_scoreboard_admin-10.4.1.tar.gz.sha256"
echo "Created $DIST/SA-ctf_scoreboard_admin-10.4.1.tar.gz"
