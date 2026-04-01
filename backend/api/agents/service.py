"""Agents service."""
from time import monotonic
from typing import Optional

from backend.db import queries as db
from backend.perf import timing_span

_seeded = False
_agents_cache: list[dict] | None = None
_agents_cache_loaded_at = 0.0
_AGENTS_CACHE_TTL_SECONDS = 300.0


async def ensure_seeded():
    """Ensure the default agent config exists."""
    global _seeded
    if _seeded:
        return
    with timing_span("service.agents.ensure_seeded"):
        await db.seed_default_agents()
    _seeded = True


async def get_all_agents():
    """Return all active agents."""
    global _agents_cache, _agents_cache_loaded_at
    await ensure_seeded()
    now = monotonic()
    if _agents_cache is not None and now - _agents_cache_loaded_at < _AGENTS_CACHE_TTL_SECONDS:
        return _agents_cache

    agents = await db.get_active_agent_summaries()
    _agents_cache = agents
    _agents_cache_loaded_at = now
    return agents


async def get_agent(agent_id: str) -> Optional[dict]:
    """Return a single active agent."""
    await ensure_seeded()
    return await db.get_agent_by_id(agent_id)
