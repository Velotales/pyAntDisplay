#!/usr/bin/env bash
set -euo pipefail

RULE_SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RULE_FILE="$RULE_SRC_DIR/50-ant.rules"
DEST_FILE="/etc/udev/rules.d/50-ant.rules"

echo "Installing ANT+ udev rules to $DEST_FILE"
if [ "$EUID" -ne 0 ]; then
  echo "This script needs root to write to /etc/udev. Re-running with sudo..."
  exec sudo "$0"
fi

install -m 0644 "$RULE_FILE" "$DEST_FILE"
udevadm control --reload-rules
udevadm trigger

echo "Done. Unplug and replug your ANT+ stick to apply new permissions."