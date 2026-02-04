# Backend - Resume Upload Service

## Part 1: Resume Upload and Extraction

This service handles PDF resume uploads, extracts content using Docling, and stores structured data in Supabase.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your Supabase credentials
```

3. Set up database:
- Go to your Supabase project dashboard
- Navigate to SQL Editor
- Run the SQL commands from `schema.sql`

4. Run the server:
```bash
python main.py
```

The server will start at http://localhost:8000

## API Endpoints

### POST /upload-resume
Upload a PDF resume for processing.

**Request:**
- Content-Type: multipart/form-data
- Body: file (PDF)

**Response:**
```json
{
  "success": true,
  "student_id": "uuid",
  "contact_info": {
    "name": "...",
    "email": "...",
    "phone": "...",
    "linkedin": "...",
    "github": "...",
    "portfolio": "..."
  },
  "sections": {
    "Education": "...",
    "Work Experience": "...",
    "Projects": "...",
    "Achievements": "...",
    "Technical Skills": "..."
  }
}
```

### GET /student/{student_id}
Retrieve student data by ID.

## Testing

Use the test script:
```bash
python test_upload.py
```
