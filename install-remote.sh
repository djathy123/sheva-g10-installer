#!/bin/bash
# SHEVA G10 v0.2 -- pinned GitHub release installer for macOS ARM64.
set -euo pipefail
if [[ "$(uname -s)" != Darwin || "$(uname -m)" != arm64 ]]; then
  echo "SHEVA_HOLD: macOS Apple Silicon required." >&2
  exit 3
fi
URL="https://github.com/djathy123/sheva-g10-installer/releases/download/v0.2.2/SHEVA_AI_FACTORY_G10_MAC_ARM64_v0.2.2.zip"
EXPECTED="43abc8b51cf07d8e47126f231781d8185c2ce9d7c1ec6a86b2aa0bbd68b909a2"
DEST="$HOME/sheva-g10-installer"
TMP="$(/usr/bin/mktemp -d -t sheva-g10-release)"
trap 'rm -rf "$TMP"' EXIT

echo "[SHEVA] Downloading verified G10 v0.2.2 from GitHub."
/usr/bin/curl --fail --location --silent --show-error --retry 2 --connect-timeout 12 --max-time 180 "$URL" -o "$TMP/bundle.zip"
ACTUAL="$(/usr/bin/shasum -a 256 "$TMP/bundle.zip" | /usr/bin/awk '{print $1}')"
if [[ "$ACTUAL" != "$EXPECTED" ]]; then
  echo "[SHEVA] NO_GO: release SHA256 mismatch" >&2
  exit 4
fi
echo "[SHEVA] Archive SHA256 PASS."
/usr/bin/unzip -q "$TMP/bundle.zip" -d "$TMP/unpacked"
(cd "$TMP/unpacked" && /usr/bin/shasum -a 256 -c SHA256SUMS.txt >/dev/null)
echo "[SHEVA] Internal file integrity PASS."

if [[ -e "$DEST" ]]; then
  while IFS= read -r path; do
    if [[ ! -f "$DEST/$path" ]] || ! /usr/bin/cmp -s "$TMP/unpacked/$path" "$DEST/$path"; then
      echo "[SHEVA] HOLD: existing bundle differs; refusing to overwrite $DEST" >&2
      exit 5
    fi
  done < <(/usr/bin/awk '{print $2}' "$TMP/unpacked/SHA256SUMS.txt")
  if [[ ! -f "$DEST/SHA256SUMS.txt" ]] || ! /usr/bin/cmp -s "$TMP/unpacked/SHA256SUMS.txt" "$DEST/SHA256SUMS.txt"; then
    echo "[SHEVA] HOLD: existing manifest differs." >&2
    exit 5
  fi
  echo "[SHEVA] Existing verified bundle reused."
else
  /bin/mv "$TMP/unpacked" "$DEST"
  echo "[SHEVA] Installed verified bundle to $DEST."
fi

exec /bin/bash "$DEST/bootstrap-macos.sh" "$@"
