"""
Tests for device manager functionality.
"""

import sys
from unittest.mock import Mock, MagicMock, patch

import pytest

# Mock openant modules at import time to prevent USB device access
sys.modules['openant'] = MagicMock()
sys.modules['openant.easy'] = MagicMock()
sys.modules['openant.easy.node'] = MagicMock()
sys.modules['openant.easy.channel'] = MagicMock()

# Mock the Node and Channel classes
mock_node = MagicMock()
mock_channel = MagicMock()
sys.modules['openant.easy.node'].Node = mock_node
sys.modules['openant.easy.channel'].Channel = mock_channel

from pyantdisplay.managers.device_manager import DeviceManager


class TestDeviceManager:
    """Test cases for DeviceManager class."""

    def test_init(self):
        """Test device manager initialization."""
        config = {
            "ant_network": {"key": [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]},
            "devices": {
                "heart_rate": {"enabled": True, "device_id": 12345},
                "bike_data": {"enabled": True, "device_id": 67890}
            }
        }

        device_manager = DeviceManager(config)

        assert device_manager.config == config
        assert device_manager.running is False
        assert device_manager.hr_monitor is None
        assert device_manager.bike_sensor is None
        assert device_manager.devices == []
        assert device_manager.hr_data == {}
        assert device_manager.bike_data == {}

    @patch("pyantdisplay.managers.device_manager.HeartRateMonitor")
    @patch("pyantdisplay.managers.device_manager.BikeSensor")
    def test_connect_devices_both_enabled_success(self, mock_bike_sensor_class, mock_hr_monitor_class):
        """Test connecting devices when both are enabled and connection succeeds."""
        config = {
            "ant_network": {"key": [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]},
            "devices": {
                "heart_rate": {"enabled": True, "device_id": 12345},
                "bike_data": {"enabled": True, "device_id": 67890}
            }
        }

        # Mock device instances
        mock_hr_monitor = Mock()
        mock_hr_monitor.connect.return_value = True
        mock_hr_monitor_class.return_value = mock_hr_monitor

        mock_bike_sensor = Mock()
        mock_bike_sensor.connect.return_value = True
        mock_bike_sensor_class.return_value = mock_bike_sensor

        device_manager = DeviceManager(config)
        device_manager.connect_devices()

        # Verify device creation
        mock_hr_monitor_class.assert_called_once_with(12345, [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45])
        mock_bike_sensor_class.assert_called_once_with(67890, [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45])

        # Verify connections attempted
        mock_hr_monitor.connect.assert_called_once()
        mock_bike_sensor.connect.assert_called_once()

        # Verify callback assignment
        assert mock_hr_monitor.on_heart_rate_data == device_manager._on_hr_data
        assert mock_bike_sensor.on_bike_data == device_manager._on_bike_data

        # Verify devices added to list
        assert len(device_manager.devices) == 2
        assert mock_hr_monitor in device_manager.devices
        assert mock_bike_sensor in device_manager.devices

    @patch("pyantdisplay.managers.device_manager.HeartRateMonitor")
    @patch("pyantdisplay.managers.device_manager.BikeSensor")
    def test_connect_devices_connection_failures(self, mock_bike_sensor_class, mock_hr_monitor_class):
        """Test connecting devices when connections fail."""
        config = {
            "ant_network": {"key": [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]},
            "devices": {
                "heart_rate": {"enabled": True, "device_id": 12345},
                "bike_data": {"enabled": True, "device_id": 67890}
            }
        }

        # Mock device instances with connection failures
        mock_hr_monitor = Mock()
        mock_hr_monitor.connect.return_value = False
        mock_hr_monitor_class.return_value = mock_hr_monitor

        mock_bike_sensor = Mock()
        mock_bike_sensor.connect.return_value = False
        mock_bike_sensor_class.return_value = mock_bike_sensor

        device_manager = DeviceManager(config)
        device_manager.connect_devices()

        # Verify devices not added to list
        assert len(device_manager.devices) == 0

    def test_connect_devices_hr_disabled(self):
        """Test connecting devices when heart rate is disabled."""
        config = {
            "ant_network": {"key": [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]},
            "devices": {
                "heart_rate": {"enabled": False, "device_id": 12345},
                "bike_data": {"enabled": True, "device_id": 67890}
            }
        }

        with patch("pyantdisplay.managers.device_manager.BikeSensor") as mock_bike_sensor_class:
            mock_bike_sensor = Mock()
            mock_bike_sensor.connect.return_value = True
            mock_bike_sensor_class.return_value = mock_bike_sensor

            device_manager = DeviceManager(config)
            device_manager.connect_devices()

            # Verify only bike sensor created
            assert device_manager.hr_monitor is None
            assert device_manager.bike_sensor is not None
            assert len(device_manager.devices) == 1

    def test_connect_devices_no_device_id(self):
        """Test connecting devices when device_id is None."""
        config = {
            "ant_network": {"key": [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]},
            "devices": {
                "heart_rate": {"enabled": True, "device_id": None},
                "bike_data": {"enabled": True, "device_id": 67890}
            }
        }

        with patch("pyantdisplay.managers.device_manager.BikeSensor") as mock_bike_sensor_class:
            mock_bike_sensor = Mock()
            mock_bike_sensor.connect.return_value = True
            mock_bike_sensor_class.return_value = mock_bike_sensor

            device_manager = DeviceManager(config)
            device_manager.connect_devices()

            # Verify HR monitor not created due to None device_id
            assert device_manager.hr_monitor is None
            assert device_manager.bike_sensor is not None
            assert len(device_manager.devices) == 1

    def test_on_hr_data_callback(self):
        """Test heart rate data callback."""
        config = {
            "ant_network": {"key": [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]},
            "devices": {
                "heart_rate": {"enabled": False, "device_id": None},
                "bike_data": {"enabled": False, "device_id": None}
            }
        }

        device_manager = DeviceManager(config)
        test_data = {"heart_rate": 75, "beat_count": 100}

        device_manager._on_hr_data(test_data)

        assert device_manager.hr_data == test_data

    def test_on_bike_data_callback(self):
        """Test bike sensor data callback."""
        config = {
            "ant_network": {"key": [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]},
            "devices": {
                "heart_rate": {"enabled": False, "device_id": None},
                "bike_data": {"enabled": False, "device_id": None}
            }
        }

        device_manager = DeviceManager(config)
        test_data = {"speed": 25.5, "cadence": 85, "distance": 10.2}

        device_manager._on_bike_data(test_data)

        assert device_manager.bike_data == test_data

    def test_get_connected_devices(self):
        """Test getting connected devices."""
        config = {
            "ant_network": {"key": [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]},
            "devices": {
                "heart_rate": {"enabled": False, "device_id": None},
                "bike_data": {"enabled": False, "device_id": None}
            }
        }

        device_manager = DeviceManager(config)

        # Create mock devices
        connected_device = Mock()
        connected_device.connected = True
        disconnected_device = Mock()
        disconnected_device.connected = False

        device_manager.devices = [connected_device, disconnected_device]

        connected = device_manager.get_connected_devices()

        assert len(connected) == 1
        assert connected_device in connected
        assert disconnected_device not in connected

    def test_has_connected_devices_true(self):
        """Test has_connected_devices returns True when devices are connected."""
        config = {
            "ant_network": {"key": [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]},
            "devices": {
                "heart_rate": {"enabled": False, "device_id": None},
                "bike_data": {"enabled": False, "device_id": None}
            }
        }

        device_manager = DeviceManager(config)

        # Mock get_connected_devices to return non-empty list
        with patch.object(device_manager, 'get_connected_devices', return_value=[Mock()]):
            assert device_manager.has_connected_devices() is True

    def test_has_connected_devices_false(self):
        """Test has_connected_devices returns False when no devices are connected."""
        config = {
            "ant_network": {"key": [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]},
            "devices": {
                "heart_rate": {"enabled": False, "device_id": None},
                "bike_data": {"enabled": False, "device_id": None}
            }
        }

        device_manager = DeviceManager(config)

        # Mock get_connected_devices to return empty list
        with patch.object(device_manager, 'get_connected_devices', return_value=[]):
            assert device_manager.has_connected_devices() is False

    def test_stop(self):
        """Test stopping device manager."""
        config = {
            "ant_network": {"key": [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]},
            "devices": {
                "heart_rate": {"enabled": False, "device_id": None},
                "bike_data": {"enabled": False, "device_id": None}
            }
        }

        device_manager = DeviceManager(config)
        device_manager.running = True

        # Create mock devices
        mock_hr_monitor = Mock()
        mock_bike_sensor = Mock()
        device_manager.hr_monitor = mock_hr_monitor
        device_manager.bike_sensor = mock_bike_sensor

        device_manager.stop()

        assert device_manager.running is False
        mock_hr_monitor.disconnect.assert_called_once()
        mock_bike_sensor.disconnect.assert_called_once()

    def test_stop_no_devices(self):
        """Test stopping device manager when no devices are connected."""
        config = {
            "ant_network": {"key": [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]},
            "devices": {
                "heart_rate": {"enabled": False, "device_id": None},
                "bike_data": {"enabled": False, "device_id": None}
            }
        }

        device_manager = DeviceManager(config)
        device_manager.running = True

        # Should not raise exception when no devices exist
        device_manager.stop()

        assert device_manager.running is False