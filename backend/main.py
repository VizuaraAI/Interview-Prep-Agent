from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from docling.document_converter import DocumentConverter
import os
import tempfile
from typing import Dict, List
import re
from supabase import create_client, Client
from dotenv import load_dotenv
import uuid
import PyPDF2

load_dotenv()

app = FastAPI(title="ML Interview Agent - Resume Upload")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)


def extract_name_from_pdf(pdf_path: str) -> str:
    """Extract name directly from PDF first page (bypasses Docling's header skipping issue)"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            if len(pdf_reader.pages) > 0:
                first_page = pdf_reader.pages[0]
                text = first_page.extract_text()

                # Get first non-empty line that looks like a name
                lines = text.split('\n')
                for line in lines[:10]:  # Check first 10 lines
                    line_stripped = line.strip()

                    # Skip empty lines
                    if not line_stripped:
                        continue

                    # Skip lines with special characters (likely contact info or URLs)
                    if '@' in line_stripped or 'http' in line_stripped.lower() or '|' in line_stripped:
                        continue

                    # Skip lines that are all numbers or have + (phone numbers)
                    if line_stripped.replace('+', '').replace('-', '').replace(' ', '').isdigit():
                        continue

                    # Must have 2-5 words
                    words = line_stripped.split()
                    if 2 <= len(words) <= 5:
                        # Check it's not a section header
                        section_keywords = ['education', 'experience', 'project', 'skill', 'summary', 'objective']
                        if not any(kw in line_stripped.lower() for kw in section_keywords):
                            return line_stripped
    except Exception as e:
        print(f"Error extracting name from PDF: {e}")

    return ""


def get_first_name(full_name: str) -> str:
    """Extract first name from full name"""
    if not full_name:
        return ""

    # Split by spaces and take first part
    parts = full_name.strip().split()
    return parts[0] if parts else ""


def extract_contact_info(text: str, pdf_path: str = None) -> Dict[str, str]:
    """Extract name, email, phone, and links from resume"""
    contact_info = {
        "name": "",
        "email": "",
        "phone": "",
        "linkedin": "",
        "github": "",
        "portfolio": ""
    }

    # Try to extract name from PDF directly (more reliable than Docling for headers)
    if pdf_path:
        name_from_pdf = extract_name_from_pdf(pdf_path)
        if name_from_pdf:
            contact_info["name"] = name_from_pdf
        else:
            # Fall back to trying to extract from Docling text
            lines = text.split('\n')
            for line in lines[:10]:
                line_stripped = line.strip()
                if not line_stripped or line_stripped in ['---', '___', '===']:
                    continue

                name_text = line_stripped.replace('## ', '').replace('# ', '').strip()
                words = name_text.split()
                if 2 <= len(words) <= 5:
                    if name_text.isupper():
                        contact_info["name"] = name_text.title()
                    else:
                        contact_info["name"] = name_text
                    break

    # Find phone
    phone_pattern = r'\+[\d\-]{10,}'
    phone_match = re.search(phone_pattern, text)
    if phone_match:
        contact_info["phone"] = phone_match.group().strip()

    # Find email - look for actual email addresses
    email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
    email_match = re.search(email_pattern, text)
    if email_match:
        contact_info["email"] = email_match.group()

    # Find LinkedIn URL
    linkedin_pattern = r'linkedin\.com/in/[\w\-]+'
    linkedin_match = re.search(linkedin_pattern, text, re.IGNORECASE)
    if linkedin_match:
        contact_info["linkedin"] = linkedin_match.group()

    # Find GitHub URL
    github_pattern = r'github\.com/[\w\-]+'
    github_match = re.search(github_pattern, text, re.IGNORECASE)
    if github_match:
        contact_info["github"] = github_match.group()

    return contact_info


def parse_resume_sections(text: str) -> Dict[str, str]:
    """Parse resume into sections from Docling markdown format"""
    sections = {}

    # Define section headers to look for
    section_headers = [
        "Education",
        "Work Experience",
        "Projects",
        "Achievements",
        "Technical Skills",
        "Key Courses Taken"
    ]

    # Split text into lines
    lines = text.split('\n')

    current_section = None
    current_content = []

    for i, line in enumerate(lines):
        line_stripped = line.strip()

        # Remove markdown ## prefix for comparison
        line_clean = line_stripped.replace('## ', '').replace('#', '').strip()

        # Check if line is a section header
        is_header = False
        for header in section_headers:
            # Match both "## Section" and "Section" formats
            if line_clean == header or line_stripped == header:
                is_header = True
                # Save previous section
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()

                # Start new section
                current_section = header
                current_content = []
                break

        if not is_header and current_section:
            # Skip empty lines at the start of a section
            if line_stripped or current_content:
                # Don't include the person's name heading if it appears
                if not (line_stripped.startswith('## ') and len(line_stripped.split()) <= 4):
                    current_content.append(line)

    # Save last section
    if current_section and current_content:
        sections[current_section] = '\n'.join(current_content).strip()

    return sections


@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    """Upload and process resume PDF"""

    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        # Extract text using Docling
        converter = DocumentConverter()
        result = converter.convert(tmp_file_path)

        # Export to markdown for better structure preservation
        extracted_text = result.document.export_to_markdown()

        # Extract contact info (pass PDF path for direct name extraction)
        contact_info = extract_contact_info(extracted_text, pdf_path=tmp_file_path)

        # Parse sections
        sections = parse_resume_sections(extracted_text)

        # Store in Supabase
        # Insert student record
        student_data = {
            "name": contact_info["name"],
            "email": contact_info["email"],
            "phone": contact_info["phone"],
            "linkedin": contact_info["linkedin"],
            "github": contact_info["github"],
            "portfolio": contact_info["portfolio"],
            "resume_file_path": file.filename
        }

        student_response = supabase.table("students").insert(student_data).execute()
        student_id = student_response.data[0]["id"]

        # Insert resume sections
        section_records = []
        for heading, content in sections.items():
            section_records.append({
                "student_id": student_id,
                "heading": heading,
                "content": content
            })

        if section_records:
            supabase.table("resume_sections").insert(section_records).execute()

        # Clean up temp file
        os.unlink(tmp_file_path)

        return {
            "success": True,
            "student_id": student_id,
            "contact_info": contact_info,
            "sections": sections,
            "message": "Resume uploaded and processed successfully"
        }

    except Exception as e:
        # Clean up temp file if it exists
        if 'tmp_file_path' in locals():
            try:
                os.unlink(tmp_file_path)
            except:
                pass

        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "ML Interview Agent Backend - Part 1: Resume Upload"}


@app.get("/student/{student_id}")
async def get_student(student_id: str):
    """Get student data by ID"""
    try:
        # Get student info
        student_response = supabase.table("students").select("*").eq("id", student_id).execute()

        if not student_response.data:
            raise HTTPException(status_code=404, detail="Student not found")

        student = student_response.data[0]

        # Get resume sections
        sections_response = supabase.table("resume_sections").select("*").eq("student_id", student_id).execute()

        sections = {}
        for section in sections_response.data:
            sections[section["heading"]] = section["content"]

        return {
            "student": student,
            "sections": sections
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching student data: {str(e)}")


@app.post("/start-conversation/{student_id}")
async def start_conversation(student_id: str):
    """Start a conversation/interview with the student"""
    from conversation import generate_greeting, create_resume_summary, text_to_speech
    import base64

    try:
        # Get student info and sections
        student_response = supabase.table("students").select("*").eq("id", student_id).execute()
        if not student_response.data:
            raise HTTPException(status_code=404, detail="Student not found")

        student = student_response.data[0]

        # Get resume sections
        sections_response = supabase.table("resume_sections").select("*").eq("student_id", student_id).execute()
        sections = {}
        for section in sections_response.data:
            sections[section["heading"]] = section["content"]

        # Create resume summary for context
        resume_summary = create_resume_summary(sections)

        # Get first name for more natural conversation
        first_name = get_first_name(student["name"])

        # Generate greeting
        greeting_text = generate_greeting(first_name, resume_summary)

        # Generate voice audio
        audio_bytes = text_to_speech(greeting_text)
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8') if audio_bytes else None

        # Create conversation record
        conversation_data = {
            "student_id": student_id,
            "phase": "greeting"
        }
        conversation_response = supabase.table("conversations").insert(conversation_data).execute()
        conversation_id = conversation_response.data[0]["id"]

        # Store assistant message
        message_data = {
            "conversation_id": conversation_id,
            "role": "assistant",
            "content": greeting_text
        }
        supabase.table("messages").insert(message_data).execute()

        return {
            "conversation_id": conversation_id,
            "message": greeting_text,
            "audio": audio_base64,
            "phase": "greeting"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting conversation: {str(e)}")


@app.post("/speech-to-text")
async def speech_to_text(file: UploadFile = File(...)):
    """Convert speech audio to text using OpenAI Whisper"""
    from openai import OpenAI
    import os

    try:
        # Save uploaded audio temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        # Use OpenAI Whisper to transcribe
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        with open(tmp_file_path, 'rb') as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )

        # Clean up temp file
        os.unlink(tmp_file_path)

        return {
            "success": True,
            "text": transcription.text
        }

    except Exception as e:
        # Clean up temp file if it exists
        if 'tmp_file_path' in locals():
            try:
                os.unlink(tmp_file_path)
            except:
                pass

        raise HTTPException(status_code=500, detail=f"Error transcribing audio: {str(e)}")


@app.post("/continue-conversation/{conversation_id}")
async def continue_conversation_endpoint(conversation_id: str, user_message: Dict[str, str]):
    """Continue the conversation with user's response"""
    from conversation import (
        continue_conversation, continue_project_questions, start_project_questions,
        start_factual_questions, continue_factual_questions,
        create_resume_summary, text_to_speech, is_ready_for_technical
    )
    from knowledge_base import extract_student_topics, select_next_question
    import base64

    try:
        # Get conversation
        conversation_response = supabase.table("conversations").select("*").eq("id", conversation_id).execute()
        if not conversation_response.data:
            raise HTTPException(status_code=404, detail="Conversation not found")

        conversation = conversation_response.data[0]
        student_id = conversation["student_id"]
        current_phase = conversation["phase"]

        user_text = user_message.get("message", "")

        # Store user message
        user_msg_data = {
            "conversation_id": conversation_id,
            "role": "user",
            "content": user_text
        }
        supabase.table("messages").insert(user_msg_data).execute()

        # Get student info
        student_response = supabase.table("students").select("*").eq("id", student_id).execute()
        student = student_response.data[0]

        # Get resume sections
        sections_response = supabase.table("resume_sections").select("*").eq("student_id", student_id).execute()
        sections = {}
        for section in sections_response.data:
            sections[section["heading"]] = section["content"]

        resume_summary = create_resume_summary(sections)
        projects = sections.get("Projects", "")

        # Create full resume text for RAG similarity
        resume_text = ""
        for section_name in ["Projects", "Work Experience", "Technical Skills"]:
            if section_name in sections:
                resume_text += f"\n{section_name}:\n{sections[section_name]}\n"

        # Get first name for more natural conversation
        first_name = get_first_name(student["name"])

        # Get conversation history for context
        messages_response = supabase.table("messages").select("*").eq("conversation_id", conversation_id).order("created_at").execute()
        message_history = []
        for msg in messages_response.data:
            message_history.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        # Get conversation metadata
        project_q_count = conversation.get("project_questions_count", 0)
        factual_q_count = conversation.get("factual_questions_count", 0)
        student_topics = conversation.get("student_topics", [])
        questions_asked = conversation.get("questions_asked", [])
        question_metadata = None  # Will be set if we're asking a factual question

        # Check for phase transition
        if current_phase == "greeting" and is_ready_for_technical(user_text):
            # Transition to project questions (Phase III)
            supabase.table("conversations").update({
                "phase": "project_questions",
                "project_questions_count": 1
            }).eq("id", conversation_id).execute()

            assistant_response = start_project_questions(first_name, projects)
            current_phase = "project_questions"

        elif current_phase == "project_questions":
            # Check if we should transition to factual questions (after ~5 project questions)
            if project_q_count >= 5:
                # Extract student topics if not done yet
                if not student_topics:
                    student_topics = extract_student_topics(sections)

                # Get first factual question with similarity scoring and topic diversity
                next_q = select_next_question([], student_topics, resume_text, topics_covered={})

                # Transition to factual questions (Phase IV)
                supabase.table("conversations").update({
                    "phase": "factual_questions",
                    "student_topics": student_topics,
                    "questions_asked": [next_q["question"]],
                    "factual_questions_count": 1
                }).eq("id", conversation_id).execute()

                assistant_response = start_factual_questions(first_name, next_q)
                current_phase = "factual_questions"

                # Store the question metadata for response
                question_metadata = {
                    "similarity_score": next_q.get("similarity_score"),
                    "max_similarity": next_q.get("max_similarity"),
                    "match_reason": next_q.get("match_reason"),
                    "matched_topics": next_q.get("matched_topics", []),
                    "current_topic": next_q.get("topic"),
                    "question_text": next_q.get("question"),
                    "question_source": next_q.get("topic")  # The topic is the section name in ML_QUESTIONS
                }
            else:
                # Continue project questions
                supabase.table("conversations").update({
                    "project_questions_count": project_q_count + 1
                }).eq("id", conversation_id).execute()

                assistant_response = continue_project_questions(message_history, first_name, projects)

        elif current_phase == "factual_questions":
            # Continue factual questions
            # Check if this is the last question (after ~5 factual questions)
            is_final = factual_q_count >= 5

            if not is_final:
                # Calculate topics covered so far to ensure diversity
                topics_covered = {}
                from knowledge_base import ML_QUESTIONS
                for asked_q in (questions_asked or []):
                    # Find which topic this question belongs to
                    for topic, questions in ML_QUESTIONS.items():
                        if asked_q in questions:
                            topics_covered[topic] = topics_covered.get(topic, 0) + 1
                            break

                print(f"📊 Topics covered so far: {topics_covered}")

                # Get next question with similarity scoring and topic diversity
                next_q = select_next_question(
                    questions_asked or [],
                    student_topics or [],
                    resume_text,
                    topics_covered=topics_covered
                )
                updated_questions = (questions_asked or []) + [next_q["question"]]

                supabase.table("conversations").update({
                    "questions_asked": updated_questions,
                    "factual_questions_count": factual_q_count + 1
                }).eq("id", conversation_id).execute()

                assistant_response = continue_factual_questions(message_history, first_name, next_q, is_final=False)

                # Store the question metadata for response
                question_metadata = {
                    "similarity_score": next_q.get("similarity_score"),
                    "max_similarity": next_q.get("max_similarity"),
                    "match_reason": next_q.get("match_reason"),
                    "matched_topics": next_q.get("matched_topics", []),
                    "current_topic": next_q.get("topic"),
                    "question_text": next_q.get("question"),
                    "question_source": next_q.get("topic")  # The topic is the section name in ML_QUESTIONS
                }
            else:
                # Final question - wrap up
                assistant_response = continue_factual_questions(
                    message_history,
                    first_name,
                    {"topic": "", "question": ""},
                    is_final=True
                )

        else:
            # Still in greeting phase (Phase II)
            assistant_response = continue_conversation(message_history, first_name, resume_summary)

        # Generate voice audio
        audio_bytes = text_to_speech(assistant_response)
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8') if audio_bytes else None

        # Store assistant message
        assistant_msg_data = {
            "conversation_id": conversation_id,
            "role": "assistant",
            "content": assistant_response
        }
        supabase.table("messages").insert(assistant_msg_data).execute()

        response_data = {
            "message": assistant_response,
            "audio": audio_base64,
            "phase": current_phase
        }

        # Include student topics when in factual questions phase
        if current_phase == "factual_questions" and student_topics:
            response_data["student_topics"] = student_topics

        # Include question metadata (similarity scores, matching details)
        if question_metadata:
            response_data["question_metadata"] = question_metadata
            print(f"📊 Sending question metadata: {question_metadata}")
        else:
            print("⚠️ No question metadata to send")

        return response_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error continuing conversation: {str(e)}")


@app.post("/evaluate")
async def evaluate_interview(conversation_id: str):
    """
    Generate comprehensive evaluation report for a completed interview.
    Evaluates Project Phase and Factual Phase.
    """
    try:
        from evaluation import evaluate_project_phase, evaluate_factual_phase, generate_final_report

        # Fetch conversation data
        conversation = supabase.table("conversations").select("*").eq("id", conversation_id).single().execute()
        if not conversation.data:
            raise HTTPException(status_code=404, detail="Conversation not found")

        conv_data = conversation.data

        # Fetch student name
        student_id = conv_data.get("student_id")
        student_result = supabase.table("students").select("name").eq("id", student_id).single().execute()
        student_name = student_result.data['name'] if student_result.data else "Student"

        # Fetch all messages
        messages_result = supabase.table("messages").select("*").eq("conversation_id", conversation_id).order("created_at").execute()
        messages = messages_result.data

        if not messages:
            raise HTTPException(status_code=400, detail="No messages found for evaluation")

        # Separate messages by phase
        # Simple approach: Find when factual ML questions start by looking for typical ML terms
        # that appear in factual questions but not in project discussions

        project_messages = []
        factual_messages = []
        phase = "greeting"
        factual_started = False

        # Factual question indicators - terms that strongly suggest ML theory questions
        factual_indicators = [
            "dropout", "dropouts",
            "rnn", "lstm", "gru",
            "rcnn", "r-cnn",
            "variants of",
            "gradient descent",
            "backpropagation",
            "activation function",
            "overfitting",
            "regularization"
        ]

        for i, msg in enumerate(messages):
            content = msg.get("content", "").strip()
            content_lower = content.lower()
            role = msg.get("role")

            # Detect when project phase starts
            if phase == "greeting" and role == "assistant":
                # Look for project-related keywords indicating project discussion started
                project_indicators = [
                    "project caught my eye",
                    "tell me about your project",
                    "what project",
                    "describe your project",
                    "tell me more about",
                    "can you share more about",
                    "your project",
                    "you built",
                    "you developed",
                    "you implemented"
                ]
                if any(keyword in content_lower for keyword in project_indicators):
                    phase = "project"
                    print(f"🔍 Detected project phase starting at message {i}")

            # Detect when factual phase starts
            if phase == "project" and role == "assistant" and not factual_started:
                # Check if message is asking about ML theory/concepts (not project specifics)
                # Look for factual question patterns combined with transition phrases
                has_transition = any(phrase in content_lower for phrase in [
                    "let's switch", "move on", "another topic", "pivot a bit",
                    "dive into some ml", "ml theory", "ml concepts"
                ])
                has_factual_term = any(term in content_lower for term in factual_indicators + ["data augmentation", "augmentation"])

                if has_transition and has_factual_term:
                    phase = "factual"
                    factual_started = True
                    print(f"🔍 Detected factual phase starting at message {i}: {content[:100]}...")

            # Collect messages
            if phase == "project":
                project_messages.append(msg)
            elif phase == "factual":
                factual_messages.append(msg)

        print(f"📊 Evaluating: {len(project_messages)} project messages, {len(factual_messages)} factual messages")

        # Evaluate Project Phase
        project_evaluation = {}
        if len(project_messages) > 2:
            project_evaluation = evaluate_project_phase(project_messages, student_name)
        else:
            project_evaluation = {
                "overall_project_score": 0,
                "detail_level": 0,
                "clarity": 0,
                "socrates_metric": 0,
                "error": "Insufficient project discussion"
            }

        # Evaluate Factual Phase
        factual_evaluation = {}
        questions_asked = conv_data.get("questions_asked", [])
        if len(factual_messages) > 2:
            factual_evaluation = evaluate_factual_phase(factual_messages, questions_asked)
        else:
            factual_evaluation = {
                "factual_score": 0,
                "total_questions": 0,
                "correct_answers": 0,
                "error": "Insufficient factual discussion"
            }

        # Generate final report
        final_report = generate_final_report(student_name, project_evaluation, factual_evaluation)

        # TODO: Store evaluation in database (create evaluations table first)
        # evaluation_data = {
        #     "conversation_id": conversation_id,
        #     "student_name": student_name,
        #     "final_score": final_report["final_score"],
        #     "performance_level": final_report["performance_level"],
        #     "project_score": project_evaluation.get("overall_project_score", 0),
        #     "factual_score": factual_evaluation.get("factual_score", 0),
        #     "evaluation_details": final_report
        # }
        # supabase.table("evaluations").insert(evaluation_data).execute()

        return {
            "success": True,
            "evaluation": final_report
        }

    except Exception as e:
        print(f"Error during evaluation: {e}")
        raise HTTPException(status_code=500, detail=f"Error evaluating interview: {str(e)}")


@app.get("/evaluation/{conversation_id}")
async def get_evaluation(conversation_id: str):
    """Retrieve stored evaluation for a conversation."""
    try:
        result = supabase.table("evaluations").select("*").eq("conversation_id", conversation_id).single().execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Evaluation not found")

        return result.data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching evaluation: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
