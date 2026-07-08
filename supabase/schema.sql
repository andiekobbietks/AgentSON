-- AgentSON Supabase Schema
-- Version: 1.0.0
-- Date: 2026-07-04

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Sessions table
CREATE TABLE sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- Core fields
  tool TEXT NOT NULL,
  agent TEXT,
  model TEXT,
  variant TEXT,
  
  -- Timestamps
  started_at TIMESTAMPTZ,
  ended_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  
  -- Session data (the full .agentson JSON)
  data JSONB NOT NULL,
  
  -- Full-text search vector (auto-generated)
  search_vector TSVECTOR GENERATED ALWAYS AS (
    to_tsvector('english', 
      COALESCE(data->>'id', '') || ' ' ||
      COALESCE(data->'tool'->>'name', '') || ' ' ||
      COALESCE(data->'agent'->>'name', '') || ' ' ||
      COALESCE(
        (SELECT string_agg(
          COALESCE(entry->>'text', '') || ' ' ||
          COALESCE(entry->>'code', '') || ' ' ||
          COALESCE(entry->>'output', ''),
          ' '
        )
        FROM jsonb_array_elements(data->'entries') AS entry),
        ''
      )
    )
  ) STORED,
  
  -- User association
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  
  -- Metadata
  total_tokens INTEGER,
  cost DECIMAL(10, 6),
  message_count INTEGER,
  
  -- Constraints
  CONSTRAINT valid_tool CHECK (tool IN (
    'opencode', 'minimax', 'antigravity', 'chrome-devtools',
    'cursor', 'claude-code', 'copilot', 'other'
  ))
);

-- Indexes
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_tool ON sessions(tool);
CREATE INDEX idx_sessions_created_at ON sessions(created_at DESC);
CREATE INDEX idx_sessions_search ON sessions USING GIN(search_vector);
CREATE INDEX idx_sessions_data ON sessions USING GIN(data);

-- Updated at trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER sessions_updated_at
  BEFORE UPDATE ON sessions
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();

-- Row Level Security
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY "Users can view own sessions"
  ON sessions FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own sessions"
  ON sessions FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own sessions"
  ON sessions FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own sessions"
  ON sessions FOR DELETE
  USING (auth.uid() = user_id);

-- Function for full-text search
CREATE OR REPLACE FUNCTION search_sessions(
  search_term TEXT,
  user_uuid UUID DEFAULT NULL,
  tool_filter TEXT DEFAULT NULL,
  limit_count INTEGER DEFAULT 50
)
RETURNS TABLE (
  id UUID,
  tool TEXT,
  agent TEXT,
  title TEXT,
  started_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ,
  relevance REAL
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    s.id,
    s.tool,
    s.agent,
    s.data->>'id' AS title,
    s.started_at,
    s.created_at,
    ts_rank(s.search_vector, plainto_tsquery('english', search_term)) AS relevance
  FROM sessions s
  WHERE 
    (user_uuid IS NULL OR s.user_id = user_uuid)
    AND (tool_filter IS NULL OR s.tool = tool_filter)
    AND s.search_vector @@ plainto_tsquery('english', search_term)
  ORDER BY relevance DESC
  LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Function to get session stats
CREATE OR REPLACE FUNCTION get_session_stats(user_uuid UUID)
RETURNS TABLE (
  total_sessions BIGINT,
  total_tokens BIGINT,
  total_cost DECIMAL(10, 6),
  tools_used TEXT[],
  date_range TSTZRANGE
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    COUNT(*)::BIGINT AS total_sessions,
    COALESCE(SUM(s.total_tokens), 0)::BIGINT AS total_tokens,
    COALESCE(SUM(s.cost), 0)::DECIMAL(10, 6) AS total_cost,
    ARRAY_AGG(DISTINCT s.tool) AS tools_used,
    tstzrange(MIN(s.started_at), MAX(s.ended_at)) AS date_range
  FROM sessions s
  WHERE s.user_id = user_uuid;
END;
$$ LANGUAGE plpgsql;
