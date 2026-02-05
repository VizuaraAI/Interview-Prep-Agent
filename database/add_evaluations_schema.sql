-- Evaluations table to store separate project and factual evaluations
CREATE TABLE IF NOT EXISTS evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    eval_type TEXT NOT NULL,  -- 'project' or 'factual'
    eval_data JSONB NOT NULL,
    recommendations JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_evaluations_conversation_id ON evaluations(conversation_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_type ON evaluations(eval_type);

-- Add phase column to messages for clean phase-based querying
ALTER TABLE messages ADD COLUMN IF NOT EXISTS phase TEXT;

-- Add evaluation tracking flags to conversations
ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS project_eval_triggered BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS factual_eval_triggered BOOLEAN DEFAULT FALSE;
