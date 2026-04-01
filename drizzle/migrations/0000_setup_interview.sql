CREATE TABLE IF NOT EXISTS documents (
    id uuid PRIMARY KEY,
    user_id uuid NOT NULL,
    kind varchar(50) NOT NULL,
    type varchar(50),
    source_type varchar(50),
    filename varchar(255),
    mime_type varchar(255),
    storage_path varchar(500),
    file_path varchar(500),
    source_url text,
    raw_text text,
    content text,
    parse_status varchar(50) DEFAULT 'pending',
    created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS profiles (
    id uuid PRIMARY KEY,
    document_id uuid REFERENCES documents(id) ON DELETE SET NULL,
    user_id uuid NOT NULL,
    profile_type varchar(50) NOT NULL,
    name varchar(255),
    headline text,
    skills text,
    experience text,
    company varchar(255),
    role varchar(255),
    requirements text,
    confidence_score double precision,
    structured_json jsonb DEFAULT '{}'::jsonb,
    summary_text text,
    created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agent_configs (
    id uuid PRIMARY KEY,
    name varchar(100) NOT NULL,
    description text,
    prompt_template text NOT NULL,
    behavior_settings jsonb DEFAULT '{}'::jsonb,
    rubric_definition jsonb DEFAULT '[]'::jsonb,
    version integer DEFAULT 1,
    is_active boolean DEFAULT true,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS interview_contexts (
    id uuid PRIMARY KEY,
    user_id uuid NOT NULL,
    resume_profile_id uuid REFERENCES profiles(id) ON DELETE SET NULL,
    job_profile_id uuid REFERENCES profiles(id) ON DELETE SET NULL,
    agent_id uuid REFERENCES agent_configs(id) ON DELETE SET NULL,
    custom_instructions text,
    match_analysis_json jsonb DEFAULT '{}'::jsonb,
    created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sessions (
    id uuid PRIMARY KEY,
    user_id uuid NOT NULL,
    context_id uuid REFERENCES interview_contexts(id) ON DELETE SET NULL,
    agent_id uuid REFERENCES agent_configs(id) ON DELETE SET NULL,
    status varchar(50) DEFAULT 'pending',
    started_at timestamptz DEFAULT now(),
    ended_at timestamptz,
    transcript jsonb DEFAULT '[]'::jsonb,
    reconnect_token uuid NOT NULL
);

CREATE TABLE IF NOT EXISTS debriefs (
    id uuid PRIMARY KEY,
    session_id uuid NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    user_id uuid NOT NULL,
    scores jsonb DEFAULT '{}'::jsonb,
    feedback text,
    evidence jsonb DEFAULT '[]'::jsonb,
    rubric_used jsonb DEFAULT '[]'::jsonb,
    generated_at timestamptz DEFAULT now()
);

ALTER TABLE documents ADD COLUMN IF NOT EXISTS kind varchar(50);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS source_type varchar(50);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS mime_type varchar(255);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS storage_path varchar(500);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS source_url text;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS raw_text text;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS parse_status varchar(50) DEFAULT 'pending';
UPDATE documents SET kind = COALESCE(kind, type) WHERE kind IS NULL AND type IS NOT NULL;

ALTER TABLE profiles ADD COLUMN IF NOT EXISTS structured_json jsonb DEFAULT '{}'::jsonb;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS summary_text text;

ALTER TABLE interview_contexts ADD COLUMN IF NOT EXISTS agent_id uuid REFERENCES agent_configs(id) ON DELETE SET NULL;
ALTER TABLE interview_contexts ADD COLUMN IF NOT EXISTS custom_instructions text;
ALTER TABLE interview_contexts ADD COLUMN IF NOT EXISTS match_analysis_json jsonb DEFAULT '{}'::jsonb;
