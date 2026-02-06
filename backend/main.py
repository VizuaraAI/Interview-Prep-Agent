from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import os
import tempfile
from typing import Dict, List, Any
import re
from supabase import create_client, Client
from dotenv import load_dotenv
import uuid
import PyPDF2

load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI(title="ML Interview Agent - Resume Upload")

# CORS middleware - Allow frontend origins
# In production, set ALLOWED_ORIGINS env var to your Vercel domain
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)


def run_project_evaluation(conversation_id: str, student_name: str):
    """Background task to evaluate project phase and store results."""
    from evaluation import evaluate_project_phase, generate_dynamic_recommendations
    import json

    try:
        # Fetch project-phase messages using phase tag
        messages_result = supabase.table("messages").select("*").eq(
            "conversation_id", conversation_id
        ).eq("phase", "project_questions").order("created_at").execute()

        project_messages = [{"role": m["role"], "content": m["content"], "metadata": m.get("metadata")} for m in messages_result.data]

        if len(project_messages) > 2:
            evaluation = evaluate_project_phase(project_messages, student_name)
            recommendations = generate_dynamic_recommendations(
                "project", evaluation, project_messages
            )

            # Store in database
            supabase.table("evaluations").insert({
                "conversation_id": conversation_id,
                "eval_type": "project",
                "eval_data": json.dumps(evaluation),
                "recommendations": json.dumps(recommendations)
            }).execute()

            print(f"Project evaluation stored for conversation {conversation_id}")
        else:
            print(f"Not enough project messages to evaluate ({len(project_messages)})")
    except Exception as e:
        print(f"Error in background project evaluation: {e}")


def run_factual_evaluation(conversation_id: str, questions_asked: List[str]):
    """Background task to evaluate factual phase and store results."""
    from evaluation import evaluate_factual_phase, generate_dynamic_recommendations
    import json

    try:
        # Fetch factual-phase messages using phase tag
        messages_result = supabase.table("messages").select("*").eq(
            "conversation_id", conversation_id
        ).eq("phase", "factual_questions").order("created_at").execute()

        factual_messages = [{"role": m["role"], "content": m["content"], "metadata": m.get("metadata")} for m in messages_result.data]

        if len(factual_messages) > 2:
            evaluation = evaluate_factual_phase(factual_messages, questions_asked)
            recommendations = generate_dynamic_recommendations(
                "factual", evaluation, factual_messages
            )

            # Store in database
            supabase.table("evaluations").insert({
                "conversation_id": conversation_id,
                "eval_type": "factual",
                "eval_data": json.dumps(evaluation),
                "recommendations": json.dumps(recommendations)
            }).execute()

            print(f"Factual evaluation stored for conversation {conversation_id}")
        else:
            print(f"Not enough factual messages to evaluate ({len(factual_messages)})")
    except Exception as e:
        print(f"Error in background factual evaluation: {e}")


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


def extract_top_two_projects(projects_section: str) -> List[Dict[str, str]]:
    """
    Extract the top 2 projects from the projects section.
    Returns list of dicts with 'title' and 'content' for each project.
    """
    if not projects_section:
        return []

    projects = []
    lines = projects_section.split('\n')
    current_project = None
    current_content = []

    for line in lines:
        line_stripped = line.strip()

        # Project titles are usually bold or marked with ** or have specific formatting
        # Or are standalone lines with project names
        is_project_title = False

        # Check if it looks like a project title
        if line_stripped and not line_stripped.startswith('-') and not line_stripped.startswith('•'):
            # If it's a short line (likely a title) or contains certain keywords
            words = line_stripped.split()
            if len(words) <= 10 or any(keyword in line_stripped.lower() for keyword in ['project', 'system', 'application', 'platform', 'tool']):
                # Likely a project title
                if current_project is not None:
                    # Save previous project
                    projects.append({
                        'title': current_project,
                        'content': '\n'.join(current_content).strip()
                    })
                current_project = line_stripped.replace('**', '').replace('*', '').strip()
                current_content = []
                is_project_title = True

        if not is_project_title and current_project is not None:
            current_content.append(line)

    # Save last project
    if current_project is not None and current_content:
        projects.append({
            'title': current_project,
            'content': '\n'.join(current_content).strip()
        })

    # Return top 2 projects (first two are usually most important)
    return projects[:2] if len(projects) >= 2 else projects


def extract_gpa(education_section: str) -> float:
    """
    Extract GPA from education section.
    Returns GPA as float, or 0 if not found.
    """
    if not education_section:
        return 0.0

    # Look for GPA patterns like "GPA: 8.5", "CGPA: 8.5/10", "Grade: 8.5"
    import re

    # Common GPA patterns
    patterns = [
        r'gpa[:\s]+(\d+\.?\d*)',
        r'cgpa[:\s]+(\d+\.?\d*)',
        r'grade[:\s]+(\d+\.?\d*)',
        r'percentage[:\s]+(\d+\.?\d*)%?'
    ]

    for pattern in patterns:
        match = re.search(pattern, education_section.lower())
        if match:
            try:
                gpa = float(match.group(1))
                # Normalize percentage to 10-point scale if it's > 10
                if gpa > 10 and gpa <= 100:
                    gpa = gpa / 10
                return gpa
            except ValueError:
                continue

    return 0.0


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

        # Extract structured data using Gemini API
        import json as json_module
        model = genai.GenerativeModel("gemini-2.0-flash")
        pdf_file = genai.upload_file(tmp_file_path, mime_type="application/pdf")
        response = model.generate_content([
            """Analyze this resume PDF and extract ALL information into the following JSON structure.
Be thorough - extract EVERY detail from the resume. Do not skip or summarize anything.

Return ONLY valid JSON (no markdown fences, no extra text):
{
  "contact_info": {
    "name": "Full Name",
    "email": "email@example.com",
    "phone": "phone number with country code",
    "linkedin": "full LinkedIn URL (e.g. linkedin.com/in/username)",
    "github": "full GitHub URL (e.g. github.com/username)",
    "portfolio": "portfolio URL if any"
  },
  "gpa": 0.0,
  "top_projects": [
    {"title": "Actual descriptive project name", "content": "Complete project description with all bullet points and details"},
    {"title": "Actual descriptive project name", "content": "Complete project description with all bullet points and details"}
  ],
  "sections": {
    "Education": "Complete education details including institution names, degrees, dates, GPA/CGPA, relevant coursework - preserve ALL details",
    "Work Experience": "Complete work experience with company names, roles, dates, and ALL bullet points describing responsibilities and achievements",
    "Projects": "ALL projects with their full names, descriptions, tech stacks, dates, and every bullet point",
    "Technical Skills": "ALL skills listed - programming languages, frameworks, tools, databases, etc.",
    "Achievements": "ALL achievements, awards, certifications, competitions",
    "Key Courses Taken": "ALL relevant courses mentioned"
  }
}

IMPORTANT RULES:
- For "contact_info": Extract LinkedIn and GitHub URLs even if they are hidden behind icons or hyperlinked text. Look for any clickable links in the PDF that point to linkedin.com or github.com. If the resume shows icons or text like "LinkedIn" or "GitHub" with embedded hyperlinks, extract the actual destination URLs.
- For "top_projects": Pick the 2 most impressive/relevant projects. The "title" MUST be the actual descriptive project name (e.g., "Machine learning aided global quarantine analysis during Covid-19"), NEVER a location (like "Cambridge, MA"), a date (like "2024"), or a generic label. The title should clearly describe what the project is about.
- For "sections": use EXACTLY these keys where applicable: "Education", "Work Experience", "Projects", "Technical Skills", "Achievements", "Key Courses Taken"
- If the resume has additional sections not in the list above, include them with their original heading name
- For each section, include the COMPLETE content - every bullet point, every detail, every date
- For "gpa": extract GPA/CGPA as a float (e.g., 8.5). If percentage, divide by 10. If not found, use 0.0
- For contact fields not found in the resume, use empty string ""
- Do NOT summarize or shorten any content - include everything verbatim from the resume""",
            pdf_file
        ])

        # Parse Gemini's JSON response
        response_text = response.text.strip()
        # Remove markdown code fences if present
        if response_text.startswith("```"):
            response_text = response_text.split("\n", 1)[1]
            if response_text.endswith("```"):
                response_text = response_text[:-3].strip()
            elif "```" in response_text:
                response_text = response_text[:response_text.rfind("```")].strip()

        parsed_data = json_module.loads(response_text)

        contact_info = parsed_data.get("contact_info", {})
        # Ensure all expected keys exist
        for key in ["name", "email", "phone", "linkedin", "github", "portfolio"]:
            if key not in contact_info:
                contact_info[key] = ""

        sections = parsed_data.get("sections", {})
        top_projects = parsed_data.get("top_projects", [])
        gpa = float(parsed_data.get("gpa", 0.0))

        # Fallback: if Gemini didn't extract the name, try PyPDF2
        if not contact_info.get("name"):
            contact_info["name"] = extract_name_from_pdf(tmp_file_path)

        # Store in Supabase
        # Insert student record
        student_data = {
            "name": contact_info["name"],
            "email": contact_info["email"],
            "phone": contact_info["phone"],
            "linkedin": contact_info["linkedin"],
            "github": contact_info["github"],
            "portfolio": contact_info["portfolio"],
            "resume_file_path": file.filename,
            "gpa": gpa
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

        # Store top projects as a special section for easy retrieval
        import json as json_mod
        if top_projects:
            supabase.table("resume_sections").insert({
                "student_id": student_id,
                "heading": "_top_projects",
                "content": json_mod.dumps(top_projects)
            }).execute()

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
    """Root endpoint"""
    return {"message": "ML Interview Agent Backend - API is running"}


@app.get("/health")
async def health_check():
    """Health check endpoint for deployment"""
    return {"status": "healthy", "service": "interview-prep-agent"}


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
    from conversation import generate_greeting, create_resume_summary, text_to_speech, strip_markdown
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

        # Get top 2 projects (extracted by Gemini during upload)
        import json
        top_projects_section = sections.get("_top_projects", "")
        if top_projects_section:
            top_projects = json.loads(top_projects_section) if isinstance(top_projects_section, str) else top_projects_section
        else:
            # Fallback to old parser if Gemini data not available
            projects_section = sections.get("Projects", "")
            top_projects = extract_top_two_projects(projects_section)

        # Create resume summary for context
        resume_summary = create_resume_summary(sections)

        # Get first name for more natural conversation
        first_name = get_first_name(student["name"])

        # Generate greeting and strip markdown
        greeting_text = generate_greeting(first_name, resume_summary)
        greeting_text = strip_markdown(greeting_text)

        # Generate voice audio
        audio_bytes = text_to_speech(greeting_text)
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8') if audio_bytes else None

        # Create conversation record with projects data
        import json
        conversation_data = {
            "student_id": student_id,
            "phase": "greeting",
            "projects_data": json.dumps(top_projects) if top_projects else None,
            "current_project_index": 0,
            "project_1_questions_count": 0,
            "project_2_questions_count": 0
        }
        conversation_response = supabase.table("conversations").insert(conversation_data).execute()
        conversation_id = conversation_response.data[0]["id"]

        # Store assistant message
        message_data = {
            "conversation_id": conversation_id,
            "role": "assistant",
            "content": greeting_text,
            "phase": "greeting"
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
async def continue_conversation_endpoint(conversation_id: str, user_message: Dict[str, Any], background_tasks: BackgroundTasks):
    """Continue the conversation with user's response"""
    from conversation import (
        continue_conversation, continue_project_questions, start_project_questions,
        start_factual_questions, continue_factual_questions,
        create_resume_summary, text_to_speech, is_ready_for_technical,
        transition_to_second_project, start_gpa_questions, strip_markdown
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

        # Extract anti-cheat metadata from frontend
        response_time_seconds = user_message.get("response_time_seconds", None)
        paste_count = user_message.get("paste_count", 0)
        paste_char_count = user_message.get("paste_char_count", 0)
        suspicious_typing = user_message.get("suspicious_typing", False)
        timer_expired = user_message.get("timer_expired", False)

        import json as json_meta
        anti_cheat_metadata = json_meta.dumps({
            "response_time_seconds": response_time_seconds,
            "paste_count": paste_count,
            "paste_char_count": paste_char_count,
            "suspicious_typing": suspicious_typing,
            "timer_expired": timer_expired
        })

        # Store user message (tagged with current phase before any transition)
        user_msg_data = {
            "conversation_id": conversation_id,
            "role": "user",
            "content": user_text,
            "phase": current_phase,
            "metadata": anti_cheat_metadata
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
        import json
        project_q_count = conversation.get("project_questions_count", 0)
        project_1_q_count = conversation.get("project_1_questions_count", 0)
        project_2_q_count = conversation.get("project_2_questions_count", 0)
        current_project_index = conversation.get("current_project_index", 0)
        projects_data = json.loads(conversation.get("projects_data", "[]")) if conversation.get("projects_data") else []
        factual_q_count = conversation.get("factual_questions_count", 0)
        student_topics = conversation.get("student_topics", [])
        questions_asked = conversation.get("questions_asked", [])
        question_metadata = None  # Will be set if we're asking a factual question
        gpa = student.get("gpa", 0.0)
        education_section = sections.get("Education", "")

        # Check for phase transition
        if current_phase == "greeting" and is_ready_for_technical(user_text):
            # Transition to project questions - start with first project
            if projects_data and len(projects_data) > 0:
                first_project = projects_data[0]
                supabase.table("conversations").update({
                    "phase": "project_questions",
                    "current_project_index": 0,
                    "project_1_questions_count": 1
                }).eq("id", conversation_id).execute()

                assistant_response = start_project_questions(
                    first_name,
                    first_project.get("title", ""),
                    first_project.get("content", ""),
                    project_number=1
                )
                current_phase = "project_questions"
            else:
                # No projects found, skip to factual questions
                current_phase = "greeting"
                assistant_response = continue_conversation(message_history, first_name, resume_summary)

        elif current_phase == "project_questions":
            # Handle project questions phase with TWO projects
            if current_project_index == 0:
                # Working on first project
                if project_1_q_count >= 4 and len(projects_data) > 1:
                    # Transition to second project (after 2-3 questions on first project)
                    second_project = projects_data[1]
                    supabase.table("conversations").update({
                        "current_project_index": 1,
                        "project_2_questions_count": 1
                    }).eq("id", conversation_id).execute()

                    assistant_response = transition_to_second_project(
                        first_name,
                        second_project.get("title", ""),
                        second_project.get("content", "")
                    )
                    current_project_index = 1
                else:
                    # Continue with first project
                    first_project = projects_data[0] if projects_data else {"title": "", "content": ""}
                    supabase.table("conversations").update({
                        "project_1_questions_count": project_1_q_count + 1
                    }).eq("id", conversation_id).execute()

                    assistant_response = continue_project_questions(
                        message_history,
                        first_name,
                        first_project.get("title", ""),
                        first_project.get("content", ""),
                        project_number=1
                    )

            elif current_project_index == 1:
                # Working on second project
                if project_2_q_count >= 4:
                    # Done with both projects, transition to GPA questions
                    supabase.table("conversations").update({
                        "phase": "gpa_questions",
                        "project_eval_triggered": True
                    }).eq("id", conversation_id).execute()

                    assistant_response = start_gpa_questions(first_name, gpa, education_section)
                    current_phase = "gpa_questions"

                    # Trigger project evaluation in background
                    background_tasks.add_task(
                        run_project_evaluation,
                        conversation_id,
                        student["name"]
                    )
                else:
                    # Continue with second project
                    second_project = projects_data[1] if len(projects_data) > 1 else {"title": "", "content": ""}
                    supabase.table("conversations").update({
                        "project_2_questions_count": project_2_q_count + 1
                    }).eq("id", conversation_id).execute()

                    assistant_response = continue_project_questions(
                        message_history,
                        first_name,
                        second_project.get("title", ""),
                        second_project.get("content", ""),
                        project_number=2
                    )

        elif current_phase == "gpa_questions":
            # After GPA discussion (1-2 exchanges), transition to factual questions
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

                # Trigger factual evaluation in background
                background_tasks.add_task(
                    run_factual_evaluation,
                    conversation_id,
                    questions_asked or []
                )

        else:
            # Still in greeting phase (Phase II)
            assistant_response = continue_conversation(message_history, first_name, resume_summary)

        # Strip markdown from response (for display and TTS)
        assistant_response = strip_markdown(assistant_response)

        # Generate voice audio
        audio_bytes = text_to_speech(assistant_response)
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8') if audio_bytes else None

        # Store assistant message (tagged with current phase after any transition)
        assistant_msg_data = {
            "conversation_id": conversation_id,
            "role": "assistant",
            "content": assistant_response,
            "phase": current_phase
        }
        supabase.table("messages").insert(assistant_msg_data).execute()

        # Determine if interview is truly complete (after final wrap-up)
        is_interview_complete = current_phase == "factual_questions" and factual_q_count >= 5

        response_data = {
            "message": assistant_response,
            "audio": audio_base64,
            "phase": current_phase,
            "interview_complete": is_interview_complete
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


@app.get("/evaluate/project/{conversation_id}")
async def get_project_evaluation(conversation_id: str):
    """Retrieve the project phase evaluation."""
    import json
    try:
        result = supabase.table("evaluations").select("*").eq(
            "conversation_id", conversation_id
        ).eq("eval_type", "project").execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Project evaluation not ready yet")

        eval_row = result.data[0]
        eval_data = json.loads(eval_row["eval_data"]) if isinstance(eval_row["eval_data"], str) else eval_row["eval_data"]
        recommendations = json.loads(eval_row["recommendations"]) if isinstance(eval_row.get("recommendations"), str) else eval_row.get("recommendations", [])

        return {
            "success": True,
            "evaluation": eval_data,
            "recommendations": recommendations
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching project evaluation: {str(e)}")


@app.get("/evaluate/factual/{conversation_id}")
async def get_factual_evaluation(conversation_id: str):
    """Retrieve the factual phase evaluation."""
    import json
    try:
        result = supabase.table("evaluations").select("*").eq(
            "conversation_id", conversation_id
        ).eq("eval_type", "factual").execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Factual evaluation not ready yet")

        eval_row = result.data[0]
        eval_data = json.loads(eval_row["eval_data"]) if isinstance(eval_row["eval_data"], str) else eval_row["eval_data"]
        recommendations = json.loads(eval_row["recommendations"]) if isinstance(eval_row.get("recommendations"), str) else eval_row.get("recommendations", [])

        return {
            "success": True,
            "evaluation": eval_data,
            "recommendations": recommendations
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching factual evaluation: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
