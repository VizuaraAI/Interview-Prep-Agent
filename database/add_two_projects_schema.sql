-- Add columns to conversations table for tracking two projects and GPA

-- Add project tracking columns
ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS current_project_index INTEGER DEFAULT 0, -- 0 = first project, 1 = second project
ADD COLUMN IF NOT EXISTS project_1_questions_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS project_2_questions_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS projects_data JSONB; -- Store the two project titles and content

-- Add GPA column to students table
ALTER TABLE students
ADD COLUMN IF NOT EXISTS gpa DECIMAL(4,2) DEFAULT 0;

-- Add comments
COMMENT ON COLUMN conversations.current_project_index IS 'Index of current project being discussed (0 or 1)';
COMMENT ON COLUMN conversations.project_1_questions_count IS 'Number of questions asked about first project';
COMMENT ON COLUMN conversations.project_2_questions_count IS 'Number of questions asked about second project';
COMMENT ON COLUMN conversations.projects_data IS 'JSON data containing the two projects being discussed';
COMMENT ON COLUMN students.gpa IS 'Student GPA/CGPA extracted from resume';
