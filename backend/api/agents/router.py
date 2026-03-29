"""Agents router."""
from fastapi import APIRouter, HTTPException

from backend.api.agents import service as agent_service
from backend.api.sessions import service as session_service

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("")
async def list_agents():
    """List all available interview agents."""
    return agent_service.get_all_agents()


@router.get("/{agent_id}")
async def get_agent(agent_id: str):
    """Get an agent by ID."""
    agent = agent_service.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.post("/sessions/{session_id}/handoff")
async def handoff_agent(session_id: str, agent_id: str):
    """Handoff a session to a different agent."""
    # Get agent info
    agent = agent_service.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Update session with new agent
    session = session_service.update_session(
        session_id,
        user_id="",  # Will be validated in update_session
        agent_id=agent_id
    )

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "success": True,
        "message": f"Handoff to {agent['name']} complete",
        "agent": agent
    }