"""
Test configuration and fixtures for pyantdisplay tests.
"""

from unittest.mock import MagicMock, Mock

import pytest


@pytest.fixture
def mock_usb_device():
    """Mock USB device for testing."""
    device = Mock()
    device.idVendor = 0x0FCF
    device.idProduct = 0x1008
    device.bus = 1
    device.address = 2
    device.manufacturer = "Dynastream"
    device.product = "ANT USB Stick"
    device.serial_number = "12345"
    return device


@pytest.fixture
def mock_ant_node():
    """Mock ANT+ node for testing."""
    node = Mock()
    node.start = Mock()
    node.stop = Mock()
    node.new_network = Mock()
    node.new_channel = Mock()
    return node


@pytest.fixture
def mock_ant_channel():
    """Mock ANT+ channel for testing."""
    channel = Mock()
    channel.open = Mock()
    channel.close = Mock()
    channel.set_period = Mock()
    channel.set_search_timeout = Mock()
    channel.set_rf_freq = Mock()
    channel.set_id = Mock()
    return channel


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        "devices": {
            "heart_rate": {"device_id": 12345, "device_type": 120, "enabled": True},
            "bike_data": {"device_id": 67890, "device_type": 121, "enabled": True},
        },
        "ant_network": {"key": [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45], "frequency": 57},
        "app": {"scan_timeout": 30, "data_display_interval": 1, "found_devices_file": "test_found_devices.json"},
    }
