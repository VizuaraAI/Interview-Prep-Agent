"""
Update database schema for Phase IV
Run this once to add new columns to conversations table
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

# Execute SQL to add Phase IV columns
sql_query = """
ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS student_topics TEXT[],
ADD COLUMN IF NOT EXISTS questions_asked TEXT[],
ADD COLUMN IF NOT EXISTS project_questions_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS factual_questions_count INTEGER DEFAULT 0;
"""

try:
    result = supabase.rpc('exec_sql', {'query': sql_query}).execute()
    print("Schema updated successfully!")
    print(result)
except Exception as e:
    print(f"Note: Schema may already exist or direct SQL execution not available.")
    print(f"Please run the SQL manually in Supabase dashboard:")
    print(sql_query)

print("\nDone!")
