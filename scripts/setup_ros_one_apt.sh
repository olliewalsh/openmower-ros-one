#!/usr/bin/env bash
set -euo pipefail

install -d -m 0755 /etc/apt/keyrings
if [ ! -f /etc/apt/keyrings/ros-one-keyring.gpg ]; then
  curl -fsSL https://ros.packages.techfak.net/gpg.key \
    -o /etc/apt/keyrings/ros-one-keyring.gpg
fi
arch="$(dpkg --print-architecture)"
printf 'deb [arch=%s signed-by=/etc/apt/keyrings/ros-one-keyring.gpg] https://ros.packages.techfak.net noble main\n' "$arch" \
  > /etc/apt/sources.list.d/ros-one.list
apt-get update
