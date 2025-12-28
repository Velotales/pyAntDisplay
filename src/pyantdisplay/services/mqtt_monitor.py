#!/usr/bin/env python3
"""
PyANTDisplay - MQTT Monitor

Copyright (c) 2025 Velotales

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

MQTT publishing monitor for Home Assistant integration.
"""

import json
import logging
import sys
import threading
import time
from typing import Dict, List, Optional

import yaml
from colorama import Fore, Style

from ..utils.common import deep_merge_save, load_manufacturers, parse_common_pages

try:
    from openant.easy.channel import Channel
    from openant.easy.node import Message, Node
except ImportError:
    print("openant is not installed. Run ./setup.sh first.")
    sys.exit(1)

try:
    import paho.mqtt.client as mqtt
except ImportError:
    mqtt = None

ANT_PLUS_NETWORK_KEY = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]


def configure_logging(debug: bool):
    logging.basicConfig(
        level=(logging.DEBUG if debug else logging.INFO),
        format="[%(levelname)s] %(name)s: %(message)s",
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


class MqttMonitor:
    def __init__(
        self,
        sensor_config_path: str,
        save_path: str,
        app_config_path: Optional[str] = None,
        local_app_config_path: Optional[str] = None,
        debug: bool = False,
    ):
        self.sensor_config_path = sensor_config_path
        self.save_path = save_path
        self.app_config_path = app_config_path or "config/config.yaml"
        self.local_app_config_path = local_app_config_path
        self.debug = debug
        self.sensor_config = self._load_yaml(self.sensor_config_path)
        self.app_config = self._merge_yaml(
            self.app_config_path, self.local_app_config_path
        )
        self.node: Optional[Node] = None
        self.loop_thread: Optional[threading.Thread] = None
        self.channels: List[Channel] = []

        # Device and user state
        self.lock = threading.Lock()
        self.device_values: Dict[int, Dict] = {}
        self.user_values: Dict[str, Dict] = {}
        self.last_hr_active_user: Optional[str] = None
        self.stop_event = threading.Event()
        self.last_save_times: Dict[str, float] = {}
        self.last_published_values: Dict[
            str, Dict[str, Optional[float]]
        ] = {}  # Track last published values
        self.last_availability: Dict[str, bool] = {}  # Track last availability state
        self.manufacturer_map: Dict[int, str] = load_manufacturers()

        # MQTT config
        mqtt_cfg = (
            self.app_config.get("mqtt", {}) if isinstance(self.app_config, dict) else {}
        )
        self.mqtt_host = mqtt_cfg.get("host", "localhost")
        self.mqtt_port = int(mqtt_cfg.get("port", 1883))
        self.mqtt_username = mqtt_cfg.get("username")
        self.mqtt_password = mqtt_cfg.get("password")
        self.base_topic = mqtt_cfg.get("base_topic", "pyantdisplay")
        self.qos = int(mqtt_cfg.get("qos", 1))
        self.retain = bool(mqtt_cfg.get("retain", True))
        self.stale_secs = int(mqtt_cfg.get("stale_secs", 10))
        self.client_id = mqtt_cfg.get("client_id", "pyantdisplay-mqtt")
        self.discovery_enabled = bool(mqtt_cfg.get("discovery", True))
        self.discovery_prefix = str(mqtt_cfg.get("discovery_prefix", "homeassistant"))
        self.mqtt_client = None

    def _load_yaml(self, path: str) -> dict:
        try:
            with open(path, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def _merge_yaml(self, base_path: str, local_path: Optional[str]) -> dict:
        base = self._load_yaml(base_path)
        if local_path:
            try:
                with open(local_path, "r") as f:
                    local = yaml.safe_load(f) or {}

                # shallow merge is sufficient for our config structure
                def _deep(a, b):
                    out = dict(a)
                    for k, v in (b or {}).items():
                        if isinstance(v, dict) and isinstance(out.get(k), dict):
                            out[k] = _deep(out[k], v)
                        else:
                            out[k] = v
                    return out

                base = _deep(base, local)
            except Exception:
                pass
        return base

    def _connect_mqtt(self):
        if mqtt is None:
            print(
                f"{Fore.RED}paho-mqtt not installed; cannot run MQTT mode{Style.RESET_ALL}"
            )
            sys.exit(1)
        self.mqtt_client = mqtt.Client(client_id=self.client_id, clean_session=True)
        if self.mqtt_username:
            self.mqtt_client.username_pw_set(self.mqtt_username, self.mqtt_password)
        logging.info(f"Connecting to MQTT broker {self.mqtt_host}:{self.mqtt_port}")
        self.mqtt_client.connect(self.mqtt_host, self.mqtt_port, keepalive=30)
        self.mqtt_client.loop_start()
        logging.info("MQTT connected")

    def _publish(self, topic: str, payload: str):
        full = f"{self.base_topic}/{topic}"
        try:
            self.mqtt_client.publish(
                full, payload=payload, qos=self.qos, retain=self.retain
            )
        except Exception:
            pass

    def _publish_discovery_for_user(self, user: str):
        if not self.discovery_enabled:
            return

        # Find user configuration to determine which devices they have
        user_config = None
        for u in self.sensor_config.get("sensor_map", {}).get("users", []):
            if u.get("name") == user:
                user_config = u
                break

        if not user_config:
            return

        # Common device block
        device = {
            "identifiers": [f"pyantdisplay_user_{user}"],
            "manufacturer": "PyANTDisplay",
            "model": "ANT+ Monitor",
            "name": f"PyANTDisplay {user}",
        }

        # Only create entities for configured devices
        entities = []

        # HR - check for hr_device_ids or hr_device_id (old format)
        hr_ids = user_config.get("hr_device_ids", [])
        if not hr_ids:  # Fallback to old format
            old_hr_id = user_config.get("hr_device_id")
            if old_hr_id:
                hr_ids = [old_hr_id]
        if hr_ids:
            entities.append(
                {
                    "metric": "hr",
                    "name": f"{user} Heart Rate",
                    "unit": "bpm",
                    "state_class": "measurement",
                    "icon": "mdi:heart",
                }
            )

        # Speed
        if user_config.get("speed_device_id"):
            entities.append(
                {
                    "metric": "speed",
                    "name": f"{user} Speed",
                    "unit": "km/h",
                    "state_class": "measurement",
                    "icon": "mdi:speedometer",
                }
            )

        # Cadence
        if user_config.get("cadence_device_id"):
            entities.append(
                {
                    "metric": "cadence",
                    "name": f"{user} Cadence",
                    "unit": "rpm",
                    "state_class": "measurement",
                    "icon": "mdi:timer-sync",
                }
            )

        # Power
        if user_config.get("power_device_id"):
            entities.append(
                {
                    "metric": "power",
                    "name": f"{user} Power",
                    "unit": "W",
                    "device_class": "power",
                    "state_class": "measurement",
                    "icon": "mdi:flash",
                }
            )
        for ent in entities:
            obj_id = f"pyantdisplay_{user}_{ent['metric']}"
            state_topic = f"{self.base_topic}/users/{user}/{ent['metric']}"
            avail_topic = f"{self.base_topic}/users/{user}/availability"
            payload = {
                "name": ent["name"],
                "unique_id": obj_id,
                "state_topic": state_topic,
                "availability_topic": avail_topic,
                "payload_available": "online",
                "payload_not_available": "offline",
                "qos": self.qos,
                "device": device,
                "retain": self.retain,
                "unit_of_measurement": ent["unit"],
                "icon": ent.get("icon"),
            }
            if ent.get("device_class"):
                payload["device_class"] = ent["device_class"]
            if ent.get("state_class"):
                payload["state_class"] = ent["state_class"]
            topic = f"{self.discovery_prefix}/sensor/{obj_id}/config"
            try:
                self.mqtt_client.publish(
                    topic, payload=json.dumps(payload), qos=1, retain=True
                )
                logging.info(f"Published HA discovery for '{user}' {ent['metric']}")
            except Exception:
                pass

    def _availability(self, user: str, online: bool):
        # Only publish availability changes
        if self.last_availability.get(user) != online:
            state = "online" if online else "offline"
            # Use retain=True for availability so HA gets state after restart
            try:
                full = f"{self.base_topic}/users/{user}/availability"
                self.mqtt_client.publish(full, payload=state, qos=self.qos, retain=True)
                logging.info(f"Availability for '{user}': {state}")
                self.last_availability[user] = online
            except Exception:
                pass

    def _publish_user_metrics(self, user: str, vals: Dict[str, Optional[float]]):
        # Only publish values that have changed
        last_vals = self.last_published_values.get(user, {})

        # Check each metric for changes
        if vals.get("hr") is not None and vals.get("hr") != last_vals.get("hr"):
            self._publish(f"users/{user}/hr", str(int(vals["hr"])))
            logging.info(f"Published HR update for user '{user}'")

        if vals.get("speed") is not None and vals.get("speed") != last_vals.get(
            "speed"
        ):
            self._publish(f"users/{user}/speed", f"{float(vals['speed']):.2f}")
            logging.info(f"Published speed update for user '{user}'")

        if vals.get("cadence") is not None and vals.get("cadence") != last_vals.get(
            "cadence"
        ):
            self._publish(f"users/{user}/cadence", str(int(vals["cadence"])))
            logging.info(f"Published cadence update for user '{user}'")

        if vals.get("power") is not None and vals.get("power") != last_vals.get(
            "power"
        ):
            self._publish(f"users/{user}/power", str(int(vals["power"])))
            logging.info(f"Published power update for user '{user}'")

        # Update last published values
        self.last_published_values[user] = {
            "hr": vals.get("hr"),
            "speed": vals.get("speed"),
            "cadence": vals.get("cadence"),
            "power": vals.get("power"),
        }

    def start(self):
        # MQTT first
        self._connect_mqtt()
        # Start node
        self.node = Node()
        self.loop_thread = threading.Thread(
            target=self.node.start, name="openant.easy.main", daemon=True
        )
        self.loop_thread.start()
        # Set network key
        self.node.set_network_key(0, ANT_PLUS_NETWORK_KEY)
        # Open channels per config
        self._open_configured_channels()
        # Publish discovery for known users
        try:
            for user in self.sensor_config.get("sensor_map", {}).get("users", []):
                name = user.get("name")
                if name:
                    self._publish_discovery_for_user(name)
        except Exception:
            pass

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
            if self.mqtt_client:
                try:
                    # Mark users offline
                    for user in list(self.user_values.keys()):
                        self._availability(user, False)
                    self.mqtt_client.loop_stop()
                    self.mqtt_client.disconnect()
                except Exception:
                    pass
        logging.info("MQTT monitor stopped")

    def _open_channel(self, device_id: int, device_type: int, label: str):
        ch = self.node.new_channel(Channel.Type.BIDIRECTIONAL_RECEIVE)

        def on_broadcast(data):
            with self.lock:
                parsed = None
                if device_type == 120:
                    try:
                        hr = data[7]
                        parsed = {"type": "hr", "hr": hr, "ts": time.time()}
                    except Exception:
                        parsed = {"type": "hr", "ts": time.time()}
                elif device_type in (121, 123, 122):
                    try:
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
                                circ = self.sensor_config.get(
                                    "wheel_circumference_m", 2.105
                                )
                                if device_type == 123 or device_type == 121:
                                    mps = (d_revs * circ) / sec
                                    speed = mps * 3.6
                                if device_type == 122 or device_type == 121:
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
                        power = (data[7] | (data[8] << 8)) if len(data) >= 9 else None
                        parsed = {"type": "power", "power": power, "ts": time.time()}
                    except Exception:
                        parsed = {"type": "power", "ts": time.time()}
                else:
                    parsed = {"type": "unknown", "ts": time.time()}

                dv = self.device_values.get(device_id, {})
                first = not dv
                dv.update(parsed)
                dv["label"] = label
                dv["device_type"] = device_type
                dv["device_id"] = device_id
                self.device_values[device_id] = dv

                # First data event
                if first:
                    logging.info(
                        f"First data received for device '{label}' (ID={device_id}, type={device_type})"
                    )

                # Request channel ID once and persist
                try:
                    res = ch.request_message(Message.ID.RESPONSE_CHANNEL_ID)
                    _, _, id_data = res
                    dev_num = id_data[0] | (id_data[1] << 8)
                    dev_type = id_data[2]
                    trans_type = id_data[3]
                    extra = parse_common_pages(data)
                    deep_merge_save(
                        self.save_path,
                        dev_num,
                        dev_type,
                        trans_type,
                        base_extra=extra or None,
                        manufacturers=self.manufacturer_map,
                        rate_limit_secs=30,
                        last_save_times=self.last_save_times,
                    )
                except Exception:
                    pass

                # Update HR active user
                if device_type == 120 and dv.get("hr", 0):
                    self.last_hr_active_user = self._user_for_hr(device_id)
                    if self.last_hr_active_user:
                        self._availability(self.last_hr_active_user, True)
                        logging.info(f"Active HR user: {self.last_hr_active_user}")

        ch.on_broadcast_data = on_broadcast
        ch.on_burst_data = on_broadcast
        ch.set_period(8070 if device_type == 120 else 8086)
        ch.set_search_timeout(30)
        ch.set_rf_freq(57)
        ch.set_id(device_id or 0, device_type, 0)
        try:
            ch.enable_extended_messages(True)
        except Exception:
            pass
        ch.open()
        logging.info(f"Opened channel '{label}' (ID={device_id}, type={device_type})")
        self.channels.append(ch)

    def _open_configured_channels(self):
        users = self.sensor_config.get("sensor_map", {}).get("users", [])
        wattbike = self.sensor_config.get("sensor_map", {}).get("wattbike", {})

        for user in users:
            name = user.get("name")
            # Support both old single hr_device_id and new hr_device_ids list
            hr_ids = user.get("hr_device_ids", [])
            if not hr_ids:  # Fallback to old format
                old_hr_id = user.get("hr_device_id")
                if old_hr_id:
                    hr_ids = [old_hr_id]

            # Open channels for all HR devices assigned to this user
            for i, hr_id in enumerate(hr_ids):
                if hr_id:
                    self._open_channel(
                        hr_id, 120, f"{name}-HR{i+1 if len(hr_ids) > 1 else ''}"
                    )

            # Initialize user store if they have any HR devices
            if hr_ids:
                with self.lock:
                    self.user_values.setdefault(
                        name,
                        {
                            "hr": None,
                            "speed": None,
                            "cadence": None,
                            "power": None,
                            "updated": 0,
                        },
                    )
                    self._availability(name, False)

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
        for user in self.sensor_config.get("sensor_map", {}).get("users", []):
            # Support both old single hr_device_id and new hr_device_ids list
            hr_ids = user.get("hr_device_ids", [])
            if not hr_ids:  # Fallback to old format
                old_hr_id = user.get("hr_device_id")
                if old_hr_id:
                    hr_ids = [old_hr_id]

            if hr_device_id in hr_ids:
                return user.get("name")
        return None

    def _assign_shared_sensors(self):
        users = self.sensor_config.get("sensor_map", {}).get("users", [])

        # Process heart rate data for all users
        for user in users:
            name = user.get("name")
            if not name:
                continue

            # Support both old single hr_device_id and new hr_device_ids list
            hr_ids = user.get("hr_device_ids", [])
            if not hr_ids:  # Fallback to old format
                old_hr_id = user.get("hr_device_id")
                if old_hr_id:
                    hr_ids = [old_hr_id]

            # Check for active HR devices for this user
            hr_value = None
            for hr_id in hr_ids:
                if hr_id in self.device_values:
                    dv = self.device_values[hr_id]
                    if dv.get("hr") is not None:
                        hr_value = dv.get("hr")
                        break  # Use first active HR device

            # Update user values if we have HR data
            if hr_value is not None:
                with self.lock:
                    uv = self.user_values.setdefault(
                        name,
                        {
                            "hr": None,
                            "speed": None,
                            "cadence": None,
                            "power": None,
                            "updated": 0,
                        },
                    )
                    uv["hr"] = hr_value
                    uv["updated"] = time.time()

                    # Also handle individual bike sensors for this user
                    if (
                        user.get("speed_device_id")
                        and user.get("speed_device_id") in self.device_values
                    ):
                        dv = self.device_values[user.get("speed_device_id")]
                        if dv.get("speed") is not None:
                            uv["speed"] = dv.get("speed")

                    if (
                        user.get("cadence_device_id")
                        and user.get("cadence_device_id") in self.device_values
                    ):
                        dv = self.device_values[user.get("cadence_device_id")]
                        if dv.get("cadence") is not None:
                            uv["cadence"] = dv.get("cadence")

                    if (
                        user.get("power_device_id")
                        and user.get("power_device_id") in self.device_values
                    ):
                        dv = self.device_values[user.get("power_device_id")]
                        if dv.get("power") is not None:
                            uv["power"] = dv.get("power")

        # Handle shared wattbike sensors (existing functionality)
        wattbike = self.sensor_config.get("sensor_map", {}).get("wattbike", {})
        if not users or not wattbike:
            return
        target = self.last_hr_active_user
        if not target:
            return
        sp = wattbike.get("speed_device_id")
        cad = wattbike.get("cadence_device_id")
        pow_id = wattbike.get("power_device_id")
        with self.lock:
            uv = self.user_values.setdefault(
                target,
                {
                    "hr": None,
                    "speed": None,
                    "cadence": None,
                    "power": None,
                    "updated": 0,
                },
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

    def run(self):
        configure_logging(self.debug)
        self.start()
        logging.info("MQTT live monitor started")
        try:
            while not self.stop_event.is_set():
                # Shared sensors assignment and publish
                self._assign_shared_sensors()
                with self.lock:
                    for name, vals in self.user_values.items():
                        updated = vals.get("updated", 0)
                        if updated:
                            self._publish_user_metrics(name, vals)
                            self._availability(name, True)
                        # Offline detection
                        if (time.time() - updated) > self.stale_secs:
                            self._availability(name, False)
                time.sleep(0.5)
        except KeyboardInterrupt:
            logging.info("Interrupted")
        finally:
            self.stop()
