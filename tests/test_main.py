"""
Tests for main entry point functionality.
"""

from unittest.mock import patch

from pyantdisplay.__main__ import main


class TestMain:
    """Test cases for main entry point."""

    @patch("pyantdisplay.__main__.CLIHandler")
    def test_main(self, mock_cli_handler_class):
        """Test main function creates CLI handler and runs it."""
        mock_cli_handler = mock_cli_handler_class.return_value
        
        main()
        
        mock_cli_handler_class.assert_called_once()
        mock_cli_handler.run.assert_called_once()

    @patch("pyantdisplay.__main__.CLIHandler")
    def test_main_exception_handling(self, mock_cli_handler_class):
        """Test main function handles exceptions from CLI handler."""
        mock_cli_handler = mock_cli_handler_class.return_value
        mock_cli_handler.run.side_effect = Exception("Test exception")
        
        # Should propagate exception (not catch it)
        try:
            main()
            assert False, "Expected exception to be raised"
        except Exception as e:
            assert str(e) == "Test exception"
            
        mock_cli_handler_class.assert_called_once()
        mock_cli_handler.run.assert_called_once()