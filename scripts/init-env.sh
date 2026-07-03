#!/usr/bin/env bash
# Simple helper to create a local .env from .env.example
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXAMPLE="$ROOT_DIR/.env.example"
TARGET="$ROOT_DIR/.env"

if [ ! -f "$EXAMPLE" ]; then
  echo ".env.example not found in $ROOT_DIR" >&2
  exit 1
fi

if [ -f "$TARGET" ]; then
  bak="$TARGET.bak_$(date +%Y%m%d%H%M%S)"
  echo ".env already exists — backing up to $bak"
  cp "$TARGET" "$bak"
fi

cp "$EXAMPLE" "$TARGET"

if command -v python >/dev/null 2>&1; then
  secret=$(python - <<'PY'
import secrets
print(secrets.token_hex(32))
PY
)
  # replace first DJANGO_SECRET_KEY line
  awk -v s="$secret" 'BEGIN{FS=OFS=""} {if(!done && $0 ~ /^DJANGO_SECRET_KEY=/){print "DJANGO_SECRET_KEY=" s; done=1} else print $0}' "$TARGET" > "$TARGET.tmp" && mv "$TARGET.tmp" "$TARGET"
  echo "Created $TARGET (DJANGO_SECRET_KEY set)."
else
  echo "Created $TARGET. Please set DJANGO_SECRET_KEY manually (python not found)."
fi

echo "Edit $TARGET to fill DB credentials and other secrets."