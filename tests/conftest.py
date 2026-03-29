"""Pytest configuration and fixtures."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def client():
    """Create test client with mocked database."""
    from backend.db import queries as queries_module

    # Set the module-level _pool to avoid connection
    mock_pool = MagicMock()
    queries_module._pool = mock_pool

    # Mock the async functions
    with patch.object(queries_module, 'get_pool', new_callable=AsyncMock, return_value=mock_pool), \
         patch.object(queries_module, 'close_pool', new_callable=AsyncMock, return_value=None):

        from main import app
        return TestClient(app)


@pytest.fixture
def auth_token():
    """Mock JWT token for testing."""
    from jose import jwt
    SECRET_KEY = "dev-secret-change-in-prod"
    payload = {"sub": "test-user-id", "email": "test@example.com"}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


@pytest.fixture
def auth_headers(auth_token):
    """Auth headers for protected endpoints."""
    return {"Authorization": f"Bearer {auth_token}"}