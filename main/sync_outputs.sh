#!/usr/bin/env bash
# Sync selected files from source to destination using rsync
# Usage: ./sync_selected_files.sh <source> <destination> [--dry-run]

set -e

SOURCE="$1"
DEST="$2"
DRYRUN="$3"

if [[ -z "$SOURCE" || -z "$DEST" ]]; then
  echo "Usage: $0 <source> <destination> [--dry-run]"
  exit 1
fi

# Base rsync options
RSYNC_OPTS=(
  -av
  --update            # skip files that are newer on the receiver
  --prune-empty-dirs  # don't create empty directories
  --include='sync_outputs.sh'
  --exclude='**/__backups__/'
  --include='systems/'
  --include='analyze.ipynb'
  --include='systems/cu_nh3/'
  --include='systems/nh3/'
  --include='systems/cu/'
  --exclude='**/.ipynb*/'
  --include='**/standard/'
  --include='**/xg/'
  --include='**/standard/**/'
  --include='**/xg/**/'
  --include='*.out'
  --include='*.inp'
  --include='*.cs'
  --include='*.csv'
  --include='*.xml'
  --include='*.json'
  --include='*.tinp'
  --exclude='*'
)

# Add dry-run flag if requested
if [[ "$DRYRUN" == "--dry-run" ]]; then
  RSYNC_OPTS+=(--dry-run)
  echo ">>> Running in dry-run mode. No files will be transferred."
fi

echo ">>> Syncing from: $SOURCE"
echo ">>> To:           $DEST"

rsync "${RSYNC_OPTS[@]}" "$SOURCE"/ "$DEST"/

