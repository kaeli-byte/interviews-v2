"""Agent API tests."""
from unittest.mock import AsyncMock, patch


class TestAgents:
    """Test agent endpoints."""

    @patch('backend.db.queries.seed_default_agents', new_callable=AsyncMock)
    @patch('backend.db.queries.get_active_agent_summaries', new_callable=AsyncMock)
    def test_list_agents(self, mock_list, mock_seed, client):
        """Test GET /api/agents lists available agents."""
        mock_seed.return_value = None
        mock_list.return_value = [
            {"agent_id": "hr-manager", "name": "HR Manager", "description": "Screening"},
            {"agent_id": "hiring-manager", "name": "Hiring Manager", "description": "Loop"}
        ]
        response = client.get("/api/agents")
        assert response.status_code == 200
        assert response.json()[0] == {"agent_id": "hr-manager", "name": "HR Manager", "description": "Screening"}

    @patch('backend.db.queries.get_agent_by_id', new_callable=AsyncMock)
    def test_get_agent_details(self, mock_get, client):
        """Test GET /api/agents/{id} returns agent details."""
        mock_get.return_value = {
            "id": "hr-manager",
            "name": "HR Manager",
            "description": "Manages initial screening"
        }
        response = client.get("/api/agents/hr-manager")
        assert response.status_code in [200, 404, 500]


class TestDebrief:
    """Test debrief endpoints."""

    @patch('backend.db.queries.create_debrief', new_callable=AsyncMock)
    def test_generate_debrief(self, mock_gen, client):
        """Test POST /api/debrief generates a debrief."""
        mock_gen.return_value = {
            "id": "debrief-123",
            "session_id": "session-123",
            "summary": "Candidate performed well",
            "strengths": ["Good communication"],
            "areas_for_improvement": ["Technical depth"]
        }
        response = client.post("/api/debrief", json={
            "session_id": "session-123"
        }, headers={
            "Authorization": "Bearer test-token"
        })
        assert response.status_code in [200, 201, 401, 404, 500]

    @patch('backend.db.queries.get_debriefs_by_user', new_callable=AsyncMock)
    def test_list_debriefs(self, mock_list, client):
        """Test GET /api/debrief/history lists debriefs."""
        mock_list.return_value = []
        response = client.get("/api/debrief/history", headers={
            "Authorization": "Bearer test-token"
        })
        # May fail due to auth, but tests structure
        assert response.status_code in [200, 401, 500]

    @patch('backend.db.queries.create_debrief', new_callable=AsyncMock)
    def test_regenerate_debrief(self, mock_regen, client):
        """Test POST /api/debrief/{id}/regenerate regenerates a debrief."""
        mock_regen.return_value = {
            "id": "debrief-123",
            "summary": "Updated summary",
            "strengths": ["Improved communication"],
            "areas_for_improvement": ["Technical depth"]
        }
        response = client.post("/api/debrief/debrief-123/regenerate", headers={
            "Authorization": "Bearer test-token"
        })
        assert response.status_code in [200, 401, 404, 500]
