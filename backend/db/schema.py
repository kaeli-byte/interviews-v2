"""Database schema using Drizzle."""
import uuid
from datetime import datetime
from drizzle_orm import asyncpg

# Users table
users = asyncpg.Table(
    "users",
    asyncpg.Column("id", asyncpg.UUID, primary_key=True, default=uuid.uuid4),
    asyncpg.Column("email", asyncpg.Varchar(255), unique=True, not_null=True),
    asyncpg.Column("password_hash", asyncpg.Varchar(255), not_null),
    asyncpg.Column("created_at", asyncpg.Timestamp, default=datetime.utcnow),
)

# Documents table
documents = asyncpg.Table(
    "documents",
    asyncpg.Column("id", asyncpg.UUID, primary_key=True, default=uuid.uuid4),
    asyncpg.Column("user_id", asyncpg.UUID, not_null),
    asyncpg.Column("type", asyncpg.Varchar(50), not_null),  # resume, job_description
    asyncpg.Column("filename", asyncpg.Varchar(255)),
    asyncpg.Column("content", asyncpg.Text),
    asyncpg.Column("file_path", asyncpg.Varchar(500)),
    asyncpg.Column("created_at", asyncpg.Timestamp, default=datetime.utcnow),
)

# Profiles table (extracted from documents)
profiles = asyncpg.Table(
    "profiles",
    asyncpg.Column("id", asyncpg.UUID, primary_key=True, default=uuid.uuid4),
    asyncpg.Column("document_id", asyncpg.UUID),
    asyncpg.Column("user_id", asyncpg.UUID, not_null),
    asyncpg.Column("profile_type", asyncpg.Varchar(50), not_null),  # candidate, job
    asyncpg.Column("name", asyncpg.Varchar(255)),
    asyncpg.Column("headline", asyncpg.Text),
    asyncpg.Column("skills", asyncpg.Text),  # JSON string
    asyncpg.Column("experience", asyncpg.Text),
    asyncpg.Column("company", asyncpg.Varchar(255)),
    asyncpg.Column("role", asyncpg.Varchar(255)),
    asyncpg.Column("requirements", asyncpg.Text),
    asyncpg.Column("confidence_score", asyncpg.Float),
    asyncpg.Column("created_at", asyncpg.Timestamp, default=datetime.utcnow),
)

# Interview contexts table
interview_contexts = asyncpg.Table(
    "interview_contexts",
    asyncpg.Column("id", asyncpg.UUID, primary_key=True, default=uuid.uuid4),
    asyncpg.Column("user_id", asyncpg.UUID, not_null),
    asyncpg.Column("resume_profile_id", asyncpg.UUID),
    asyncpg.Column("job_profile_id", asyncpg.UUID),
    asyncpg.Column("created_at", asyncpg.Timestamp, default=datetime.utcnow),
)

# Sessions table
sessions = asyncpg.Table(
    "sessions",
    asyncpg.Column("id", asyncpg.UUID, primary_key=True, default=uuid.uuid4),
    asyncpg.Column("user_id", asyncpg.UUID, not_null),
    asyncpg.Column("context_id", asyncpg.UUID),
    asyncpg.Column("agent_id", asyncpg.UUID),  # Current interviewer agent
    asyncpg.Column("status", asyncpg.Varchar(50), default="pending"),  # pending, active, paused, ended
    asyncpg.Column("started_at", asyncpg.Timestamp, default=datetime.utcnow),
    asyncpg.Column("ended_at", asyncpg.Timestamp),
    asyncpg.Column("transcript", asyncpg.JSONB, default=[]),
    asyncpg.Column("reconnect_token", asyncpg.UUID, default=uuid.uuid4),  # For session persistence
)

__all__ = ["users", "documents", "profiles", "interview_contexts", "sessions", "agent_configs", "debriefs"]

# Agent configs table (versioned interviewer personas)
agent_configs = asyncpg.Table(
    "agent_configs",
    asyncpg.Column("id", asyncpg.UUID, primary_key=True, default=uuid.uuid4),
    asyncpg.Column("name", asyncpg.Varchar(100), not_null),
    asyncpg.Column("description", asyncpg.Text),
    asyncpg.Column("prompt_template", asyncpg.Text, not_null),
    asyncpg.Column("behavior_settings", asyncpg.JSONB, default={}),
    asyncpg.Column("rubric_definition", asyncpg.JSONB, default=[]),
    asyncpg.Column("version", asyncpg.Integer, default=1),
    asyncpg.Column("is_active", asyncpg.Boolean, default=True),
    asyncpg.Column("created_at", asyncpg.Timestamp, default=datetime.utcnow),
    asyncpg.Column("updated_at", asyncpg.Timestamp, default=datetime.utcnow),
)

# Debriefs table
debriefs = asyncpg.Table(
    "debriefs",
    asyncpg.Column("id", asyncpg.UUID, primary_key=True, default=uuid.uuid4),
    asyncpg.Column("session_id", asyncpg.UUID, not_null),
    asyncpg.Column("user_id", asyncpg.UUID, not_null),
    asyncpg.Column("scores", asyncpg.JSONB, default={}),
    asyncpg.Column("feedback", asyncpg.Text),
    asyncpg.Column("evidence", asyncpg.JSONB, default=[]),
    asyncpg.Column("rubric_used", asyncpg.JSONB, default=[]),
    asyncpg.Column("generated_at", asyncpg.Timestamp, default=datetime.utcnow),
)