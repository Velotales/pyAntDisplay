#!/usr/bin/env python3
"""
PyANTDisplay - Single Entry Point

Run different behaviors based on CLI flags or config without installing.

Examples:
  python -m pyantdisplay --mode menu
  python -m pyantdisplay --mode monitor --config config/sensor_map.yaml --save found_devices.json
  python -m pyantdisplay --mode scan --app-config config/config.yaml
  python -m pyantdisplay --mode list --app-config config/config.yaml
"""

import argparse
import json
import time
from typing import Any, Dict, Optional

try:
    import yaml  # type: ignore
except Exception:
    yaml = None

from colorama import Fore, Style

from .device_scanner import DeviceScanner
from .live_monitor import ANT_PLUS_NETWORK_KEY, LiveMonitor
from .main import ANTPlusDisplay
from .mqtt_monitor import MqttMonitor


def _deep_merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries."""
    out = dict(a)
    for k, v in (b or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def _load_app_config(app_config: str, local_config: Optional[str] = None) -> Dict[str, Any]:
    """Load application configuration with optional local overrides."""
    if yaml is None:
        print(f"{Fore.RED}PyYAML not available, using empty config{Style.RESET_ALL}")
        return {}

    # Load base config
    try:
        with open(app_config, "r") as f:
            base = yaml.safe_load(f) or {}
    except Exception:
        base = {}

    # Merge local config if provided
    if local_config:
        try:
            with open(local_config, "r") as f:
                local = yaml.safe_load(f) or {}
            base = _deep_merge(base, local)
        except Exception:
            pass

    return base


def run_menu(app_config: Optional[str] = None, local_config: Optional[str] = None):
    """Run the interactive menu mode."""
    cfg_path = local_config or (app_config or "config/config.yaml")
    app = ANTPlusDisplay(config_file=cfg_path)
    app.check_usb_on_startup()
    try:
        app.show_menu()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Application interrupted{Style.RESET_ALL}")
    finally:
        app.stop()


def run_scan(app_config: str, local_config: Optional[str] = None, debug: bool = False):
    """Run device scanning mode."""
    cfg = _load_app_config(app_config, local_config)
    key = cfg.get("ant_network", {}).get("key", ANT_PLUS_NETWORK_KEY)
    timeout = cfg.get("app", {}).get("scan_timeout", 30)
    backend_pref = cfg.get("app", {}).get("backend", None)
    save_path = cfg.get("app", {}).get("found_devices_file", "found_devices.json")

    print(f"{Fore.CYAN}ANT+ Device Scanner{Style.RESET_ALL}")
    scanner = DeviceScanner(key, scan_timeout=timeout, debug=debug, backend_preference=backend_pref)
    devices = scanner.scan_for_devices()
    scanner.save_found_devices(save_path)
    print(f"{Fore.GREEN}Saved {len(devices)} devices to {save_path}{Style.RESET_ALL}")


def run_list(app_config: str, local_config: Optional[str] = None):
    """List discovered devices."""
    cfg = _load_app_config(app_config, local_config)
    save_path = cfg.get("app", {}).get("found_devices_file", "found_devices.json")

    try:
        with open(save_path, "r") as f:
            devices = json.load(f)
    except FileNotFoundError:
        print(f"{Fore.YELLOW}No device file found: {save_path}{Style.RESET_ALL}")
        return
    except Exception as e:
        print(f"{Fore.RED}Error reading {save_path}: {e}{Style.RESET_ALL}")
        return

    if not devices:
        print(f"{Fore.YELLOW}No devices in {save_path}{Style.RESET_ALL}")
        return

    print(f"\n{Fore.CYAN}Found ANT+ Devices ({len(devices)}){Style.RESET_ALL}")
    print(f"{'ID':<8} {'Type':<6} {'Key':<15} {'Last Seen':<20}")
    print("-" * 60)
    for k, v in devices.items():
        last = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(v.get("last_seen", 0)))
        print(f"{v.get('device_id', '-'):<8} {v.get('device_type', '-'):<6} {k:<15} {last:<20}")


def run_monitor(sensor_config: str, save_path: str, debug: bool = False):
    """Run live monitoring mode with curses dashboard."""
    mon = LiveMonitor(sensor_config, save_path, debug=debug)
    mon.run()


def run_mqtt(
    sensor_config: str, save_path: str, app_config: str, local_config: Optional[str] = None, debug: bool = False
):
    """Run MQTT publishing mode."""
    mon = MqttMonitor(
        sensor_config_path=sensor_config,
        save_path=save_path,
        app_config_path=app_config,
        local_app_config_path=local_config,
        debug=debug,
    )
    mon.run()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="PyANTDisplay entry point")
    parser.add_argument(
        "--mode", choices=["menu", "monitor", "scan", "list", "mqtt"], default="menu", help="Program mode"
    )
    parser.add_argument(
        "--config", type=str, default="config/sensor_map.yaml", help="Sensor map config for monitor/mqtt mode"
    )
    parser.add_argument(
        "--save", type=str, default="found_devices.json", help="Device persistence file for monitor/mqtt mode"
    )
    parser.add_argument(
        "--app-config", type=str, default="config/config.yaml", help="App config for scan/list/menu modes"
    )
    parser.add_argument(
        "--local-config", type=str, default=None, help="Optional local app config that overrides base config"
    )
    parser.add_argument("--debug", action="store_true", help="Enable verbose logging where supported")
    args = parser.parse_args()

    if args.mode == "menu":
        run_menu(args.app_config, args.local_config)
    elif args.mode == "monitor":
        run_monitor(args.config, args.save, debug=args.debug)
    elif args.mode == "scan":
        run_scan(args.app_config, args.local_config, debug=args.debug)
    elif args.mode == "list":
        run_list(args.app_config, args.local_config)
    elif args.mode == "mqtt":
        run_mqtt(args.config, args.save, args.app_config, args.local_config, debug=args.debug)


if __name__ == "__main__":
    main()
