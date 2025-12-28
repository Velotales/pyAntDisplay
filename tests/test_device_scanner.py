"""
Tests for device scanner functionality.
"""

from unittest.mock import MagicMock, Mock, patch

from pyantdisplay.services.device_scanner import DeviceScanner


class TestDeviceScanner:
    """Test cases for DeviceScanner class."""

    @patch("pyantdisplay.services.device_scanner.AntBackend")
    @patch("pyantdisplay.services.device_scanner.load_manufacturers")
    def test_init(self, mock_load_manufacturers, mock_backend_class):
        """Test scanner initialization."""
        mock_backend = Mock()
        mock_backend_class.return_value = mock_backend
        mock_load_manufacturers.return_value = {}

        network_key = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]
        scanner = DeviceScanner(network_key, scan_timeout=10)

        assert scanner.network_key == network_key
        assert scanner.scan_timeout == 10
        assert scanner.found_devices == {}
        assert not scanner.scanning
        assert scanner.node is None

    @patch("pyantdisplay.services.device_scanner.AntBackend")
    @patch("pyantdisplay.services.device_scanner.load_manufacturers")
    @patch("time.sleep")  # Prevent actual sleeping
    @patch("time.time")
    def test_scan_for_devices_initialization(
        self, mock_time, mock_sleep, mock_load_manufacturers, mock_backend_class
    ):
        """Test scan initialization."""
        mock_backend = Mock()
        mock_ant_node = Mock()
        mock_backend.create_node.return_value = mock_ant_node
        mock_backend_class.return_value = mock_backend
        mock_load_manufacturers.return_value = {}

        # Simulate immediate timeout to prevent hanging
        mock_time.side_effect = [0, 2]

        network_key = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]
        scanner = DeviceScanner(network_key, scan_timeout=1)

        devices = scanner.scan_for_devices()

        # Check that the backend was used properly
        mock_backend_class.assert_called_once()
        mock_backend.create_node.assert_called_once()
        assert isinstance(devices, dict)

    @patch("pyantdisplay.services.device_scanner.AntBackend")
    @patch("pyantdisplay.services.device_scanner.load_manufacturers")
    def test_on_device_found(self, mock_load_manufacturers, mock_backend_class):
        """Test device found callback."""
        mock_backend = Mock()
        mock_backend_class.return_value = mock_backend
        mock_load_manufacturers.return_value = {}

        network_key = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]
        scanner = DeviceScanner(network_key)

        # Simulate device data with channel ID
        data = [0x39, 0x30, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05]  # Sample data
        device_type = 120
        device_name = "Heart Rate Monitor"
        chan_id = (12345, device_type, 0)  # (device_id, device_type, transmission_type)

        scanner._on_device_found(data, device_type, device_name, chan_id)

        # Check if device was added
        device_id = chan_id[0]  # Use device_id from chan_id
        device_key = f"{device_type}_{device_id}"

        assert device_key in scanner.found_devices
        assert scanner.found_devices[device_key]["device_type"] == device_type
        assert scanner.found_devices[device_key]["device_name"] == device_name

    @patch("pyantdisplay.services.device_scanner.AntBackend")
    @patch("pyantdisplay.services.device_scanner.load_manufacturers")
    @patch("builtins.open", create=True)
    @patch("json.load")
    @patch("json.dump")
    def test_save_found_devices(
        self,
        mock_json_dump,
        mock_json_load,
        mock_open,
        mock_load_manufacturers,
        mock_backend_class,
    ):
        """Test saving found devices to file."""
        mock_backend = Mock()
        mock_backend_class.return_value = mock_backend
        mock_load_manufacturers.return_value = {}

        # Mock the file reading to return empty dict (simulating no existing file)
        mock_json_load.side_effect = FileNotFoundError()

        network_key = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]
        scanner = DeviceScanner(network_key)

        # Add a mock device
        scanner.found_devices = {
            "120_12345": {
                "device_id": 12345,
                "device_type": 120,
                "device_name": "Test HR Monitor",
            }
        }

        scanner.save_found_devices("test_devices.json")

        # Should be called twice: once for read attempt, once for write
        assert mock_open.call_count == 2
        mock_open.assert_any_call("test_devices.json", "r")
        mock_open.assert_any_call("test_devices.json", "w")
        mock_json_dump.assert_called_once()

    @patch("pyantdisplay.services.device_scanner.AntBackend")
    @patch("pyantdisplay.services.device_scanner.load_manufacturers")
    @patch("builtins.open", create=True)
    @patch("json.load")
    def test_load_found_devices_success(
        self, mock_json_load, mock_open, mock_load_manufacturers, mock_backend_class
    ):
        """Test loading found devices from file."""
        mock_backend = Mock()
        mock_backend_class.return_value = mock_backend
        mock_load_manufacturers.return_value = {}

        network_key = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]
        scanner = DeviceScanner(network_key)

        mock_devices = {
            "120_12345": {
                "device_id": 12345,
                "device_type": 120,
                "device_name": "Test HR Monitor",
            }
        }
        mock_json_load.return_value = mock_devices

        devices = scanner.load_found_devices("test_devices.json")

        assert devices == mock_devices
        mock_open.assert_called_once_with("test_devices.json", "r")

    @patch("pyantdisplay.services.device_scanner.AntBackend")
    @patch("pyantdisplay.services.device_scanner.load_manufacturers")
    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_load_found_devices_file_not_found(
        self, mock_open, mock_load_manufacturers, mock_backend_class
    ):
        """Test loading devices when file doesn't exist."""
        mock_backend = Mock()
        mock_backend_class.return_value = mock_backend
        mock_load_manufacturers.return_value = {}

        network_key = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]
        scanner = DeviceScanner(network_key)

        devices = scanner.load_found_devices("nonexistent.json")

        assert devices == {}

    @patch("pyantdisplay.services.device_scanner.AntBackend")
    @patch("pyantdisplay.services.device_scanner.load_manufacturers")
    def test_stop_scan(self, mock_load_manufacturers, mock_backend_class):
        """Test stopping scan."""
        mock_backend = Mock()
        mock_backend_class.return_value = mock_backend
        mock_load_manufacturers.return_value = {}

        network_key = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]
        scanner = DeviceScanner(network_key)

        scanner.scanning = True
        scanner.stop_scan()

        assert not scanner.scanning

    @patch("pyantdisplay.services.device_scanner.AntBackend")
    @patch("pyantdisplay.services.device_scanner.load_manufacturers")
    def test_scan_timeout_handling(self, mock_load_manufacturers, mock_backend_class):
        """Test scan timeout handling."""
        mock_backend = Mock()
        mock_backend_class.return_value = mock_backend
        mock_load_manufacturers.return_value = {}

        network_key = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]
        scanner = DeviceScanner(network_key, scan_timeout=1)

        # Verify timeout is set correctly
        assert scanner.scan_timeout == 1
