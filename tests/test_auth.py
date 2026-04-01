"""Authentication API tests."""
from unittest.mock import AsyncMock, patch

from backend.dependencies import get_current_user
from backend.main import app


class TestAuth:
    """Test auth endpoints."""

    @patch("backend.api.auth.service.signup", new_callable=AsyncMock)
    def test_signup(self, mock_signup, client):
        """Test user registration."""
        mock_signup.return_value = {
            "access_token": "test-token",
            "token_type": "bearer",
            "user": {"id": "test-id", "email": "test@example.com"},
        }
        response = client.post("/api/auth/signup", json={
            "email": "test@example.com",
            "password": "testpass123"
        })
        assert response.status_code == 200

    @patch("backend.api.auth.service.login", new_callable=AsyncMock)
    def test_login(self, mock_login, client):
        """Test user login."""
        mock_login.return_value = {
            "access_token": "test-token",
            "token_type": "bearer",
            "user": {"id": "test-id", "email": "test@example.com"},
        }
        response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "testpass123"
        })
        assert response.status_code == 200

    def test_me_requires_auth(self, client):
        """Test /me requires authentication."""
        app.dependency_overrides.pop(get_current_user, None)
        try:
            response = client.get("/api/auth/me")
        finally:
            async def override_current_user():
                return {
                    "id": "11111111-1111-1111-1111-111111111111",
                    "email": "test@example.com",
                    "token": "test-token",
                    "raw_user": {"id": "11111111-1111-1111-1111-111111111111", "email": "test@example.com"},
                }

            app.dependency_overrides[get_current_user] = override_current_user
        assert response.status_code in [401, 403]

    def test_me_with_auth(self, client):
        """Test /me with authentication."""
        response = client.get("/api/auth/me", headers={
            "Authorization": "Bearer test-token"
        })
        assert response.status_code == 200
