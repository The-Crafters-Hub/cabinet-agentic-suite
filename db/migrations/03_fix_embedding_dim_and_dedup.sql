-- Migration 03: S-99 fixes
-- 1. Fix embedding dimension: must match gemini-embedding-2 output (3072)
-- 2. Add source_url dedup index (video_extract)
-- 3. Add question dedup index (qa_pair)

ALTER TABLE teacher_student_knowledge
    ALTER COLUMN embedding TYPE vector(3072)
    USING embedding::text::vector(3072);

CREATE UNIQUE INDEX IF NOT EXISTS idx_tsk_source_url_unique
    ON teacher_student_knowledge (source_url)
    WHERE source_url IS NOT NULL AND content_type = 'video_extract';

CREATE UNIQUE INDEX IF NOT EXISTS idx_tsk_question_unique
    ON teacher_student_knowledge (question)
    WHERE question IS NOT NULL AND content_type = 'qa_pair';
