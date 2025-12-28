#!/usr/bin/env bash
set -euo pipefail

CONF_FILE="/etc/modprobe.d/blacklist-ant-usbserial.conf"

echo "Installing kernel module blacklist to prevent usbserial_simple from grabbing ANT stick"
if [ "$EUID" -ne 0 ]; then
  echo "This script needs root. Re-running with sudo..."
  exec sudo "$0"
fi

printf "# Prevent kernel usbserial_simple (suunto converter) from binding to Dynastream ANT sticks\nblacklist usb_serial_simple\n" > "$CONF_FILE"

echo "Reloading modules (will try to remove usbserial_simple if loaded)"
modprobe -r usb_serial_simple || true
modprobe -r usbserial || true

echo "Done. Unplug and replug your ANT+ stick, then re-run the test."