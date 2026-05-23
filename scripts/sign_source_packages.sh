#!/usr/bin/env bash
set -euo pipefail

shopt -s nullglob
changes=(out/*_source.changes)
if (( ${#changes[@]} == 0 )); then
  echo "No source .changes files found in out/" >&2
  exit 1
fi

key_args=()
if [[ -n "${DEBSIGN_KEYID:-}" ]]; then
  key_args=(-k"${DEBSIGN_KEYID}")
elif [[ -n "${DEBEMAIL:-}" ]]; then
  key_args=(-k"${DEBEMAIL}")
else
  cat >&2 <<'EOF'
No signing key selected. Set one of:

  DEBSIGN_KEYID=YOUR_KEY_ID
  DEBEMAIL=your-launchpad-email@example.com

Example:

  DEBSIGN_KEYID=0123456789ABCDEF scripts/sign_source_packages.sh
EOF
  exit 2
fi

for changes_file in "${changes[@]}"; do
  debsign "${key_args[@]}" "${changes_file}"
done
