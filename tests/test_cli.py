"""
Tests for CLI handler functionality.
"""

import argparse
from unittest.mock import Mock, patch

import pytest

from pyantdisplay.cli import CLIHandler


class TestCLIHandler:
    """Test cases for CLIHandler class."""

    def test_init(self):
        """Test CLI handler initialization."""
        cli = CLIHandler()
        assert cli.launcher is not None

    def test_create_parser(self):
        """Test argument parser creation."""
        cli = CLIHandler()
        parser = cli.create_parser()
        
        assert isinstance(parser, argparse.ArgumentParser)
        assert parser.description == "PyANTDisplay entry point"

    def test_create_parser_defaults(self):
        """Test argument parser default values."""
        cli = CLIHandler()
        parser = cli.create_parser()
        
        # Test with no arguments (should use defaults)
        args = parser.parse_args([])
        
        assert args.mode == "menu"
        assert args.config == "config/sensor_map.yaml"
        assert args.save == "found_devices.json"
        assert args.app_config == "config/config.yaml"
        assert args.local_config is None
        assert args.debug is False

    def test_create_parser_all_arguments(self):
        """Test argument parser with all arguments provided."""
        cli = CLIHandler()
        parser = cli.create_parser()
        
        args = parser.parse_args([
            "--mode", "monitor",
            "--config", "custom_sensor.yaml",
            "--save", "custom_devices.json",
            "--app-config", "custom_app.yaml",
            "--local-config", "local_app.yaml",
            "--debug"
        ])
        
        assert args.mode == "monitor"
        assert args.config == "custom_sensor.yaml"
        assert args.save == "custom_devices.json"
        assert args.app_config == "custom_app.yaml"
        assert args.local_config == "local_app.yaml"
        assert args.debug is True

    def test_create_parser_valid_modes(self):
        """Test argument parser accepts all valid modes."""
        cli = CLIHandler()
        parser = cli.create_parser()
        
        valid_modes = ["menu", "monitor", "scan", "list", "mqtt"]
        
        for mode in valid_modes:
            args = parser.parse_args(["--mode", mode])
            assert args.mode == mode

    def test_create_parser_invalid_mode(self):
        """Test argument parser rejects invalid modes."""
        cli = CLIHandler()
        parser = cli.create_parser()
        
        with pytest.raises(SystemExit):
            parser.parse_args(["--mode", "invalid_mode"])

    @patch("pyantdisplay.cli.ApplicationLauncher")
    def test_handle_args_menu_mode(self, mock_launcher_class):
        """Test handling menu mode arguments."""
        mock_launcher = Mock()
        mock_launcher_class.return_value = mock_launcher
        
        cli = CLIHandler()
        
        args = Mock()
        args.mode = "menu"
        args.app_config = "test_app.yaml"
        args.local_config = "test_local.yaml"
        
        cli.handle_args(args)
        
        mock_launcher.run_menu.assert_called_once_with("test_app.yaml", "test_local.yaml")

    @patch("pyantdisplay.cli.ApplicationLauncher")
    def test_handle_args_monitor_mode(self, mock_launcher_class):
        """Test handling monitor mode arguments."""
        mock_launcher = Mock()
        mock_launcher_class.return_value = mock_launcher
        
        cli = CLIHandler()
        
        args = Mock()
        args.mode = "monitor"
        args.config = "test_sensor.yaml"
        args.save = "test_devices.json"
        args.debug = True
        
        cli.handle_args(args)
        
        mock_launcher.run_monitor.assert_called_once_with("test_sensor.yaml", "test_devices.json", debug=True)

    @patch("pyantdisplay.cli.ApplicationLauncher")
    def test_handle_args_scan_mode(self, mock_launcher_class):
        """Test handling scan mode arguments."""
        mock_launcher = Mock()
        mock_launcher_class.return_value = mock_launcher
        
        cli = CLIHandler()
        
        args = Mock()
        args.mode = "scan"
        args.app_config = "test_app.yaml"
        args.local_config = None
        args.debug = False
        
        cli.handle_args(args)
        
        mock_launcher.run_scan.assert_called_once_with("test_app.yaml", None, debug=False)

    @patch("pyantdisplay.cli.ApplicationLauncher")
    def test_handle_args_list_mode(self, mock_launcher_class):
        """Test handling list mode arguments."""
        mock_launcher = Mock()
        mock_launcher_class.return_value = mock_launcher
        
        cli = CLIHandler()
        
        args = Mock()
        args.mode = "list"
        args.app_config = "test_app.yaml"
        args.local_config = "test_local.yaml"
        
        cli.handle_args(args)
        
        mock_launcher.run_list.assert_called_once_with("test_app.yaml", "test_local.yaml")

    @patch("pyantdisplay.cli.ApplicationLauncher")
    def test_handle_args_mqtt_mode(self, mock_launcher_class):
        """Test handling MQTT mode arguments."""
        mock_launcher = Mock()
        mock_launcher_class.return_value = mock_launcher
        
        cli = CLIHandler()
        
        args = Mock()
        args.mode = "mqtt"
        args.config = "test_sensor.yaml"
        args.save = "test_devices.json"
        args.app_config = "test_app.yaml"
        args.local_config = "test_local.yaml"
        args.debug = True
        
        cli.handle_args(args)
        
        mock_launcher.run_mqtt.assert_called_once_with(
            "test_sensor.yaml", 
            "test_devices.json", 
            "test_app.yaml", 
            "test_local.yaml", 
            debug=True
        )

    @patch("argparse.ArgumentParser.parse_args")
    @patch("pyantdisplay.cli.ApplicationLauncher")
    def test_run(self, mock_launcher_class, mock_parse_args):
        """Test running the CLI with argument parsing."""
        mock_launcher = Mock()
        mock_launcher_class.return_value = mock_launcher
        
        mock_args = Mock()
        mock_args.mode = "menu"
        mock_args.app_config = "config/config.yaml"
        mock_args.local_config = None
        mock_parse_args.return_value = mock_args
        
        cli = CLIHandler()
        cli.run()
        
        mock_parse_args.assert_called_once()
        mock_launcher.run_menu.assert_called_once_with("config/config.yaml", None)

    @patch("sys.argv", ["pyantdisplay"])
    @patch("pyantdisplay.cli.ApplicationLauncher")
    def test_run_integration_defaults(self, mock_launcher_class):
        """Test running CLI with default arguments (integration test)."""
        mock_launcher = Mock()
        mock_launcher_class.return_value = mock_launcher
        
        cli = CLIHandler()
        cli.run()
        
        # Should call menu mode with default config
        mock_launcher.run_menu.assert_called_once_with("config/config.yaml", None)

    @patch("sys.argv", ["pyantdisplay", "--mode", "scan", "--debug"])
    @patch("pyantdisplay.cli.ApplicationLauncher")
    def test_run_integration_scan_debug(self, mock_launcher_class):
        """Test running CLI with scan mode and debug flag (integration test)."""
        mock_launcher = Mock()
        mock_launcher_class.return_value = mock_launcher
        
        cli = CLIHandler()
        cli.run()
        
        # Should call scan mode with debug enabled
        mock_launcher.run_scan.assert_called_once_with("config/config.yaml", None, debug=True)