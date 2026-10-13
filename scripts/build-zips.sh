#!/usr/bin/env bash
# Build one zip per skill for upload to claude.ai (Settings > Capabilities > Skills).
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
skills="$root/plugins/pipedrive-skills/skills"
dist="$root/dist"

rm -rf "$dist"
mkdir -p "$dist"

for dir in "$skills"/*/; do
  name="$(basename "$dir")"
  (cd "$skills" && zip -qr "$dist/$name.zip" "$name" -x '*/__pycache__/*' '*.DS_Store')
  echo "built dist/$name.zip"
done
