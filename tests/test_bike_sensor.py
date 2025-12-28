"""
Tests for bike sensor functionality.
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

from pyantdisplay.devices.bike_sensor import BikeSensor


class TestBikeSensor:
    """Test cases for BikeSensor class."""

    def test_init(self):
        """Test bike sensor initialization."""
        device_id = 67890
        network_key = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]
        wheel_circumference = 2.1

        bike_sensor = BikeSensor(device_id, network_key, wheel_circumference)

        assert bike_sensor.device_id == device_id
        assert bike_sensor.network_key == network_key
        assert bike_sensor.wheel_circumference == wheel_circumference
        assert bike_sensor.speed == 0.0
        assert bike_sensor.cadence == 0
        assert bike_sensor.distance == 0.0
        assert not bike_sensor.connected
        assert not bike_sensor.running
        assert bike_sensor.node is None
        assert bike_sensor.channel is None

    @patch("pyantdisplay.devices.bike_sensor.Node")
    def test_connect_success(self, mock_node_class):
        """Test successful connection to bike sensor."""
        mock_ant_node = Mock()
        mock_ant_channel = Mock()
        mock_node_class.return_value = mock_ant_node
        mock_ant_node.new_channel.return_value = mock_ant_channel

        device_id = 67890
        network_key = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]

        bike_sensor = BikeSensor(device_id, network_key)
        result = bike_sensor.connect()

        assert result is True
        assert bike_sensor.connected is True
        assert bike_sensor.running is True
        mock_ant_node.start.assert_called_once()
        mock_ant_channel.open.assert_called_once()
        mock_ant_channel.set_id.assert_called_with(device_id, 121, 0)

    @patch("pyantdisplay.devices.bike_sensor.Node")
    def test_connect_failure(self, mock_node_class):
        """Test connection failure."""
        mock_node_class.side_effect = Exception("Connection failed")

        device_id = 67890
        network_key = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]

        bike_sensor = BikeSensor(device_id, network_key)
        result = bike_sensor.connect()

        assert result is False
        assert bike_sensor.connected is False
        assert bike_sensor.running is False

    @patch("time.time", return_value=1234567890)
    def test_on_bike_data_initial(self, mock_time):
        """Test initial bike data processing (no previous data)."""
        device_id = 67890
        network_key = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]

        bike_sensor = BikeSensor(device_id, network_key, wheel_circumference=2.0)

        # Mock callback
        callback_data = None

        def mock_callback(data):
            nonlocal callback_data
            callback_data = data

        bike_sensor.on_bike_data = mock_callback

        # Simulate bike sensor data
        # Format: [cadence_time_lsb, cadence_time_msb, cadence_count_lsb, cadence_count_msb,
        #          speed_time_lsb, speed_time_msb, speed_count_lsb, speed_count_msb]
        data = [0x10, 0x20, 0x05, 0x00, 0x30, 0x40, 0x0A, 0x00]

        bike_sensor._on_bike_data(data)

        # First data point should set baseline values but not calculate speed/cadence
        assert bike_sensor.last_update == 1234567890
        assert callback_data is not None

    def test_get_current_data(self):
        """Test getting current bike sensor data."""
        device_id = 67890
        network_key = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]

        bike_sensor = BikeSensor(device_id, network_key)
        bike_sensor.speed = 25.5
        bike_sensor.cadence = 85
        bike_sensor.distance = 10.2
        bike_sensor.connected = True
        bike_sensor.last_update = 1234567890

        data = bike_sensor.get_current_data()

        assert data["speed"] == 25.5
        assert data["cadence"] == 85
        assert data["distance"] == 10.2
        assert data["connected"] is True
        assert data["last_update"] == 1234567890
        assert "data_age" in data

    @patch("time.time", return_value=1234567895)
    def test_is_data_fresh(self, mock_time):
        """Test data freshness check."""
        device_id = 67890
        network_key = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]

        bike_sensor = BikeSensor(device_id, network_key)

        # No data yet
        assert not bike_sensor.is_data_fresh()

        # Fresh data (1 second old)
        bike_sensor.last_update = 1234567894
        assert bike_sensor.is_data_fresh()

        # Stale data (10 seconds old)
        bike_sensor.last_update = 1234567885
        assert not bike_sensor.is_data_fresh()

    def test_reset_distance(self):
        """Test resetting trip distance."""
        device_id = 67890
        network_key = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]

        bike_sensor = BikeSensor(device_id, network_key)
        bike_sensor.distance = 15.5

        bike_sensor.reset_distance()

        assert bike_sensor.distance == 0.0

    def test_disconnect(self):
        """Test disconnection."""
        device_id = 67890
        network_key = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]

        bike_sensor = BikeSensor(device_id, network_key)
        bike_sensor.running = True
        bike_sensor.connected = True
        bike_sensor.channel = Mock()
        bike_sensor.node = Mock()

        bike_sensor.disconnect()

        assert not bike_sensor.running
        assert not bike_sensor.connected
        bike_sensor.channel.close.assert_called_once()
        bike_sensor.node.stop.assert_called_once()

    @patch("time.time")
    def test_on_bike_data_subsequent_calls(self, mock_time):
        """Test subsequent bike data processing with speed/cadence calculation."""
        mock_time.side_effect = [1234567890, 1234567892]  # 2 second difference
        
        device_id = 67890
        network_key = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]
        bike_sensor = BikeSensor(device_id, network_key, wheel_circumference=2.0)

        # Mock callback
        callback_data = None
        def mock_callback(data):
            nonlocal callback_data
            callback_data = data

        bike_sensor.on_bike_data = mock_callback

        # First data point - establishes baseline
        data1 = [0x10, 0x20, 0x05, 0x00, 0x30, 0x40, 0x0A, 0x00]
        bike_sensor._on_bike_data(data1)
        
        # Second data point - should calculate speed/cadence
        data2 = [0x20, 0x20, 0x06, 0x00, 0x40, 0x40, 0x0C, 0x00]
        bike_sensor._on_bike_data(data2)

        # Should have updated speed/cadence
        assert bike_sensor.last_update == 1234567892
        assert callback_data is not None

    def test_on_bike_data_invalid_data(self):
        """Test bike data processing with invalid/short data."""
        device_id = 67890
        network_key = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]
        bike_sensor = BikeSensor(device_id, network_key)

        # Test with data too short
        short_data = [0x10, 0x20]
        bike_sensor._on_bike_data(short_data)
        
        # Should not update anything
        assert bike_sensor.last_update == 0

    @patch("time.time")
    def test_on_bike_data_subsequent_calls(self, mock_time):
        """Test subsequent bike data processing with speed/cadence calculation."""
        mock_time.side_effect = [1234567890, 1234567892]  # 2 second difference
        
        device_id = 67890
        network_key = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]
        bike_sensor = BikeSensor(device_id, network_key, wheel_circumference=2.0)

        # Mock callback
        callback_data = None
        def mock_callback(data):
            nonlocal callback_data
            callback_data = data

        bike_sensor.on_bike_data = mock_callback

        # First data point - establishes baseline
        data1 = [0x10, 0x20, 0x05, 0x00, 0x30, 0x40, 0x0A, 0x00]
        bike_sensor._on_bike_data(data1)
        
        # Second data point - should calculate speed/cadence
        data2 = [0x20, 0x20, 0x06, 0x00, 0x40, 0x40, 0x0C, 0x00]
        bike_sensor._on_bike_data(data2)

        # Should have updated speed/cadence
        assert bike_sensor.last_update == 1234567892
        assert callback_data is not None

    def test_on_bike_data_invalid_data(self):
        """Test bike data processing with invalid/short data."""
        device_id = 67890
        network_key = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]
        bike_sensor = BikeSensor(device_id, network_key)

        # Test with data too short
        short_data = [0x10, 0x20]
        bike_sensor._on_bike_data(short_data)
        
        # Should not update anything
        assert bike_sensor.last_update == 0
