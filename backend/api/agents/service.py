"""Agents service - predefined interview agents."""
import uuid
from datetime import datetime

# In-memory storage
agents_db: dict = {}


def seed_default_agents():
    """Seed default interview agents."""
    default_agents = [
        {
            "agent_id": "technical",
            "name": "Technical Interviewer",
            "description": "Focuses on technical skills and problem-solving",
            "system_prompt": "You are a technical interviewer. Ask about data structures, algorithms, and system design.",
            "icon": "code"
        },
        {
            "agent_id": "behavioral",
            "name": "Behavioral Interviewer",
            "description": "Focuses on soft skills and past experiences",
            "system_prompt": "You are a behavioral interviewer. Ask about past projects, teamwork, and conflict resolution.",
            "icon": "users"
        },
        {
            "agent_id": "leadership",
            "name": "Leadership Interviewer",
            "description": "Focuses on management and leadership experience",
            "system_prompt": "You are a leadership interviewer. Ask about managing teams, strategic decisions, and project oversight.",
            "icon": "briefcase"
        }
    ]

    for agent in default_agents:
        agents_db[agent["agent_id"]] = agent


# Initialize default agents
seed_default_agents()


def get_all_agents():
    """Get all available agents."""
    return list(agents_db.values())


def get_agent(agent_id: str):
    """Get an agent by ID."""
    return agents_db.get(agent_id)