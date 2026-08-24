-- Migration: 01_teacher_student_knowledge.sql
-- Creates the teacher_student_knowledge table for the Agentic Hackathon project.
-- This table is NEW — not part of The Cabinet (the-cabinet repo).
-- Run: psql -U crafter_admin -d thecraftershub -f 01_teacher_student_knowledge.sql

-- Enable pgvector extension (safe if already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Main table
CREATE TABLE IF NOT EXISTS teacher_student_knowledge (
    id                  SERIAL PRIMARY KEY,
    content_type        TEXT NOT NULL CHECK (content_type IN ('video_extract', 'qa_pair')),

    -- Source attribution
    source_url          TEXT,
    source_filename     TEXT,

    -- Extracted craft knowledge (populated for video_extract)
    technique_name      TEXT,
    category            TEXT,
    materials           TEXT[],
    tools               TEXT[],
    safety_notes        TEXT,
    skill_level         TEXT CHECK (skill_level IN ('beginner', 'intermediate', 'advanced')),
    step_by_step        JSONB,
    key_concepts        TEXT[],
    common_mistakes     TEXT[],

    -- Q&A fields (populated for qa_pair)
    question            TEXT,
    answer              TEXT,
    confidence_level    TEXT CHECK (confidence_level IN ('kb_match', 'web_source', 'synthesized')),

    -- Raw content (always populated — transcript or "Q: ... A: ..." string)
    raw_content         TEXT NOT NULL,

    -- pgvector embedding (3072-dim, gemini-embedding-2 actual output)
    embedding           vector(3072),

    -- Timestamps
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_tsk_embedding
    ON teacher_student_knowledge
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 50);

CREATE INDEX IF NOT EXISTS idx_tsk_content_type
    ON teacher_student_knowledge (content_type);

CREATE INDEX IF NOT EXISTS idx_tsk_created_at
    ON teacher_student_knowledge (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_tsk_category
    ON teacher_student_knowledge (category);

-- Auto-update updated_at on row changes
CREATE OR REPLACE FUNCTION update_tsk_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tsk_updated_at_trigger ON teacher_student_knowledge;
CREATE TRIGGER tsk_updated_at_trigger
    BEFORE UPDATE ON teacher_student_knowledge
    FOR EACH ROW
    EXECUTE FUNCTION update_tsk_updated_at();

-- Verification
DO $$
BEGIN
    RAISE NOTICE 'teacher_student_knowledge table ready. Row count: %',
        (SELECT COUNT(*) FROM teacher_student_knowledge);
END $$;
