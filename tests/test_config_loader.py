"""
Tests for configuration loader functionality.
"""

from unittest.mock import Mock, patch, mock_open

import pytest

from pyantdisplay.utils.config_loader import ConfigLoader


class TestConfigLoader:
    """Test cases for ConfigLoader class."""

    def test_init(self):
        """Test ConfigLoader initialization."""
        loader = ConfigLoader()
        assert loader is not None

    @patch("builtins.open", mock_open(read_data="key: value\nnested:\n  item: test"))
    @patch("yaml.safe_load")
    def test_load_app_config_success(self, mock_yaml_load):
        """Test successful app config loading."""
        mock_config = {"key": "value", "nested": {"item": "test"}}
        mock_yaml_load.return_value = mock_config

        loader = ConfigLoader()
        result = loader.load_app_config("app_config.yaml")

        assert result == mock_config

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_load_app_config_file_not_found(self, mock_open):
        """Test app config loading when file doesn't exist."""
        loader = ConfigLoader()
        result = loader.load_app_config("nonexistent.yaml")

        assert result == {}

    def test_load_app_config_with_local_override(self):
        """Test app config loading with local config override."""
        loader = ConfigLoader()
        
        with patch("builtins.open") as mock_open:
            with patch("yaml.safe_load") as mock_yaml_load:
                # First call returns base config, second returns local config
                mock_yaml_load.side_effect = [
                    {"base": "value", "common": "app"},
                    {"override": "local", "common": "local"}
                ]
                
                result = loader.load_app_config("app_config.yaml", "local_config.yaml")

                expected = {
                    "base": "value",
                    "common": "local",  # Local should override base
                    "override": "local"
                }
                assert result == expected

    @patch("builtins.open", mock_open(read_data="base: value"))
    @patch("yaml.safe_load", return_value={"base": "value"})
    def test_load_app_config_local_file_not_found(self, mock_yaml_load):
        """Test app config loading when local config file doesn't exist."""
        loader = ConfigLoader()
        
        with patch("builtins.open", side_effect=[
            mock_open(read_data="base: value").return_value,
            FileNotFoundError()
        ]):
            result = loader.load_app_config("app_config.yaml", "nonexistent_local.yaml")

        assert result == {"base": "value"}

    @patch("pyantdisplay.utils.config_loader.yaml", None)
    def test_load_app_config_no_yaml_module(self):
        """Test app config loading when PyYAML is not available."""
        loader = ConfigLoader()
        result = loader.load_app_config("app_config.yaml")

        assert result == {}

    def test_deep_merge_simple(self):
        """Test simple dictionary merging."""
        loader = ConfigLoader()
        
        a = {"key1": "value1", "key2": "value2"}
        b = {"key2": "newvalue2", "key3": "value3"}
        
        result = loader._deep_merge(a, b)
        
        expected = {"key1": "value1", "key2": "newvalue2", "key3": "value3"}
        assert result == expected

    def test_deep_merge_nested(self):
        """Test nested dictionary merging."""
        loader = ConfigLoader()
        
        a = {
            "level1": {
                "key1": "value1",
                "key2": "value2"
            },
            "simple": "value"
        }
        b = {
            "level1": {
                "key2": "newvalue2",
                "key3": "value3"
            },
            "new": "added"
        }
        
        result = loader._deep_merge(a, b)
        
        expected = {
            "level1": {
                "key1": "value1",
                "key2": "newvalue2",
                "key3": "value3"
            },
            "simple": "value",
            "new": "added"
        }
        assert result == expected

    def test_deep_merge_none_values(self):
        """Test merging with None values."""
        loader = ConfigLoader()
        
        a = {"key1": "value1"}
        b = None
        
        result = loader._deep_merge(a, b)
        assert result == {"key1": "value1"}

    def test_deep_merge_overwrite_with_dict(self):
        """Test merging when value type changes from simple to dict."""
        loader = ConfigLoader()
        
        a = {"key": "simple_value"}
        b = {"key": {"nested": "dict_value"}}
        
        result = loader._deep_merge(a, b)
        
        expected = {"key": {"nested": "dict_value"}}
        assert result == expected

    def test_deep_merge_empty_dicts(self):
        """Test merging empty dictionaries."""
        loader = ConfigLoader()
        
        result = loader._deep_merge({}, {})
        assert result == {}
        
        result = loader._deep_merge({"key": "value"}, {})
        assert result == {"key": "value"}
        
        result = loader._deep_merge({}, {"key": "value"})
        assert result == {"key": "value"}