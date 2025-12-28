#!/usr/bin/env python3
"""
PyANTDisplay - Live Monitor

Runs continuously, scans and connects to ANT+ devices, maps sensors to users
based on a YAML config, and renders a non-scrolling console dashboard.

Usage:
  python -m pyantdisplay.live_monitor --config config/sensor_map.yaml --save found_devices.json [--debug]
"""

import curses
import logging
import signal
import sys
import threading
import time
from typing import Dict, List, Optional

import yaml
from colorama import Fore, Style

from .common import deep_merge_save, load_manufacturers, parse_common_pages

try:
    from openant.easy.channel import Channel
    from openant.easy.node import Message, Node
except ImportError:
    print("openant is not installed. Run ./setup.sh first.")
    sys.exit(1)

ANT_PLUS_NETWORK_KEY = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]


def configure_logging(debug: bool):
    logging.basicConfig(
        level=(logging.DEBUG if debug else logging.INFO), format="[%(levelname)s] %(name)s: %(message)s"
    )
    for name in [
        "openant",
        "openant.base",
        "openant.base.ant",
        "openant.base.driver",
        "openant.easy",
        "openant.easy.node",
        "openant.easy.channel",
        "openant.easy.filter",
    ]:
        logging.getLogger(name).setLevel(logging.DEBUG if debug else logging.WARNING)


class LiveMonitor:
    def __init__(self, config_path: str, save_path: str, debug: bool = False):
        self.config_path = config_path
        self.save_path = save_path
        self.debug = debug
        self.config = self._load_config()
        self.node: Optional[Node] = None
        self.loop_thread: Optional[threading.Thread] = None
        self.channels: List[Channel] = []

        # Device and user state
        self.lock = threading.Lock()
        self.device_values: Dict[int, Dict] = {}  # device_id -> parsed values + meta
        self.user_values: Dict[str, Dict] = {}  # user -> hr/speed/cadence/power
        self.last_hr_active_user: Optional[str] = None
        self.stop_event = threading.Event()
        self.last_save_times: Dict[str, float] = {}
        self.manufacturer_map: Dict[int, str] = load_manufacturers()

    def _load_config(self) -> dict:
        try:
            with open(self.config_path, "r") as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            print(f"{Fore.YELLOW}Config not found: {self.config_path}{Style.RESET_ALL}")
            return {
                "sensor_map": {
                    "users": [],
                    "wattbike": {
                        "speed_device_id": None,
                        "cadence_device_id": None,
                        "power_device_id": None,
                        "auto_assign": True,
                    },
                }
            }

    def _save_found(self, dev_num: int, dev_type: int, trans_type: int, extra: dict | None = None):
        deep_merge_save(
            self.save_path,
            dev_num,
            dev_type,
            trans_type,
            base_extra=extra,
            manufacturers=self.manufacturer_map,
            rate_limit_secs=30,
            last_save_times=self.last_save_times,
        )

    def start(self):
        # Start node in background
        self.node = Node()
        self.loop_thread = threading.Thread(target=self.node.start, name="openant.easy.main", daemon=True)
        self.loop_thread.start()
        # Set network key
        self.node.set_network_key(0, ANT_PLUS_NETWORK_KEY)
        # Open channels per config
        self._open_configured_channels()

    def stop(self):
        self.stop_event.set()
        try:
            for ch in self.channels:
                try:
                    ch.close()
                except Exception:
                    pass
            self.channels.clear()
        finally:
            if self.node:
                try:
                    self.node.stop()
                except Exception:
                    pass

    def _open_channel(self, device_id: int, device_type: int, label: str):
        ch = self.node.new_channel(Channel.Type.BIDIRECTIONAL_RECEIVE)

        # Callbacks
        def on_broadcast(data):
            # Parse based on device_type
            with self.lock:
                parsed = None
                if device_type == 120:  # HR
                    try:
                        # page = data[0]  # Page number not currently used
                        beat_time = (data[4] | (data[5] << 8)) / 1024.0
                        beat_count = data[6]
                        hr = data[7]
                        parsed = {
                            "type": "hr",
                            "hr": hr,
                            "beat_time": beat_time,
                            "beat_count": beat_count,
                            "ts": time.time(),
                        }
                    except Exception:
                        parsed = {"type": "hr", "hr": 0, "ts": time.time()}
                elif device_type in (121, 123, 122):
                    # Speed/Cadence profiles
                    try:
                        # page = data[0]  # Page number not currently used
                        evt_time = data[4] | (data[5] << 8)
                        revs = data[6] | (data[7] << 8)
                        prev = self.device_values.get(device_id, {})
                        last_time = prev.get("evt_time")
                        last_revs = prev.get("revs")
                        speed = None
                        cadence = None
                        if last_time is not None and last_revs is not None:
                            dt_ticks = (evt_time - last_time) & 0xFFFF
                            d_revs = (revs - last_revs) & 0xFFFF
                            sec = dt_ticks / 1024.0 if dt_ticks > 0 else 0.0
                            if sec > 0 and d_revs >= 0:
                                if device_type == 123 or device_type == 121:  # Speed or combined
                                    # Assume wheel circumference from config if provided
                                    circ = self.config.get("wheel_circumference_m", 2.105)
                                    mps = (d_revs * circ) / sec
                                    speed = mps * 3.6
                                if device_type == 122 or device_type == 121:  # Cadence or combined
                                    cadence = (d_revs / sec) * 60.0
                        parsed = {
                            "type": "bike",
                            "speed": speed,
                            "cadence": cadence,
                            "evt_time": evt_time,
                            "revs": revs,
                            "ts": time.time(),
                        }
                    except Exception:
                        parsed = {"type": "bike", "ts": time.time()}
                elif device_type == 11:
                    try:
                        # Power typically at bytes 7-8
                        power = (data[7] | (data[8] << 8)) if len(data) >= 9 else None
                        parsed = {"type": "power", "power": power, "ts": time.time()}
                    except Exception:
                        parsed = {"type": "power", "ts": time.time()}
                else:
                    parsed = {"type": "unknown", "ts": time.time()}

                # Update device store
                dv = self.device_values.get(device_id, {})
                dv.update(parsed)
                dv["label"] = label
                dv["device_type"] = device_type
                dv["device_id"] = device_id
                self.device_values[device_id] = dv

                # Request channel ID once and persist
                try:
                    res = ch.request_message(Message.ID.RESPONSE_CHANNEL_ID)
                    _, _, id_data = res
                    dev_num = id_data[0] | (id_data[1] << 8)
                    dev_type = id_data[2]
                    trans_type = id_data[3]
                    # If parsed contains common info, include it
                    extra = parse_common_pages(data)
                    self._save_found(dev_num, dev_type, trans_type, extra=extra or None)
                except Exception:
                    pass

                # Update user mapping if HR
                if device_type == 120 and dv.get("hr", 0) > 0:
                    self.last_hr_active_user = self._user_for_hr(device_id)

        ch.on_broadcast_data = on_broadcast
        ch.on_burst_data = on_broadcast
        # Parameters
        ch.set_period(8070 if device_type == 120 else 8086)
        ch.set_search_timeout(30)
        ch.set_rf_freq(57)
        ch.set_id(device_id or 0, device_type, 0)  # 0 = wildcard if not known
        # Prefer extended messages where available
        try:
            ch.enable_extended_messages(True)
        except Exception:
            pass
        ch.open()
        self.channels.append(ch)

    def _open_configured_channels(self):
        # Users and sensors from config
        users = self.config.get("sensor_map", {}).get("users", [])
        wattbike = self.config.get("sensor_map", {}).get("wattbike", {})

        # Open user HR channels
        for user in users:
            name = user.get("name")
            hr_id = user.get("hr_device_id")
            if hr_id:
                self._open_channel(hr_id, 120, f"{name}-HR")
                # initialize user store
                with self.lock:
                    self.user_values.setdefault(
                        name, {"hr": None, "speed": None, "cadence": None, "power": None, "updated": 0}
                    )

        # Open explicit user bike sensors
        for user in users:
            name = user.get("name")
            sp = user.get("speed_device_id")
            cad = user.get("cadence_device_id")
            pow_id = user.get("power_device_id")
            if sp:
                self._open_channel(sp, 123, f"{name}-Speed")
            if cad:
                self._open_channel(cad, 122, f"{name}-Cadence")
            if pow_id:
                self._open_channel(pow_id, 11, f"{name}-Power")

        # Open shared wattbike sensors (optional)
        if wattbike:
            sp = wattbike.get("speed_device_id")
            cad = wattbike.get("cadence_device_id")
            pow_id = wattbike.get("power_device_id")
            if sp:
                self._open_channel(sp, 123, "Wattbike-Speed")
            if cad:
                self._open_channel(cad, 122, "Wattbike-Cadence")
            if pow_id:
                self._open_channel(pow_id, 11, "Wattbike-Power")

    def _user_for_hr(self, hr_device_id: int) -> Optional[str]:
        for user in self.config.get("sensor_map", {}).get("users", []):
            if user.get("hr_device_id") == hr_device_id:
                return user.get("name")
        return None

    def _assign_shared_sensors(self):
        # Assign shared wattbike sensors to the most recently active HR user
        users = self.config.get("sensor_map", {}).get("users", [])
        wattbike = self.config.get("sensor_map", {}).get("wattbike", {})
        if not users or not wattbike:
            return
        target = self.last_hr_active_user
        if not target:
            return
        # Determine sensor device IDs
        sp = wattbike.get("speed_device_id")
        cad = wattbike.get("cadence_device_id")
        pow_id = wattbike.get("power_device_id")
        with self.lock:
            uv = self.user_values.setdefault(
                target, {"hr": None, "speed": None, "cadence": None, "power": None, "updated": 0}
            )
            if sp and sp in self.device_values:
                dv = self.device_values[sp]
                if dv.get("speed") is not None:
                    uv["speed"] = dv.get("speed")
            if cad and cad in self.device_values:
                dv = self.device_values[cad]
                if dv.get("cadence") is not None:
                    uv["cadence"] = dv.get("cadence")
            if pow_id and pow_id in self.device_values:
                dv = self.device_values[pow_id]
                if dv.get("power") is not None:
                    uv["power"] = dv.get("power")
            uv["updated"] = time.time()
            self.user_values[target] = uv

    def run_curses(self, stdscr):
        curses.curs_set(0)
        # Initialize color pairs
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)  # header
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)  # good
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # warning
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)  # error
        stdscr.nodelay(True)
        stdscr.timeout(500)
        # Main loop
        while not self.stop_event.is_set():
            # Handle key press (q to quit)
            try:
                ch = stdscr.getch()
                if ch in (ord("q"), ord("Q")):
                    self.stop_event.set()
                    break
            except Exception:
                pass

            # Assign shared sensors
            self._assign_shared_sensors()

            # Update display
            stdscr.erase()
            stdscr.addstr(0, 0, " ANT+ Live Monitor (q to quit) ", curses.color_pair(1))
            stdscr.addstr(1, 0, time.strftime("Time: %Y-%m-%d %H:%M:%S"))
            # Compute fixed column positions for aligned header and rows
            user_w = 20
            hr_w = 8
            sp_w = 12
            cad_w = 13
            pw_w = 8
            gap = 3
            hr_col = user_w + 1
            sp_col = hr_col + hr_w + gap
            cad_col = sp_col + sp_w + gap
            pw_col = cad_col + cad_w + gap

            # Header with fixed positions (emojis supported)
            stdscr.addstr(3, 0, "User".ljust(user_w))
            stdscr.addstr(3, hr_col, "❤️ HR".rjust(hr_w))
            stdscr.addstr(3, sp_col, "🚴 Speed".rjust(sp_w))
            stdscr.addstr(3, cad_col, "🔁 Cadence".rjust(cad_w))
            stdscr.addstr(3, pw_col, "⚡ Power".rjust(pw_w))
            # Separator spans terminal width
            _, cols = stdscr.getmaxyx()
            stdscr.addstr(4, 0, "-" * max(pw_col + pw_w, cols))

            row = 5
            with self.lock:
                # Update HR-linked values for users
                for user in self.config.get("sensor_map", {}).get("users", []):
                    name = user.get("name", "Unknown")
                    hr_id = user.get("hr_device_id")
                    hr_val = None
                    if hr_id and hr_id in self.device_values:
                        dv = self.device_values[hr_id]
                        hr_val = dv.get("hr")
                        # stamp last active
                        if hr_val:
                            self.last_hr_active_user = name
                            uv = self.user_values.setdefault(
                                name, {"hr": None, "speed": None, "cadence": None, "power": None, "updated": 0}
                            )
                            uv["hr"] = hr_val
                            uv["updated"] = time.time()
                            self.user_values[name] = uv

                # Render table rows
                for name, vals in self.user_values.items():
                    # Prepare name with truncation/ellipsis for long entries
                    if len(name) > user_w:
                        display_name = name[: max(0, user_w - 3)] + "..."
                    else:
                        display_name = name
                    hr = vals.get("hr")
                    sp = vals.get("speed")
                    cad = vals.get("cadence")
                    pw = vals.get("power")
                    hr_s = f"{hr}" if hr is not None else "-"
                    sp_s = f"{sp:.1f}" if sp is not None else "-"
                    cad_s = f"{int(cad)}" if cad is not None else "-"
                    pw_s = f"{int(pw)}" if pw is not None else "-"
                    # Choose colors based on data freshness/values
                    hr_attr = curses.color_pair(2) if hr else curses.color_pair(3)
                    sp_attr = curses.color_pair(2) if sp else curses.color_pair(3)
                    cad_attr = curses.color_pair(2) if cad else curses.color_pair(3)
                    pw_attr = curses.color_pair(2) if pw else curses.color_pair(3)
                    stdscr.addstr(row, 0, display_name.ljust(user_w))
                    stdscr.addstr(row, hr_col, f"{hr_s:>{hr_w}}", hr_attr)
                    stdscr.addstr(row, sp_col, f"{sp_s:>{sp_w}}", sp_attr)
                    stdscr.addstr(row, cad_col, f"{cad_s:>{cad_w}}", cad_attr)
                    stdscr.addstr(row, pw_col, f"{pw_s:>{pw_w}}", pw_attr)
                    row += 1

            stdscr.refresh()
            time.sleep(0.5)

    def run(self):
        self.start()

        # Install clean shutdown
        def _handle(sig, frame):
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, _handle)
        signal.signal(signal.SIGTERM, _handle)
        curses.wrapper(self.run_curses)
        self.stop()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="ANT+ Live Monitor")
    parser.add_argument("--config", type=str, default="config/sensor_map.yaml", help="Sensor map config file")
    parser.add_argument("--save", type=str, default="found_devices.json", help="File to persist found devices")
    parser.add_argument("--debug", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    configure_logging(args.debug)
    mon = LiveMonitor(args.config, args.save, debug=args.debug)
    mon.run()


if __name__ == "__main__":
    main()
