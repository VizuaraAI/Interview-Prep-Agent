# Part 2: Greeting and Conversation Setup

Part 2 adds AI-powered conversation with voice support for the greeting phase of the interview.

## What's New in Part 2

- **OpenAI GPT-4** integration for natural conversation
- **ElevenLabs voice synthesis** with your voice clone (Raj Dandekae)
- **Conversation tracking** in Supabase database
- **Real-time chat interface** with voice playback
- **Greeting phase** that:
  - Greets student by name
  - Makes small talk based on their resume
  - Asks about goals and motivation
  - Checks if they're ready to begin the technical interview

## Setup Instructions

### Step 1: Run Database Schema for Part 2

1. Go to your Supabase dashboard: https://supabase.com/dashboard
2. Click on **SQL Editor** (left sidebar)
3. Click **New Query**
4. Open the file `backend/schema_part2.sql` on your computer
5. Copy all the SQL content and paste it into the Supabase SQL Editor
6. Click **Run** to create the new tables:
   - `conversations`: Tracks interview sessions
   - `messages`: Stores conversation history

### Step 2: Verify Backend is Running

The backend should already be running with the new features. To verify:

```bash
curl http://localhost:8000/
```

You should see: `{"message":"ML Interview Agent Backend - Part 1: Resume Upload"}`

### Step 3: Verify Frontend is Running

The frontend should be running on http://localhost:3001

If not, start it:
```bash
cd frontend
npm run dev
```

## Testing Part 2

### Full Workflow Test:

1. **Upload a Resume**
   - Go to http://localhost:3001
   - Upload the Himanshu Kumar resume (or any other resume)
   - Click **Upload Resume**
   - Verify data is extracted correctly

2. **Start Interview**
   - After successful upload, click the **"Start Interview"** button
   - You'll be redirected to the interview page

3. **Test Greeting Conversation**
   - The interviewer (Raj) will greet you with:
     - Personalized greeting using your name
     - Small talk about your background
     - Questions about goals and motivation
   - **Voice should play automatically** for each interviewer message
   - Type your responses in the chat box
   - Press Enter to send (Shift+Enter for new line)

4. **Expected Conversation Flow**:
   ```
   Raj: "Hi Himanshu! It's great to have you here today. I see you're currently studying Computer Science at IIIT Nagpur and have impressive experience working with Generative AI at IIT Madras. How has your journey in AI been so far?"

   You: [Type your response about your AI journey]

   Raj: "That sounds exciting! What draws you to this ML Engineer position, and what are you hoping to achieve in your career?"

   You: [Share your goals and motivation]

   Raj: "Great! Are you ready to begin the technical portion of the interview?"

   You: "Yes, I'm ready!"
   ```

### What to Verify:

- [ ] Resume upload still works (Part 1)
- [ ] "Start Interview" button appears after upload
- [ ] Interview page loads correctly
- [ ] Raj's greeting mentions the student's name correctly
- [ ] Raj's message references details from the resume
- [ ] **Voice audio plays automatically** for Raj's messages
- [ ] You can type and send responses
- [ ] Conversation history displays correctly
- [ ] The conversation flows naturally (2-3 exchanges before asking if ready)

### Troubleshooting:

**No voice playing:**
- Check your browser allows audio autoplay
- Try clicking anywhere on the page first (browsers sometimes block autoplay)
- Check browser console for errors (F12)

**Conversation not starting:**
- Check backend logs: `tail -f /private/tmp/claude/...*/bfbdbe4.output`
- Verify API keys are correct in `backend/.env`
- Check Supabase schema was created successfully

**Backend errors:**
- Make sure OpenAI API key is valid
- Make sure ElevenLabs API key and Voice ID are correct
- Check that new tables exist in Supabase

## Database Tables

After running the schema, you should have these new tables:

### `conversations`
- Tracks each interview session
- Links to student
- Records phase (greeting, project_questions, etc.)
- Timestamps for start and completion

### `messages`
- Stores all chat messages
- Links to conversation
- Separates user vs assistant messages
- Can store audio URLs (currently base64 in response)

## API Endpoints (Part 2)

### POST `/start-conversation/{student_id}`
Starts a new interview conversation

**Response:**
```json
{
  "conversation_id": "uuid",
  "message": "Hi Himanshu! It's great to have you here...",
  "audio": "base64_encoded_audio"
}
```

### POST `/continue-conversation/{conversation_id}`
Continues the conversation

**Request:**
```json
{
  "message": "I'm excited to interview for this position..."
}
```

**Response:**
```json
{
  "message": "That's wonderful! What specific areas...",
  "audio": "base64_encoded_audio"
}
```

## Features in Part 2

### AI Conversation
- **GPT-4** generates natural, context-aware responses
- Remembers conversation history
- References student's resume details
- Guides conversation toward interview readiness

### Voice Synthesis
- **ElevenLabs** generates realistic voice
- Uses your voice clone (Raj Dandekae)
- Audio plays automatically for each response
- Base64 encoded for easy transmission

### Chat Interface
- Clean, Apple-style messaging UI
- Real-time message updates
- Loading indicators
- Keyboard shortcuts (Enter to send)
- Auto-scroll to latest message

## Next Steps

Once Part 2 is tested and working:

**Part 3: Project-based Questions** (Coming Next)
- Deep technical questions about student's projects
- Follow-up questions using FDR framework (Fundamentals, Practicals, Research)
- Evaluation of responses

**Part 4: Factual Questions** (Final Part)
- Questions from ML interview question banks
- Scoring and evaluation
- Learning pathway generation

---

## Success Criteria for Part 2

Part 2 is successful when:

✅ Resume upload works (Part 1 still functional)
✅ Interview starts after upload
✅ Raj greets student by name
✅ Conversation references resume details
✅ Voice plays for each message
✅ Natural 2-3 exchange conversation
✅ Conversation stored in Supabase
✅ Ready for Part 3

Let me know when Part 2 is working, and we'll move to Part 3!
