#!/usr/bin/env bash
# Usage: ./sync_media_s3.sh s3://bucket-name/media/
# Requires: AWS CLI configured with credentials or env vars set (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)

set -euo pipefail

DEST=${1:-}
if [ -z "$DEST" ]; then
  echo "Usage: $0 s3://your-bucket/media/"
  exit 2
fi

echo "Syncing local media/ to $DEST"
aws s3 sync media/ "$DEST" --acl private

echo "Done."
