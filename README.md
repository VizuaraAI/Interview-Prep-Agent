# ML Engineer Interview Simulation Agent

An AI-powered interview preparation platform for ML Engineers.

## Project Structure

```
Interview-Simulation-Agent/
├── backend/          # FastAPI backend with Docling
├── frontend/         # Next.js frontend with Apple-style design
└── README.md
```

## Development Approach

This project is built using a **unit testing workflow**, where each part is developed, tested, and approved before moving to the next part.

### Parts Overview

- **Part 1**: Resume Upload and Extraction ✅ (Current)
- **Part 2**: Greeting and Conversation (Pending)
- **Part 3**: Project-based Questions (Pending)
- **Part 4**: Factual and Theory Questions (Pending)

---

## Part 1: Resume Upload and Extraction

### Features

- PDF resume upload via drag-and-drop or file picker
- Docling-powered text extraction
- Structured data extraction:
  - Name
  - Education
  - Work Experience
  - Projects
  - Achievements
  - Technical Skills
- Supabase database storage

### Setup Instructions

#### 1. Set up Supabase Database

1. Go to your Supabase project dashboard: https://supabase.com/dashboard
2. Navigate to SQL Editor
3. Run the SQL commands from `backend/schema.sql`
4. Get your Supabase anon key:
   - Go to Project Settings > API
   - Copy the `anon` `public` key
5. Update `backend/.env` with your Supabase anon key

#### 2. Set up Backend

```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Make sure .env file has correct credentials
# Edit .env and add your SUPABASE_KEY

# Run the backend
python main.py
```

Backend will be available at http://localhost:8000

#### 3. Set up Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```

Frontend will be available at http://localhost:3000

### Testing Part 1

#### Option 1: Using the Web Interface (Recommended)

1. Make sure both backend (port 8000) and frontend (port 3000) are running
2. Open http://localhost:3000 in your browser
3. Drag and drop the resume PDF or click to browse
4. Click "Upload Resume"
5. Verify that:
   - Upload completes successfully
   - Contact information is extracted correctly
   - All sections (Education, Work Experience, Projects, etc.) are displayed
   - Data shows in the success screen

#### Option 2: Using the Test Script

```bash
cd backend

# Make sure backend is running (python main.py)

# In a new terminal:
python test_upload.py
```

The test script will:
- Upload the sample resume
- Display extracted contact information
- Show all extracted sections
- Display the student ID
- Retrieve the data from the database

#### Option 3: Using curl

```bash
# Upload resume
curl -X POST "http://localhost:8000/upload-resume" \
  -F "file=@/Users/rajat/Desktop/Vizuara RAG Demo Nutri Chatbot/Himanshu Kumar Resume - Himanshu Kumar.pdf"

# Get student data (replace STUDENT_ID with the ID from upload response)
curl "http://localhost:8000/student/STUDENT_ID"
```

### Verification Checklist for Part 1

- [ ] Backend runs without errors
- [ ] Frontend runs without errors
- [ ] Resume can be uploaded via drag-and-drop
- [ ] Resume can be uploaded via file picker
- [ ] Name is extracted correctly
- [ ] Contact info (email, phone, LinkedIn, GitHub) is extracted
- [ ] Education section is extracted
- [ ] Work Experience section is extracted
- [ ] Projects section is extracted
- [ ] Achievements section is extracted
- [ ] Technical Skills section is extracted
- [ ] Data is stored in Supabase (check database)
- [ ] Data can be retrieved using the student ID
- [ ] UI is clean and Apple-style minimalistic

### Database Verification

To verify data is stored in Supabase:

1. Go to your Supabase dashboard
2. Navigate to Table Editor
3. Check the `students` table - you should see the student record
4. Check the `resume_sections` table - you should see all extracted sections

---

## Next Steps

Once Part 1 is tested and approved, we will proceed to:

**Part 2: Greeting and Conversation**
- Personalized greeting using extracted name
- Small talk with the student
- Goal and motivation questions
- Ready-to-start confirmation

---

## Tech Stack

### Backend
- Python 3.9+
- FastAPI
- Docling (PDF extraction)
- Supabase (Database)

### Frontend
- Next.js 15
- TypeScript
- Tailwind CSS
- Apple-style minimalistic design

---

## Notes

- Only PDF files are supported for resume upload
- The frontend uses Apple's SF Pro Display font family
- All sections are stored separately in the database for easy querying
- The design follows Apple's minimalistic aesthetic principles
