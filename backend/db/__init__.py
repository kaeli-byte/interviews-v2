"""Database connection using asyncpg with Supabase."""
import os
from dotenv import load_dotenv
import asyncpg

load_dotenv()

DATABASE_URL = os.getenv("SUPABASE_DB_URL", os.getenv("DATABASE_URL"))

_pool: asyncpg.Pool = None


async def get_pool() -> asyncpg.Pool:
    """Get or create database connection pool."""
    global _pool
    if _pool is None:
        if not DATABASE_URL:
            raise ValueError("SUPABASE_DB_URL not set in environment")
        _pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=2,
            max_size=10,
            command_timeout=60
        )
    return _pool


async def close_pool():
    """Close database connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None