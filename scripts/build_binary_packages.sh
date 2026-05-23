#!/usr/bin/env bash
set -euo pipefail

if [ ! -f /etc/apt/sources.list.d/ros-one.list ]; then
  scripts/setup_ros_one_apt.sh
fi
python3 scripts/build_source_packages.py --binary "$@"
