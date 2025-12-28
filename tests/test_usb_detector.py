"""
Tests for USB detector functionality.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from pyantdisplay.utils.usb_detector import ANTUSBDetector


class TestANTUSBDetector:
    """Test cases for ANTUSBDetector class."""

    def test_init(self):
        """Test detector initialization."""
        detector = ANTUSBDetector()
        assert detector.detected_devices == []
        assert len(detector.ANT_DEVICES) > 0

    @patch("usb.core.find")
    def test_detect_ant_sticks_success(self, mock_find, mock_usb_device):
        """Test successful ANT+ stick detection."""
        mock_find.return_value = [mock_usb_device]

        detector = ANTUSBDetector()
        devices = detector.detect_ant_sticks()

        assert len(devices) == 1
        assert devices[0]["vendor_id"] == 0x0FCF
        assert devices[0]["product_id"] == 0x1008
        assert devices[0]["name"] == "Dynastream ANT USB-m Stick"

    @patch("usb.core.find")
    def test_detect_ant_sticks_none_found(self, mock_find):
        """Test when no ANT+ sticks are found."""
        mock_find.return_value = []

        detector = ANTUSBDetector()
        devices = detector.detect_ant_sticks()

        assert len(devices) == 0

    @patch("usb.core.find")
    def test_detect_ant_sticks_exception_handling(self, mock_find):
        """Test exception handling during detection."""
        mock_find.side_effect = Exception("USB error")

        detector = ANTUSBDetector()
        devices = detector.detect_ant_sticks()

        assert len(devices) == 0

    def test_is_ant_stick_connected(self, mock_usb_device):
        """Test connection status check."""
        detector = ANTUSBDetector()

        # No devices detected
        assert not detector.is_ant_stick_connected()

        # Add a device
        detector.detected_devices = [{"device": mock_usb_device}]
        assert detector.is_ant_stick_connected()

    @patch("usb.core.find")
    def test_check_usb_permissions_success(self, mock_find):
        """Test USB permissions check success."""
        mock_find.return_value = []

        detector = ANTUSBDetector()
        result = detector.check_usb_permissions()

        assert result is True

    @patch("usb.core.find")
    def test_check_usb_permissions_no_backend(self, mock_find):
        """Test USB permissions check with no backend error."""
        from usb.core import NoBackendError

        mock_find.side_effect = NoBackendError("No backend")

        detector = ANTUSBDetector()
        result = detector.check_usb_permissions()

        assert result is False
