"""
Pytest configuration and shared fixtures for pico-boot tests.
"""

import os
import sys
from importlib.metadata import EntryPoint
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_module():
    """Create a mock module for testing."""
    module = ModuleType("test_module")
    module.__name__ = "test_module"
    return module


@pytest.fixture
def mock_module_with_components():
    """Create a mock module with pico-ioc components."""
    module = ModuleType("app_module")
    module.__name__ = "app_module"

    # Simulate a component class
    class MockService:
        pass

    module.MockService = MockService
    return module


@pytest.fixture
def mock_entry_point():
    """Create a mock entry point."""
    ep = MagicMock(spec=EntryPoint)
    ep.name = "test_plugin"
    ep.module = "test_plugin_module"
    ep.group = "pico_boot.modules"
    return ep


@pytest.fixture
def mock_entry_points_empty():
    """Mock entry_points() to return empty results."""
    with patch("pico_boot.entry_points") as mock_eps:
        mock_result = MagicMock()
        mock_result.select.return_value = []
        mock_eps.return_value = mock_result
        yield mock_eps


@pytest.fixture
def clean_env():
    """Ensure clean environment variables for tests."""
    env_vars = ["PICO_BOOT_AUTO_PLUGINS"]
    original = {k: os.environ.get(k) for k in env_vars}

    for var in env_vars:
        if var in os.environ:
            del os.environ[var]

    yield

    for var, value in original.items():
        if value is not None:
            os.environ[var] = value
        elif var in os.environ:
            del os.environ[var]
