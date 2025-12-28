#!/usr/bin/env python3
"""
pyantdisplay.common

Shared utilities:
- Type names mapping
- Manufacturer name lookup (config/manufacturers.yaml)
- Parse ANT+ common pages (80/81)
- Deep-merge persistence of found devices with optional rate limiting
"""

import json
import time
from typing import Dict, Optional

import yaml

TYPE_NAMES: Dict[int, str] = {
    120: "Heart Rate Monitor",
    121: "Speed and Cadence Sensor",
    122: "Cadence Sensor",
    123: "Speed Sensor",
    11: "Power Meter",
    16: "Fitness Equipment",
    17: "Environment Sensor",
}


def load_manufacturers(path: str = "config/manufacturers.yaml") -> Dict[int, str]:
    default = {1: "Garmin/Dynastream"}
    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f) or {}
        custom = {int(k): str(v) for k, v in (data.get("manufacturers", {}) or {}).items()}
        default.update(custom)
    except Exception:
        pass
    return default


def parse_common_pages(data: bytes) -> Dict[str, object]:
    info: Dict[str, object] = {}
    try:
        page = data[0]
        if page == 80:
            manufacturer_id = data[1] | (data[2] << 8)
            serial_number = data[3] | (data[4] << 8) | (data[5] << 16) | (data[6] << 24)
            info.update(
                {
                    "manufacturer_id": manufacturer_id,
                    "serial_number": serial_number,
                }
            )
        elif page == 81:
            hw_revision = data[1]
            sw_rev_major = data[2]
            sw_rev_minor = data[3]
            model_number = data[4] | (data[5] << 8)
            info.update(
                {
                    "hw_revision": hw_revision,
                    "sw_revision": f"{sw_rev_major}.{sw_rev_minor}",
                    "model_number": model_number,
                }
            )
    except Exception:
        pass
    return info


def record_key(device_type: int, device_id: int) -> str:
    return f"{device_type}_{device_id}"


def deep_merge_save(
    save_path: str,
    device_id: int,
    device_type: int,
    transmission_type: Optional[int],
    base_extra: Optional[Dict[str, object]] = None,
    manufacturers: Optional[Dict[int, str]] = None,
    rate_limit_secs: Optional[int] = None,
    last_save_times: Optional[Dict[str, float]] = None,
) -> None:
    """
    Deep-merge a device record into the JSON file.
    Optionally rate-limit writes by record key.
    """
    desc = TYPE_NAMES.get(device_type, f"Device type {device_type}")
    base = {
        "device_id": device_id,
        "device_type": device_type,
        "transmission_type": transmission_type,
        "description": desc,
        "last_seen": time.time(),
    }
    if base_extra:
        base.update(base_extra)
    # Enrich manufacturer_name
    try:
        mid = base.get("manufacturer_id")
        if manufacturers and isinstance(mid, int):
            mname = manufacturers.get(mid)
            if mname:
                base["manufacturer_name"] = mname
    except Exception:
        pass

    rk = record_key(device_type, device_id)
    # Rate limit
    if rate_limit_secs and last_save_times is not None:
        now = time.time()
        last = last_save_times.get(rk, 0)
        should_write = bool(base_extra) or (now - last) > rate_limit_secs
        if not should_write:
            return
        last_save_times[rk] = now

    # Load existing and merge
    try:
        try:
            with open(save_path, "r") as f:
                existing = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            existing = {}
        merged = existing.get(rk, {})
        merged.update(base)
        existing[rk] = merged
        with open(save_path, "w") as f:
            json.dump(existing, f, indent=2)
    except Exception:
        # Swallow persistence errors silently; caller can log if needed
        pass
