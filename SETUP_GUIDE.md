# Quick Setup Guide - Part 1

Follow these steps to test Part 1 of the ML Interview Agent.

## Prerequisites

- Python 3.9 or higher
- Node.js 18 or higher
- Supabase account

## Step 1: Set up Supabase Database

1. Go to https://supabase.com/dashboard
2. Open your project: https://msmtxfsqkcgsmzafpiuj.supabase.co
3. Navigate to **SQL Editor** (left sidebar)
4. Click **New Query**
5. Copy and paste the entire content from `backend/schema.sql`
6. Click **Run** to execute the SQL
7. Verify tables are created:
   - Go to **Table Editor**
   - You should see `students` and `resume_sections` tables

## Step 2: Get Supabase API Key

1. In your Supabase dashboard, go to **Project Settings** (gear icon)
2. Click on **API** in the left sidebar
3. Under **Project API keys**, find the `anon` `public` key
4. Copy this key
5. Open `backend/.env` file
6. Replace `your_supabase_anon_key_here` with your actual key

## Step 3: Start Backend

Open a terminal:

```bash
cd backend

# Create and activate virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
python main.py
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Keep this terminal open.

## Step 4: Start Frontend

Open a NEW terminal:

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

You should see:
```
- Local:        http://localhost:3000
```

Keep this terminal open.

## Step 5: Test the Application

### Method 1: Web Interface (Easiest)

1. Open your browser and go to http://localhost:3000
2. You should see a beautiful Apple-style interface
3. Drag and drop the resume PDF:
   - Path: `/Users/rajat/Desktop/Vizuara RAG Demo Nutri Chatbot/Himanshu Kumar Resume - Himanshu Kumar.pdf`
   - Or click the upload area to browse for the file
4. Click **Upload Resume**
5. Wait for processing (should take 5-10 seconds)
6. Verify the extracted data shows correctly:
   - Name: Himanshu Kumar
   - Contact information
   - All sections (Education, Work Experience, Projects, etc.)

### Method 2: Test Script

Open a third terminal:

```bash
cd backend
python test_upload.py
```

This will:
- Upload the sample resume
- Print all extracted information
- Show the student ID
- Verify database storage

## Verification Checklist

After testing, verify:

- [ ] Backend is running on port 8000
- [ ] Frontend is running on port 3000
- [ ] Can upload resume via web interface
- [ ] Name extracted: "Himanshu Kumar"
- [ ] Education section extracted
- [ ] Work Experience section extracted (IIT Madras, ProCohat)
- [ ] Projects section extracted (NanoVLM, etc.)
- [ ] Achievements section extracted
- [ ] Technical Skills section extracted
- [ ] Success message displays after upload
- [ ] Data visible in Supabase dashboard

## Database Verification

1. Go to Supabase dashboard
2. Click **Table Editor**
3. Click on `students` table
   - Should see 1 row with student data
4. Click on `resume_sections` table
   - Should see multiple rows (one for each section)

## Troubleshooting

### Backend won't start
- Check Python version: `python --version` (should be 3.9+)
- Check if port 8000 is already in use
- Check if all packages installed: `pip list`

### Frontend won't start
- Check Node version: `node --version` (should be 18+)
- Try deleting `node_modules` and running `npm install` again
- Check if port 3000 is already in use

### Upload fails
- Check if backend is running (http://localhost:8000 should show a message)
- Check browser console for errors (F12)
- Verify Supabase credentials in `backend/.env`

### No data in Supabase
- Verify SQL schema was executed correctly
- Check backend logs for errors
- Try uploading again

## Success Criteria

Part 1 is successful if:

1. ✅ Resume uploads without errors
2. ✅ All sections are extracted correctly
3. ✅ Data is stored in Supabase
4. ✅ Data can be retrieved from database
5. ✅ UI looks clean and minimalistic (Apple-style)

## Ready for Part 2?

Once all tests pass, let me know and we'll proceed to Part 2: Greeting and Conversation!
