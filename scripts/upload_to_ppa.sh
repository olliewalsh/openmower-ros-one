#!/usr/bin/env bash
set -euo pipefail

PPA_TARGET="${PPA_TARGET:?Set PPA_TARGET, for example ppa:your-user/openmower-ros-one}"

shopt -s nullglob
changes=(out/*_source.changes)
if (( ${#changes[@]} == 0 )); then
  echo "No source .changes files found in out/" >&2
  exit 1
fi

for changes_file in "${changes[@]}"; do
  dput "${PPA_TARGET}" "${changes_file}"
done
