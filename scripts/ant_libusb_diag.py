#!/usr/bin/env python3
"""
ANT+ libusb diagnostics

Probes the ANT USB stick via PyUSB (libusb):
- Finds the Dynastream device (0x0fcf:0x1008)
- Detaches kernel driver if active
- Sets configuration and claims interface 0
- Discovers bulk IN/OUT endpoints
- Sends ANT System Reset and reads any response frames

Prints detailed step-by-step status to help pinpoint failures.
"""

import sys
import time
import usb.core
import usb.util

VID = 0x0fcf
PID = 0x1008

SYNC = 0xA4
MSG_SYSTEM_RESET = 0x4A


def xor_checksum(payload_bytes):
    chk = 0
    for b in payload_bytes:
        chk ^= b
    return chk


def ant_frame(msg_id, data):
    frame = [SYNC, len(data), msg_id] + data
    frame.append(xor_checksum(frame[1:]))
    return frame


def main():
    print("[INFO] Searching for ANT stick 0x%04x:0x%04x" % (VID, PID))
    dev = usb.core.find(idVendor=VID, idProduct=PID)
    if dev is None:
        print("[ERROR] ANT stick not found")
        sys.exit(1)

    # Detach kernel driver if needed
    try:
        if dev.is_kernel_driver_active(0):
            print("[INFO] Detaching kernel driver from interface 0")
            dev.detach_kernel_driver(0)
        else:
            print("[INFO] No kernel driver attached to interface 0")
    except Exception as e:
        print(f"[WARN] Kernel driver check/detach failed: {e}")

    # Set configuration
    try:
        dev.set_configuration()
        print("[INFO] Set device configuration")
    except Exception as e:
        print(f"[ERROR] set_configuration failed: {e}")
        sys.exit(2)

    # Get active configuration and interface
    try:
        cfg = dev.get_active_configuration()
        intf = usb.util.find_descriptor(cfg, bInterfaceNumber=0)
        if intf is None:
            print("[ERROR] Could not get interface 0 from active configuration")
            sys.exit(3)
        print("[INFO] Active config set; interface 0 obtained")
    except Exception as e:
        print(f"[ERROR] Failed to get active configuration/interface: {e}")
        sys.exit(3)

    # Claim interface
    try:
        usb.util.claim_interface(dev, 0)
        print("[INFO] Claimed interface 0")
    except Exception as e:
        print(f"[WARN] claim_interface failed (continuing): {e}")

    # Discover endpoints
    ep_out = None
    ep_in = None
    try:
        for ep in intf:
            addr = ep.bEndpointAddress
            is_in = bool(addr & 0x80)
            is_bulk = (ep.bmAttributes & 0x03) == 0x02
            print(f"[INFO] Endpoint 0x{addr:02x}: bulk={is_bulk} in={is_in} maxPacket={ep.wMaxPacketSize}")
            if is_bulk and not is_in:
                ep_out = ep
            elif is_bulk and is_in:
                ep_in = ep

        if not ep_out or not ep_in:
            print("[ERROR] Could not find bulk IN/OUT endpoints")
            sys.exit(4)
        else:
            print(f"[INFO] Using OUT 0x{ep_out.bEndpointAddress:02x}, IN 0x{ep_in.bEndpointAddress:02x}")
    except Exception as e:
        print(f"[ERROR] Endpoint discovery failed: {e}")
        sys.exit(4)

    # Send ANT System Reset
    try:
        frame = ant_frame(MSG_SYSTEM_RESET, [0x00])
        print(f"[INFO] Sending System Reset: {frame}")
        wrote = dev.write(ep_out.bEndpointAddress, frame, timeout=1000)
        print(f"[INFO] Wrote {wrote} bytes to OUT 0x{ep_out.bEndpointAddress:02x}")
    except Exception as e:
        print(f"[ERROR] Bulk write failed: {e}")
        sys.exit(5)

    # Read response (if any)
    try:
        print("[INFO] Reading for up to 1s...")
        data = dev.read(ep_in.bEndpointAddress, ep_in.wMaxPacketSize or 64, timeout=1000)
        payload = list(data)
        print(f"[INFO] Read {len(payload)} bytes from IN 0x{ep_in.bEndpointAddress:02x}: {payload}")
    except usb.core.USBTimeoutError:
        print("[WARN] Read timed out (no immediate response). This can be normal after reset.")
    except Exception as e:
        print(f"[ERROR] Bulk read failed: {e}")
        sys.exit(6)

    # Release interface
    try:
        usb.util.release_interface(dev, 0)
        print("[INFO] Released interface 0")
    except Exception as e:
        print(f"[WARN] release_interface failed: {e}")

    print("[SUCCESS] libusb basic operations completed")
    sys.exit(0)


if __name__ == "__main__":
    main()