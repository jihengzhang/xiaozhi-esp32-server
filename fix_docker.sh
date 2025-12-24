#!/usr/bin/env bash
set -euo pipefail

# Switch Docker to the default socket and remove the Desktop credential helper.
info() { printf '[info] %s\n' "$*"; }

command -v docker >/dev/null 2>&1 || { echo "docker is not installed" >&2; exit 1; }

info "Switching docker context to 'default'"
docker context use default >/dev/null

CONFIG_FILE="${HOME}/.docker/config.json"
BACKUP_FILE="${CONFIG_FILE}.bak-$(date +%Y%m%d%H%M%S)"

if [ -f "$CONFIG_FILE" ]; then
    info "Backing up existing config to $BACKUP_FILE"
    cp "$CONFIG_FILE" "$BACKUP_FILE"
else
    info "Creating ${CONFIG_FILE}"
    mkdir -p "${HOME}/.docker"
    printf '{"auths":{}}' >"$CONFIG_FILE"
fi

info "Removing credsStore from ${CONFIG_FILE} if present"
python - <<'PY'
import json
from pathlib import Path

cfg = Path("~/.docker/config.json").expanduser()
data = {}
if cfg.exists():
    content = cfg.read_text().strip()
    if content:
        data = json.loads(content)

removed = data.pop("credsStore", None)
cfg.write_text(json.dumps(data, indent=4))
if removed:
    print("Removed credsStore entry")
else:
    print("credsStore was not set")
PY

info "Done. You can now rerun: docker compose up -d"
