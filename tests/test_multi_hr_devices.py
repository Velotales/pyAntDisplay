#!/usr/bin/env python3
"""
Test multiple heart rate devices per user functionality.

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
"""

from unittest.mock import MagicMock, patch

from pyantdisplay.live_monitor import LiveMonitor
from pyantdisplay.mqtt_monitor import MqttMonitor


class TestMultiHRDevices:
    """Test multiple heart rate devices per user."""

    def test_user_for_hr_multiple_devices(self):
        """Test that users can be identified from multiple HR device IDs."""
        # Mock config with multiple HR devices for one user
        mock_config = {
            "sensor_map": {
                "users": [
                    {
                        "name": "John",
                        "hr_device_ids": [12345, 67890],  # Two HR devices
                        "speed_device_id": None,
                    },
                    {
                        "name": "Sarah", 
                        "hr_device_ids": [11111],  # Single HR device
                        "speed_device_id": None,
                    }
                ]
            }
        }
        
        with patch("builtins.open"), patch("yaml.safe_load", return_value=mock_config):
            monitor = LiveMonitor("test_config.yaml", "test_save.json")
            
            # Test that both HR devices map to John
            assert monitor._user_for_hr(12345) == "John"
            assert monitor._user_for_hr(67890) == "John"
            
            # Test that Sarah's device maps correctly
            assert monitor._user_for_hr(11111) == "Sarah"
            
            # Test unknown device returns None
            assert monitor._user_for_hr(99999) is None

    def test_backward_compatibility_single_hr_device(self):
        """Test backward compatibility with old hr_device_id format."""
        # Mock config with old single hr_device_id format
        mock_config = {
            "sensor_map": {
                "users": [
                    {
                        "name": "John",
                        "hr_device_id": 12345,  # Old format
                        "speed_device_id": None,
                    }
                ]
            }
        }
        
        with patch("builtins.open"), patch("yaml.safe_load", return_value=mock_config):
            monitor = LiveMonitor("test_config.yaml", "test_save.json")
            
            # Test that old format still works
            assert monitor._user_for_hr(12345) == "John"
            assert monitor._user_for_hr(99999) is None

    def test_mqtt_monitor_multiple_hr_devices(self):
        """Test MQTT monitor handles multiple HR devices per user."""
        sensor_config = {
            "sensor_map": {
                "users": [
                    {
                        "name": "John",
                        "hr_device_ids": [12345, 67890],
                        "speed_device_id": None,
                    }
                ]
            }
        }
        
        app_config = {
            "mqtt": {
                "host": "localhost",
                "port": 1883,
                "base_topic": "test"
            }
        }
        
        with patch("builtins.open"), \
             patch("yaml.safe_load") as mock_yaml, \
             patch("pyantdisplay.mqtt_monitor.mqtt") as mock_mqtt:
            
            mock_yaml.side_effect = [sensor_config, app_config]
            mock_mqtt.Client.return_value = MagicMock()
            
            monitor = MqttMonitor("sensor_config.yaml", "save.json", "app_config.yaml")
            
            # Test that both HR devices map to John  
            assert monitor._user_for_hr(12345) == "John"
            assert monitor._user_for_hr(67890) == "John"
            assert monitor._user_for_hr(99999) is None

    def test_channel_opening_multiple_hr_devices(self):
        """Test that channels are opened for all HR devices assigned to users."""
        mock_config = {
            "sensor_map": {
                "users": [
                    {
                        "name": "John",
                        "hr_device_ids": [12345, 67890],
                        "speed_device_id": None,
                    }
                ],
                "wattbike": {}
            }
        }
        
        with patch("builtins.open"), \
             patch("yaml.safe_load", return_value=mock_config), \
             patch("pyantdisplay.live_monitor.load_manufacturers", return_value={}):
            
            monitor = LiveMonitor("test_config.yaml", "test_save.json")
            monitor._open_channel = MagicMock()
            
            # Mock the channels and user_values initialization
            monitor.channels = []
            monitor.user_values = {}
            
            monitor._open_configured_channels()
            
            # Verify channels were opened for both HR devices
            expected_calls = [
                ((12345, 120, "John-HR1"), {}),
                ((67890, 120, "John-HR2"), {}),
            ]
            
            actual_calls = monitor._open_channel.call_args_list
            assert len(actual_calls) == 2
            
            # Check that user was initialized in user_values
            assert "John" in monitor.user_values
            assert monitor.user_values["John"]["hr"] is None