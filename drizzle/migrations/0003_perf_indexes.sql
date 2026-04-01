CREATE INDEX IF NOT EXISTS sessions_user_started_at_idx
ON sessions (user_id, started_at DESC);

CREATE INDEX IF NOT EXISTS interview_contexts_user_created_at_idx
ON interview_contexts (user_id, created_at DESC);

CREATE UNIQUE INDEX IF NOT EXISTS sessions_reconnect_token_idx
ON sessions (reconnect_token);

CREATE INDEX IF NOT EXISTS sessions_context_id_idx
ON sessions (context_id);

CREATE INDEX IF NOT EXISTS sessions_agent_id_idx
ON sessions (agent_id);

CREATE INDEX IF NOT EXISTS interview_contexts_agent_id_idx
ON interview_contexts (agent_id);

CREATE INDEX IF NOT EXISTS agent_configs_is_active_created_at_idx
ON agent_configs (is_active, created_at);
