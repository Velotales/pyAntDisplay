"""
Tests for device scanner functionality.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from src.pyantdisplay.device_scanner import DeviceScanner


class TestDeviceScanner:
    """Test cases for DeviceScanner class."""

    def test_init(self):
        """Test scanner initialization."""
        network_key = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]
        scanner = DeviceScanner(network_key, scan_timeout=10)

        assert scanner.network_key == network_key
        assert scanner.scan_timeout == 10
        assert scanner.found_devices == {}
        assert not scanner.scanning
        assert scanner.node is None

    @patch("src.pyantdisplay.device_scanner.AntBackend")
    def test_scan_for_devices_initialization(self, mock_backend_class):
        """Test scan initialization."""
        mock_backend = Mock()
        mock_ant_node = Mock()
        mock_backend.create_node.return_value = mock_ant_node
        mock_backend_class.return_value = mock_backend

        network_key = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]
        scanner = DeviceScanner(network_key, scan_timeout=1)

        with patch("time.time", side_effect=[0, 2]):  # Simulate timeout
            devices = scanner.scan_for_devices()

        # Check that the backend was used properly
        mock_backend_class.assert_called_once()
        mock_backend.create_node.assert_called_once()
        assert isinstance(devices, dict)

    def test_on_device_found(self):
        """Test device found callback."""
        network_key = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]
        scanner = DeviceScanner(network_key)

        # Simulate device data
        data = [0x39, 0x30, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05]  # Sample data
        device_type = 120
        device_name = "Heart Rate Monitor"

        scanner._on_device_found(data, device_type, device_name)

        # Check if device was added
        device_id = (data[1] << 8) | data[0]  # Extract device ID
        device_key = f"{device_type}_{device_id}"

        assert device_key in scanner.found_devices
        assert scanner.found_devices[device_key]["device_type"] == device_type
        assert scanner.found_devices[device_key]["device_name"] == device_name

    @patch("builtins.open", create=True)
    @patch("json.dump")
    def test_save_found_devices(self, mock_json_dump, mock_open):
        """Test saving found devices to file."""
        network_key = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]
        scanner = DeviceScanner(network_key)

        # Add a mock device
        scanner.found_devices = {
            "120_12345": {"device_id": 12345, "device_type": 120, "device_name": "Test HR Monitor"}
        }

        scanner.save_found_devices("test_devices.json")

        mock_open.assert_called_once_with("test_devices.json", "w")
        mock_json_dump.assert_called_once()

    @patch("builtins.open", create=True)
    @patch("json.load")
    def test_load_found_devices_success(self, mock_json_load, mock_open):
        """Test loading found devices from file."""
        network_key = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]
        scanner = DeviceScanner(network_key)

        mock_devices = {"120_12345": {"device_id": 12345, "device_type": 120, "device_name": "Test HR Monitor"}}
        mock_json_load.return_value = mock_devices

        devices = scanner.load_found_devices("test_devices.json")

        assert devices == mock_devices
        mock_open.assert_called_once_with("test_devices.json", "r")

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_load_found_devices_file_not_found(self, mock_open):
        """Test loading devices when file doesn't exist."""
        network_key = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]
        scanner = DeviceScanner(network_key)

        devices = scanner.load_found_devices("nonexistent.json")

        assert devices == {}

    def test_stop_scan(self):
        """Test stopping scan."""
        network_key = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]
        scanner = DeviceScanner(network_key)

        scanner.scanning = True
        scanner.stop_scan()

        assert not scanner.scanning
