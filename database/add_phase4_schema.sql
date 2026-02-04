-- Add columns to conversations table for Phase IV tracking
ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS student_topics TEXT[], -- Array of ML topics student is interested in
ADD COLUMN IF NOT EXISTS questions_asked TEXT[], -- Array of questions already asked in Phase IV
ADD COLUMN IF NOT EXISTS project_questions_count INTEGER DEFAULT 0, -- Track number of project questions asked
ADD COLUMN IF NOT EXISTS factual_questions_count INTEGER DEFAULT 0; -- Track number of factual questions asked

-- Add comment
COMMENT ON COLUMN conversations.student_topics IS 'ML topics extracted from student resume for Phase IV';
COMMENT ON COLUMN conversations.questions_asked IS 'List of factual questions already asked in Phase IV';
COMMENT ON COLUMN conversations.project_questions_count IS 'Counter for project questions in Phase III';
COMMENT ON COLUMN conversations.factual_questions_count IS 'Counter for factual questions in Phase IV';
