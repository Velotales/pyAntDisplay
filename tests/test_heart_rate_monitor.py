"""
Tests for heart rate monitor functionality.
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

from pyantdisplay.devices.heart_rate_monitor import HeartRateMonitor


class TestHeartRateMonitor:
    """Test cases for HeartRateMonitor class."""

    def test_init(self):
        """Test heart rate monitor initialization."""
        device_id = 12345
        network_key = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]

        hr_monitor = HeartRateMonitor(device_id, network_key)

        assert hr_monitor.device_id == device_id
        assert hr_monitor.network_key == network_key
        assert hr_monitor.heart_rate == 0
        assert hr_monitor.rr_intervals == []
        assert not hr_monitor.connected
        assert not hr_monitor.running
        assert hr_monitor.node is None
        assert hr_monitor.channel is None

    @patch("pyantdisplay.devices.heart_rate_monitor.Node")
    def test_connect_success(self, mock_node_class):
        """Test successful connection to heart rate monitor."""
        mock_ant_node = Mock()
        mock_ant_channel = Mock()
        mock_node_class.return_value = mock_ant_node
        mock_ant_node.new_channel.return_value = mock_ant_channel

        device_id = 12345
        network_key = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]

        hr_monitor = HeartRateMonitor(device_id, network_key)
        result = hr_monitor.connect()

        assert result is True
        assert hr_monitor.connected is True
        assert hr_monitor.running is True
        mock_ant_node.start.assert_called_once()
        mock_ant_channel.open.assert_called_once()
        mock_ant_channel.set_id.assert_called_with(device_id, 120, 0)

    @patch("pyantdisplay.devices.heart_rate_monitor.Node")
    def test_connect_failure(self, mock_node_class):
        """Test connection failure."""
        mock_node_class.side_effect = Exception("Connection failed")

        device_id = 12345
        network_key = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]

        hr_monitor = HeartRateMonitor(device_id, network_key)
        result = hr_monitor.connect()

        assert result is False
        assert hr_monitor.connected is False
        assert hr_monitor.running is False

    def test_on_heart_rate_data(self):
        """Test heart rate data processing."""
        device_id = 12345
        network_key = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]

        hr_monitor = HeartRateMonitor(device_id, network_key)

        # Mock callback
        callback_data = None

        def mock_callback(data):
            nonlocal callback_data
            callback_data = data

        hr_monitor.on_heart_rate_data = mock_callback

        # Simulate heart rate data
        # ANT+ HR data format: [sync, beat_count_lsb, hr, beat_count_msb, rr_lsb, rr_msb, ?, computed_hr]
        data = [0x00, 0x10, 0x00, 0x00, 0x44, 0x03, 0x20, 0x48]  # 72 BPM

        hr_monitor._on_heart_rate_data(data)

        assert hr_monitor.heart_rate == 72
        assert callback_data is not None
        assert callback_data["heart_rate"] == 72

    def test_get_current_data(self):
        """Test getting current heart rate data."""
        device_id = 12345
        network_key = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]

        hr_monitor = HeartRateMonitor(device_id, network_key)
        hr_monitor.heart_rate = 75
        hr_monitor.connected = True
        hr_monitor.last_update = 1234567890

        data = hr_monitor.get_current_data()

        assert data["heart_rate"] == 75
        assert data["connected"] is True
        assert data["last_update"] == 1234567890
        assert "data_age" in data

    @patch("time.time", return_value=1234567895)
    def test_is_data_fresh(self, mock_time):
        """Test data freshness check."""
        device_id = 12345
        network_key = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]

        hr_monitor = HeartRateMonitor(device_id, network_key)

        # No data yet
        assert not hr_monitor.is_data_fresh()

        # Fresh data (1 second old)
        hr_monitor.last_update = 1234567894
        assert hr_monitor.is_data_fresh()

        # Stale data (10 seconds old)
        hr_monitor.last_update = 1234567885
        assert not hr_monitor.is_data_fresh()

    def test_disconnect(self):
        """Test disconnection."""
        device_id = 12345
        network_key = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]

        hr_monitor = HeartRateMonitor(device_id, network_key)
        hr_monitor.running = True
        hr_monitor.connected = True
        hr_monitor.channel = Mock()
        hr_monitor.node = Mock()

        hr_monitor.disconnect()

        assert not hr_monitor.running
        assert not hr_monitor.connected
        hr_monitor.channel.close.assert_called_once()
        hr_monitor.node.stop.assert_called_once()
