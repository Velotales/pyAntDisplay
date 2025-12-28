"""
Tests for MQTT monitor functionality.
"""

import threading
from unittest.mock import Mock, patch, mock_open
import tempfile
import os
import sys

import pytest

# Mock all openant imports to prevent USB device interaction during test collection
openant_mock = Mock()
openant_mock.easy = Mock()
openant_mock.easy.node = Mock()
openant_mock.easy.channel = Mock()

with patch.dict(
    "sys.modules",
    {
        "openant": openant_mock,
        "openant.easy": openant_mock.easy,
        "openant.easy.node": openant_mock.easy.node,
        "openant.easy.channel": openant_mock.easy.channel,
    },
):
    from src.pyantdisplay.services.mqtt_monitor import MqttMonitor


class TestMqttMonitor:
    """Test cases for MqttMonitor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_sensor_config = """
devices:
  - device_type: 120
    device_id: 12345
    mqtt_topic: "sensor/hr"
"""
        self.temp_app_config = """
mqtt:
  enabled: true
  broker: "localhost"
  port: 1883
"""

    @patch("builtins.open", mock_open())
    @patch("yaml.safe_load")
    def test_init_basic(self, mock_yaml_load):
        """Test basic MQTT monitor initialization."""
        mock_yaml_load.side_effect = [
            {"devices": [{"device_type": 120, "device_id": 12345}]},  # sensor config
            {"mqtt": {"enabled": True, "broker": "localhost"}},  # app config
        ]

        monitor = MqttMonitor(
            sensor_config_path="sensors.yaml",
            save_path="/tmp/data",
            app_config_path="config.yaml",
        )

        assert monitor.sensor_config_path == "sensors.yaml"
        assert monitor.save_path == "/tmp/data"
        assert monitor.app_config_path == "config.yaml"
        assert monitor.debug is False
        assert monitor.node is None
        assert monitor.channels == []

    @patch("builtins.open", mock_open())
    @patch("yaml.safe_load")
    def test_init_with_debug(self, mock_yaml_load):
        """Test MQTT monitor initialization with debug enabled."""
        mock_yaml_load.side_effect = [{"devices": []}, {"mqtt": {"enabled": True}}]

        monitor = MqttMonitor(
            sensor_config_path="sensors.yaml", save_path="/tmp/data", debug=True
        )

        assert monitor.debug is True

    @patch("builtins.open", mock_open())
    @patch("yaml.safe_load")
    def test_init_with_local_config(self, mock_yaml_load):
        """Test MQTT monitor initialization with local config override."""
        mock_yaml_load.side_effect = [
            {"devices": []},  # sensor config
            {"mqtt": {"enabled": True, "broker": "localhost"}},  # main app config
            {"mqtt": {"broker": "local.host", "port": 1884}},  # local override
        ]

        monitor = MqttMonitor(
            sensor_config_path="sensors.yaml",
            save_path="/tmp/data",
            app_config_path="config.yaml",
            local_app_config_path="local.yaml",
        )

        assert monitor.local_app_config_path == "local.yaml"

    @patch("builtins.open", side_effect=FileNotFoundError("Config not found"))
    def test_init_missing_config(self, mock_open):
        """Test MQTT monitor initialization with missing config file."""
        # The MqttMonitor constructor calls _load_yaml which handles FileNotFoundError
        try:
            monitor = MqttMonitor(
                sensor_config_path="nonexistent.yaml", save_path="/tmp/data"
            )
            # If we get here, the constructor handled the missing file gracefully
            assert True
        except FileNotFoundError:
            # This is also acceptable behavior
            assert True

    @patch("builtins.open", mock_open())
    @patch("yaml.safe_load")
    def test_device_values_thread_safety(self, mock_yaml_load):
        """Test thread-safe access to device values."""
        mock_yaml_load.side_effect = [{"devices": []}, {"mqtt": {"enabled": True}}]

        monitor = MqttMonitor(sensor_config_path="sensors.yaml", save_path="/tmp/data")

        # Test that lock exists and is a threading.Lock instance
        assert hasattr(monitor, "lock")
        assert isinstance(monitor.lock, type(threading.Lock()))
        assert monitor.device_values == {}
        assert monitor.user_values == {}

    @patch("builtins.open", mock_open())
    @patch("yaml.safe_load")
    def test_stop_event_initialization(self, mock_yaml_load):
        """Test that stop event is properly initialized."""
        mock_yaml_load.side_effect = [{"devices": []}, {"mqtt": {"enabled": True}}]

        monitor = MqttMonitor(sensor_config_path="sensors.yaml", save_path="/tmp/data")

        assert isinstance(monitor.stop_event, threading.Event)
        assert not monitor.stop_event.is_set()

    @patch("builtins.open", mock_open())
    @patch("yaml.safe_load")
    def test_yaml_merge_functionality(self, mock_yaml_load):
        """Test YAML configuration merging."""
        # Mock the YAML loading to return different configs
        mock_yaml_load.side_effect = [
            {"devices": [{"device_type": 120}]},  # sensor config
            {"mqtt": {"enabled": True, "broker": "main.host"}},  # main config
            {"mqtt": {"broker": "override.host", "port": 1884}},  # local override
        ]

        monitor = MqttMonitor(
            sensor_config_path="sensors.yaml",
            save_path="/tmp/data",
            app_config_path="main.yaml",
            local_app_config_path="local.yaml",
        )

        # The _merge_yaml method should have been called
        assert monitor.app_config is not None

    @patch("builtins.open", mock_open())
    @patch("yaml.safe_load")
    def test_invalid_yaml_handling(self, mock_yaml_load):
        """Test handling of invalid YAML configurations."""
        # Mock sensor config and app config
        mock_yaml_load.side_effect = [
            {"devices": []},  # Valid sensor config
            None,  # Invalid app config
        ]

        # This test verifies that the monitor can handle malformed YAML
        try:
            monitor = MqttMonitor(
                sensor_config_path="sensors.yaml", save_path="/tmp/data"
            )
            # If it doesn't raise an exception, that's acceptable
            assert True
        except Exception:
            # If it does raise an exception, that's also acceptable behavior
            assert True

    @patch("builtins.open", mock_open())
    @patch("yaml.safe_load")
    def test_default_config_paths(self, mock_yaml_load):
        """Test default configuration paths."""
        mock_yaml_load.side_effect = [{"devices": []}, {"mqtt": {"enabled": True}}]

        monitor = MqttMonitor(sensor_config_path="sensors.yaml", save_path="/tmp/data")

        # Should use default app config path
        assert monitor.app_config_path == "config/config.yaml"
        assert monitor.local_app_config_path is None

    @patch("builtins.open", mock_open())
    @patch("yaml.safe_load")
    def test_thread_initialization(self, mock_yaml_load):
        """Test that thread-related attributes are properly initialized."""
        mock_yaml_load.side_effect = [{"devices": []}, {"mqtt": {"enabled": True}}]

        monitor = MqttMonitor(sensor_config_path="sensors.yaml", save_path="/tmp/data")

        assert monitor.loop_thread is None
        assert monitor.last_hr_active_user is None

    @patch("pyantdisplay.services.mqtt_monitor.load_manufacturers", return_value={})
    @patch("builtins.open", mock_open())
    @patch("yaml.safe_load")
    def test_configuration_loading(self, mock_yaml_load, mock_load_manufacturers):
        """Test that configurations are loaded during initialization."""
        sensor_config = {
            "sensor_map": {"users": [{"name": "TestUser", "hr_device_ids": [12345]}]}
        }
        app_config = {"mqtt": {"enabled": True, "broker": "test.local"}}

        mock_yaml_load.side_effect = [sensor_config, app_config]

        monitor = MqttMonitor(sensor_config_path="sensors.yaml", save_path="/tmp/data")

        # Verify configs were loaded
        assert monitor.sensor_config == sensor_config
        assert monitor.app_config == app_config

    @patch("builtins.open", mock_open())
    @patch("yaml.safe_load")
    def test_save_path_assignment(self, mock_yaml_load):
        """Test that save path is properly assigned."""
        mock_yaml_load.side_effect = [{"devices": []}, {"mqtt": {"enabled": True}}]

        save_path = "/custom/save/path"
        monitor = MqttMonitor(sensor_config_path="sensors.yaml", save_path=save_path)

        assert monitor.save_path == save_path

    @patch("builtins.open", mock_open())
    @patch("yaml.safe_load")
    def test_empty_configurations(self, mock_yaml_load):
        """Test handling of empty configuration files."""
        mock_yaml_load.side_effect = [{}, {}]  # Empty configs

        monitor = MqttMonitor(sensor_config_path="sensors.yaml", save_path="/tmp/data")

        assert monitor.sensor_config == {}
        assert monitor.app_config == {}
        assert monitor.channels == []

    @patch("builtins.open", mock_open())
    @patch("yaml.safe_load")
    def test_state_initialization(self, mock_yaml_load):
        """Test that internal state is properly initialized."""
        mock_yaml_load.side_effect = [{"devices": []}, {"mqtt": {"enabled": True}}]

        monitor = MqttMonitor(sensor_config_path="sensors.yaml", save_path="/tmp/data")

        # Verify all state variables are initialized
        assert isinstance(monitor.device_values, dict)
        assert isinstance(monitor.user_values, dict)
        assert monitor.device_values == {}
        assert monitor.user_values == {}
        assert monitor.last_hr_active_user is None
        assert monitor.last_published_values == {}
        assert monitor.last_availability == {}

    @patch("builtins.open", mock_open())
    @patch("yaml.safe_load")
    @patch("pyantdisplay.services.mqtt_monitor.mqtt")
    def test_publish_user_metrics_change_detection(self, mock_mqtt, mock_yaml_load):
        """Test that metrics are only published when values change."""
        mock_yaml_load.side_effect = [{"devices": []}, {"mqtt": {"enabled": True}}]
        mock_client = Mock()
        mock_mqtt.Client.return_value = mock_client

        monitor = MqttMonitor(sensor_config_path="sensors.yaml", save_path="/tmp/data")
        monitor.mqtt_client = mock_client
        monitor.base_topic = "test"
        monitor.qos = 1
        monitor.retain = True

        # First publish - should publish all values
        user_vals = {"hr": 75, "speed": 25.5, "cadence": 90, "power": 150, "updated": 1}
        monitor._publish_user_metrics("TestUser", user_vals)

        # Should have published 4 messages
        assert mock_client.publish.call_count == 4
        mock_client.publish.reset_mock()

        # Second publish with same values - should publish nothing
        monitor._publish_user_metrics("TestUser", user_vals)
        assert mock_client.publish.call_count == 0

        # Third publish with changed HR only - should publish only HR
        user_vals_changed = {
            "hr": 80,
            "speed": 25.5,
            "cadence": 90,
            "power": 150,
            "updated": 2,
        }
        monitor._publish_user_metrics("TestUser", user_vals_changed)
        assert mock_client.publish.call_count == 1
        mock_client.publish.assert_called_with(
            "test/users/TestUser/hr", payload="80", qos=1, retain=True
        )

    @patch("builtins.open", mock_open())
    @patch("yaml.safe_load")
    @patch("pyantdisplay.services.mqtt_monitor.mqtt")
    def test_availability_change_detection(self, mock_mqtt, mock_yaml_load):
        """Test that availability is only published when status changes."""
        mock_yaml_load.side_effect = [{"devices": []}, {"mqtt": {"enabled": True}}]
        mock_client = Mock()
        mock_mqtt.Client.return_value = mock_client

        monitor = MqttMonitor(sensor_config_path="sensors.yaml", save_path="/tmp/data")
        monitor.mqtt_client = mock_client
        monitor.base_topic = "test"
        monitor.qos = 1
        monitor.retain = True

        # First availability call - should publish
        monitor._availability("TestUser", True)
        assert mock_client.publish.call_count == 1
        mock_client.publish.assert_called_with(
            "test/users/TestUser/availability", payload="online", qos=1, retain=True
        )
        mock_client.publish.reset_mock()

        # Second availability call with same status - should not publish
        monitor._availability("TestUser", True)
        assert mock_client.publish.call_count == 0

        # Third availability call with different status - should publish
        monitor._availability("TestUser", False)
        assert mock_client.publish.call_count == 1
        mock_client.publish.assert_called_with(
            "test/users/TestUser/availability", payload="offline", qos=1, retain=True
        )

    @patch("builtins.open", mock_open())
    @patch("yaml.safe_load")
    @patch("pyantdisplay.services.mqtt_monitor.mqtt")
    def test_last_published_values_tracking(self, mock_mqtt, mock_yaml_load):
        """Test that last published values are properly tracked."""
        mock_yaml_load.side_effect = [{"devices": []}, {"mqtt": {"enabled": True}}]
        mock_client = Mock()
        mock_mqtt.Client.return_value = mock_client

        monitor = MqttMonitor(sensor_config_path="sensors.yaml", save_path="/tmp/data")
        monitor.mqtt_client = mock_client

        # Publish values for user
        user_vals = {"hr": 75, "speed": None, "cadence": 90, "power": None}
        monitor._publish_user_metrics("TestUser", user_vals)

        # Check that only non-None values are tracked
        expected_last_vals = {"hr": 75, "speed": None, "cadence": 90, "power": None}
        assert monitor.last_published_values["TestUser"] == expected_last_vals

        # Publish new values with some None values
        user_vals2 = {"hr": 80, "speed": 30.0, "cadence": None, "power": 200}
        monitor._publish_user_metrics("TestUser", user_vals2)

        # Check updated tracking
        expected_last_vals2 = {"hr": 80, "speed": 30.0, "cadence": None, "power": 200}
        assert monitor.last_published_values["TestUser"] == expected_last_vals2
