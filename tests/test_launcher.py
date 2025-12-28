"""
Tests for application launcher functionality.
"""

from unittest.mock import Mock, patch

import pytest

from pyantdisplay.launcher import ApplicationLauncher


class TestApplicationLauncher:
    """Test cases for ApplicationLauncher class."""

    def test_init(self):
        """Test application launcher initialization."""
        with patch("pyantdisplay.launcher.AppModeService"):
            launcher = ApplicationLauncher()
            assert launcher.mode_service is not None

    @patch("pyantdisplay.launcher.AppModeService")
    def test_run_menu(self, mock_app_mode_service_class):
        """Test running menu mode."""
        mock_mode_service = Mock()
        mock_app_mode_service_class.return_value = mock_mode_service
        
        launcher = ApplicationLauncher()
        launcher.run_menu("test_app.yaml", "test_local.yaml")
        
        mock_mode_service.run_menu.assert_called_once_with("test_app.yaml", "test_local.yaml")

    @patch("pyantdisplay.launcher.AppModeService")
    def test_run_menu_defaults(self, mock_app_mode_service_class):
        """Test running menu mode with default parameters."""
        mock_mode_service = Mock()
        mock_app_mode_service_class.return_value = mock_mode_service
        
        launcher = ApplicationLauncher()
        launcher.run_menu()
        
        mock_mode_service.run_menu.assert_called_once_with(None, None)

    @patch("pyantdisplay.launcher.AppModeService")
    def test_run_scan(self, mock_app_mode_service_class):
        """Test running scan mode."""
        mock_mode_service = Mock()
        mock_app_mode_service_class.return_value = mock_mode_service
        
        launcher = ApplicationLauncher()
        launcher.run_scan("test_app.yaml", "test_local.yaml", debug=True)
        
        mock_mode_service.run_scan.assert_called_once_with("test_app.yaml", "test_local.yaml", True)

    @patch("pyantdisplay.launcher.AppModeService")
    def test_run_scan_defaults(self, mock_app_mode_service_class):
        """Test running scan mode with default parameters."""
        mock_mode_service = Mock()
        mock_app_mode_service_class.return_value = mock_mode_service
        
        launcher = ApplicationLauncher()
        launcher.run_scan("test_app.yaml")
        
        mock_mode_service.run_scan.assert_called_once_with("test_app.yaml", None, False)

    @patch("pyantdisplay.launcher.AppModeService")
    def test_run_list(self, mock_app_mode_service_class):
        """Test running list mode."""
        mock_mode_service = Mock()
        mock_app_mode_service_class.return_value = mock_mode_service
        
        launcher = ApplicationLauncher()
        launcher.run_list("test_app.yaml", "test_local.yaml")
        
        mock_mode_service.run_list.assert_called_once_with("test_app.yaml", "test_local.yaml")

    @patch("pyantdisplay.launcher.AppModeService")
    def test_run_list_defaults(self, mock_app_mode_service_class):
        """Test running list mode with default parameters."""
        mock_mode_service = Mock()
        mock_app_mode_service_class.return_value = mock_mode_service
        
        launcher = ApplicationLauncher()
        launcher.run_list("test_app.yaml")
        
        mock_mode_service.run_list.assert_called_once_with("test_app.yaml", None)

    @patch("pyantdisplay.launcher.AppModeService")
    def test_run_monitor(self, mock_app_mode_service_class):
        """Test running monitor mode."""
        mock_mode_service = Mock()
        mock_app_mode_service_class.return_value = mock_mode_service
        
        launcher = ApplicationLauncher()
        launcher.run_monitor("sensor_config.yaml", "devices.json", debug=True)
        
        mock_mode_service.run_monitor.assert_called_once_with("sensor_config.yaml", "devices.json", True)

    @patch("pyantdisplay.launcher.AppModeService")
    def test_run_monitor_defaults(self, mock_app_mode_service_class):
        """Test running monitor mode with default parameters."""
        mock_mode_service = Mock()
        mock_app_mode_service_class.return_value = mock_mode_service
        
        launcher = ApplicationLauncher()
        launcher.run_monitor("sensor_config.yaml", "devices.json")
        
        mock_mode_service.run_monitor.assert_called_once_with("sensor_config.yaml", "devices.json", False)

    @patch("pyantdisplay.launcher.AppModeService")
    def test_run_mqtt(self, mock_app_mode_service_class):
        """Test running MQTT mode."""
        mock_mode_service = Mock()
        mock_app_mode_service_class.return_value = mock_mode_service
        
        launcher = ApplicationLauncher()
        launcher.run_mqtt(
            "sensor_config.yaml", 
            "devices.json", 
            "app_config.yaml", 
            "local_config.yaml", 
            debug=True
        )
        
        mock_mode_service.run_mqtt.assert_called_once_with(
            "sensor_config.yaml", 
            "devices.json", 
            "app_config.yaml", 
            "local_config.yaml", 
            True
        )

    @patch("pyantdisplay.launcher.AppModeService")
    def test_run_mqtt_defaults(self, mock_app_mode_service_class):
        """Test running MQTT mode with default parameters."""
        mock_mode_service = Mock()
        mock_app_mode_service_class.return_value = mock_mode_service
        
        launcher = ApplicationLauncher()
        launcher.run_mqtt("sensor_config.yaml", "devices.json", "app_config.yaml")
        
        mock_mode_service.run_mqtt.assert_called_once_with(
            "sensor_config.yaml", 
            "devices.json", 
            "app_config.yaml", 
            None, 
            False
        )

    @patch("pyantdisplay.launcher.AppModeService")
    def test_service_exception_propagation(self, mock_app_mode_service_class):
        """Test that exceptions from mode service are propagated."""
        mock_mode_service = Mock()
        mock_mode_service.run_menu.side_effect = RuntimeError("Service error")
        mock_app_mode_service_class.return_value = mock_mode_service
        
        launcher = ApplicationLauncher()
        
        with pytest.raises(RuntimeError, match="Service error"):
            launcher.run_menu("test.yaml")