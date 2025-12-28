"""
Tests for configuration manager functionality.
"""

from unittest.mock import Mock, patch, mock_open

import pytest
import yaml

from pyantdisplay.services.config_manager import ConfigManager


class TestConfigManager:
    """Test cases for ConfigManager class."""

    @patch("builtins.open", mock_open(read_data="devices:\n  heart_rate:\n    device_id: 12345"))
    @patch("yaml.safe_load")
    def test_init_loads_config(self, mock_yaml_load):
        """Test that initialization loads configuration."""
        mock_config = {"devices": {"heart_rate": {"device_id": 12345}}}
        mock_yaml_load.return_value = mock_config

        config_manager = ConfigManager("test_config.yaml")

        assert config_manager.config_file == "test_config.yaml"
        assert config_manager.config == mock_config
        mock_yaml_load.assert_called_once()

    @patch("builtins.open", mock_open(read_data="test: value"))
    @patch("yaml.safe_load")
    def test_load_config_success(self, mock_yaml_load):
        """Test successful configuration loading."""
        mock_config = {"test": "value"}
        mock_yaml_load.return_value = mock_config

        config_manager = ConfigManager("test_config.yaml")
        result = config_manager.load_config()

        assert result == mock_config

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_load_config_file_not_found(self, mock_open):
        """Test configuration loading when file doesn't exist."""
        with pytest.raises(SystemExit):
            ConfigManager("nonexistent.yaml")

    @patch("builtins.open", mock_open(read_data="invalid: yaml: content: ["))
    @patch("yaml.safe_load", side_effect=yaml.YAMLError("Invalid YAML"))
    def test_load_config_yaml_error(self, mock_yaml_load):
        """Test configuration loading with YAML parsing error."""
        with pytest.raises(SystemExit):
            ConfigManager("invalid.yaml")

    @patch("builtins.open", mock_open())
    @patch("yaml.dump")
    def test_save_config_success(self, mock_yaml_dump):
        """Test successful configuration saving."""
        with patch("builtins.open", mock_open(read_data="test: value")), \
             patch("yaml.safe_load", return_value={"test": "value"}):
            
            config_manager = ConfigManager("test_config.yaml")
            config_manager.save_config()

            # Just verify yaml.dump was called with the right config data
            mock_yaml_dump.assert_called_once()
            call_args = mock_yaml_dump.call_args
            assert call_args[0][0] == {"test": "value"}  # First positional arg should be the config
            assert call_args[1]["default_flow_style"] is False
            assert call_args[1]["indent"] == 2

    @patch("builtins.open", side_effect=OSError("Permission denied"))
    def test_save_config_error(self, mock_open_error):
        """Test configuration saving with file write error."""
        with patch("builtins.open", mock_open(read_data="test: value")), \
             patch("yaml.safe_load", return_value={"test": "value"}):
            
            config_manager = ConfigManager("test_config.yaml")
            
            # Override open for the save operation
            with patch("builtins.open", mock_open_error):
                # Should not raise exception, just print error
                config_manager.save_config()

    @patch("pyantdisplay.services.config_manager.DeviceConfigurationService")
    def test_configure_devices_interactive_success(self, mock_device_config_service):
        """Test interactive device configuration success."""
        with patch("builtins.open", mock_open(read_data="test: value")), \
             patch("yaml.safe_load", return_value={"test": "value"}):
            
            config_manager = ConfigManager("test_config.yaml")
            
            # Mock successful device configuration
            mock_service_instance = Mock()
            mock_service_instance.configure_devices_interactive.return_value = True
            mock_device_config_service.return_value = mock_service_instance

            with patch.object(config_manager, 'save_config') as mock_save:
                config_manager.configure_devices_interactive()
                
                mock_device_config_service.assert_called_once_with({"test": "value"})
                mock_service_instance.configure_devices_interactive.assert_called_once()
                mock_save.assert_called_once()

    @patch("pyantdisplay.services.config_manager.DeviceConfigurationService")
    def test_configure_devices_interactive_failure(self, mock_device_config_service):
        """Test interactive device configuration failure."""
        with patch("builtins.open", mock_open(read_data="test: value")), \
             patch("yaml.safe_load", return_value={"test": "value"}):
            
            config_manager = ConfigManager("test_config.yaml")
            
            # Mock failed device configuration
            mock_service_instance = Mock()
            mock_service_instance.configure_devices_interactive.return_value = False
            mock_device_config_service.return_value = mock_service_instance

            with patch.object(config_manager, 'save_config') as mock_save:
                config_manager.configure_devices_interactive()
                
                mock_device_config_service.assert_called_once_with({"test": "value"})
                mock_service_instance.configure_devices_interactive.assert_called_once()
                mock_save.assert_not_called()