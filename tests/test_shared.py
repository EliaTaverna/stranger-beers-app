"""Tests for the shared package."""

import pytest

from shared.phone import normalize_phone, is_valid_phone
from shared.logging import configure_logging, get_logger


class TestPhoneNormalization:
    """Tests for phone normalization utilities."""

    def test_normalize_us_phone_with_formatting(self):
        """US phone with parentheses and dashes normalizes to E.164."""
        result = normalize_phone("(415) 555-1234")
        assert result == "+14155551234"

    def test_normalize_us_phone_plain(self):
        """Plain US phone number normalizes correctly."""
        result = normalize_phone("4155551234")
        assert result == "+14155551234"

    def test_normalize_international_phone(self):
        """International phone numbers normalize correctly."""
        result = normalize_phone("+44 20 7946 0958")
        assert result == "+442079460958"

    def test_normalize_invalid_phone_returns_none(self):
        """Invalid phone numbers return None."""
        assert normalize_phone("invalid") is None
        assert normalize_phone("123") is None
        assert normalize_phone("") is None

    def test_normalize_empty_input(self):
        """Empty and whitespace inputs return None."""
        assert normalize_phone("") is None
        assert normalize_phone("   ") is None
        assert normalize_phone(None) is None  # type: ignore

    def test_is_valid_phone(self):
        """is_valid_phone returns correct boolean."""
        assert is_valid_phone("(415) 555-1234") is True
        assert is_valid_phone("invalid") is False


class TestLogging:
    """Tests for logging configuration."""

    def test_configure_logging_returns_logger(self):
        """configure_logging returns a logger instance."""
        logger = configure_logging("INFO", "test-service")
        assert logger is not None
        assert logger.name == "test-service"

    def test_configure_logging_sets_level(self):
        """Logger has correct level set."""
        import logging

        logger = configure_logging("DEBUG", "test-debug")
        assert logger.level == logging.DEBUG

    def test_get_logger(self):
        """get_logger returns child logger."""
        logger = get_logger("submodule")
        assert "stranger-beers.submodule" in logger.name
