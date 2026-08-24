-- Fix migration: change embedding dimension to 3072 (actual gemini-embedding-2 output)
-- Note: pgvector index types (ivfflat/hnsw) cap at 2000 dims.
-- Sequential scan is used at this scale (<10K rows). Index can be added post-demo.

-- Drop old index (was 768-dim)
DROP INDEX IF EXISTS idx_tsk_embedding;

-- Alter column type to match gemini-embedding-2 actual output
ALTER TABLE teacher_student_knowledge
    ALTER COLUMN embedding TYPE vector(3072);

-- No index created: sequential cosine scan is fine at demo scale (<10K rows).
-- To add later (after pgvector upgrade): CREATE INDEX USING hnsw ... WITH (m=16, ef_construction=64)

DO $$ BEGIN
    RAISE NOTICE 'teacher_student_knowledge.embedding updated to vector(3072) - no index (sequential scan)';
END $$;
