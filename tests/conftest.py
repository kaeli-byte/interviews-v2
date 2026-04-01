"""Pytest configuration and fixtures."""
import os
import sys
from typing import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def client():
    """Create a test client with auth overridden and DB access mocked."""
    from backend.db import queries as queries_module
    from backend.dependencies import get_current_user
    from backend.main import app

    async def override_current_user():
        return {
            "id": "11111111-1111-1111-1111-111111111111",
            "email": "test@example.com",
            "token": "test-token",
            "raw_user": {"id": "11111111-1111-1111-1111-111111111111", "email": "test@example.com"},
        }

    mock_pool = MagicMock()
    queries_module._pool = mock_pool

    app.dependency_overrides[get_current_user] = override_current_user

    with patch.object(queries_module, "get_pool", new_callable=AsyncMock, return_value=mock_pool), patch.object(
        queries_module, "close_pool", new_callable=AsyncMock, return_value=None
    ):
        with TestClient(app) as test_client:
            yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """Headers for endpoints that expect a bearer token."""
    return {"Authorization": "Bearer test-token"}
