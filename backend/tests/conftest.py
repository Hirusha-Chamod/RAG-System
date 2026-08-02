"""
Pytest configuration & fixtures.

Disables LangSmith tracing during automated unit test runs to prevent test clutter in LangSmith dashboard.
"""

import os
import pytest


@pytest.fixture(autouse=True, scope="session")
def disable_langsmith_during_tests():
    """Automatically disable LangSmith tracing during pytest runs."""
    os.environ["LANGSMITH_TRACING"] = "false"
    yield
