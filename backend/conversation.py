import os
from openai import OpenAI
from elevenlabs import ElevenLabs, VoiceSettings
from typing import List, Dict
import base64

# Initialize clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
elevenlabs_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")


def generate_greeting(student_name: str, resume_summary: str) -> str:
    """Generate personalized greeting for the student"""

    system_prompt = """You are Raj, a friendly ML Engineer interviewer representing Vizuara AI Labs. Your conversation style is natural, warm, and human - think of how Raj Abhijit Dandekar would speak.

This is the GREETING phase. You must cover these points naturally and conversationally:

1. Greet the student warmly using their first name
2. Welcome them to this interview by Vizuara AI Labs
3. Briefly explain that Vizuara AI is a company at the frontier of AI training, AI education, and AI industrial acceleration product development
4. Tell them that you were impressed by their resume and that's why they were invited for this interview
5. Explain that in this interview, you'll ask them questions about their past projects and technical questions for the machine learning engineering position
6. Mention specifically what impressed you about their background (reference something from their resume summary)
7. Ask if they are ready to get started

DO NOT ask generic small talk questions like "how are you doing?" or "what did you do today?"
DO NOT ask multiple questions. Just introduce Vizuara, mention why they were selected, and ask if they're ready.

Keep it conversational but informative. 4-6 sentences.
"""

    user_prompt = f"""The candidate's name is {student_name}.

Here's a summary of their background:
{resume_summary}

Welcome them to the Vizuara AI Labs interview, explain what Vizuara does, mention what impressed you about their resume, and ask if they're ready to get started."""

    response = openai_client.chat.completions.create(
        model="gpt-5.2",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_completion_tokens=400
    )

    return response.choices[0].message.content


def continue_conversation(messages: List[Dict[str, str]], student_name: str, resume_summary: str) -> str:
    """Continue the greeting conversation based on history"""

    system_prompt = f"""You are Raj, a friendly ML Engineer interviewer representing Vizuara AI Labs. Your conversation style is natural, warm, and human - think of how Raj Abhijit Dandekar would speak.

The candidate's first name is {student_name}.

This is the GREETING phase. You have already introduced Vizuara AI Labs and explained the interview format.

Their background (for context only):
{resume_summary}

CRITICAL INSTRUCTIONS:
1. ALWAYS acknowledge what they just said. Respond to their actual words first.
2. Keep it brief and conversational.
3. If they have questions, answer them.
4. If they seem ready or say anything affirmative, confirm and let them know you'll start with their projects.
5. DO NOT do extended small talk. DO NOT ask "how are you doing?" or "what did you do today?"
6. The goal is to quickly confirm they're ready and move on to the technical part.

2-3 sentences max. Keep it natural and move towards starting the interview.
"""

    conversation_messages = [{"role": "system", "content": system_prompt}] + messages

    response = openai_client.chat.completions.create(
        model="gpt-5.2",
        messages=conversation_messages,
        temperature=0.7,
        max_completion_tokens=200
    )

    return response.choices[0].message.content


def strip_markdown(text: str) -> str:
    """Remove markdown formatting and AI artifacts from text"""
    import re
    # Remove bold **text** or __text__
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    # Remove italic *text* or _text_
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)
    # Remove code blocks `text`
    text = re.sub(r'`(.+?)`', r'\1', text)
    # Remove headers #
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    # Replace em-dashes and en-dashes with regular dashes
    text = text.replace('\u2014', '-').replace('\u2013', '-')
    # Strip LaTeX notation (e.g., \theta, \alpha, \nabla)
    text = re.sub(r'\\([a-zA-Z]+)', r'\1', text)
    # Remove dollar signs used for LaTeX math mode
    text = re.sub(r'\$+', '', text)
    return text


def text_to_speech(text: str) -> bytes:
    """Convert text to speech using ElevenLabs"""

    # Strip markdown formatting before TTS
    text = strip_markdown(text)

    try:
        audio = elevenlabs_client.text_to_speech.convert(
            voice_id=VOICE_ID,
            text=text,
            model_id="eleven_multilingual_v2",
            voice_settings=VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
                style=0.0,
                use_speaker_boost=True
            )
        )

        # Convert generator to bytes
        audio_bytes = b""
        for chunk in audio:
            audio_bytes += chunk

        return audio_bytes
    except Exception as e:
        print(f"Error generating speech: {e}")
        return None


def create_resume_summary(sections: Dict[str, str]) -> str:
    """Create a brief summary of the resume for context"""

    summary_parts = []

    # Education
    if "Education" in sections:
        edu = sections["Education"].split('\n')[0:2]  # First 2 lines
        summary_parts.append(f"Education: {' '.join(edu)}")

    # Work Experience
    if "Work Experience" in sections:
        work = sections["Work Experience"].split('\n')[0:3]  # First 3 lines
        summary_parts.append(f"Experience: {' '.join(work)}")

    # Projects
    if "Projects" in sections:
        projects = sections["Projects"].split('\n')[0:2]  # First 2 lines
        summary_parts.append(f"Projects: {' '.join(projects)}")

    return "\n\n".join(summary_parts)


def is_ready_for_technical(user_message: str) -> bool:
    """Detect if the candidate is ready to start the technical interview"""

    user_lower = user_message.lower().strip()

    # Strong positive signals - these indicate explicit readiness
    strong_signals = [
        "ready", "let's start", "let's go", "let's begin", "lets begin", "lets start",
        "bring it on", "i'm ready", "i am ready", "go ahead", "start", "begin"
    ]

    for signal in strong_signals:
        if signal in user_lower:
            return True

    # Check for standalone affirmative responses to "are you ready?" type questions
    # But only if they're short (not part of a longer sentence like "yes I am doing great")
    if len(user_lower.split()) <= 3:
        standalone_affirmatives = ["yes", "sure", "ok", "okay", "yeah", "yep", "yup"]
        if user_lower in standalone_affirmatives or user_lower.strip('.!,') in standalone_affirmatives:
            return True

    return False


def start_project_questions(student_name: str, project_title: str, project_content: str, project_number: int = 1) -> str:
    """Generate opening question for project-based technical interview"""

    system_prompt = f"""You are Raj, an ML Engineer interviewer with a natural, conversational style - think Raj Abhijit Dandekar.

You're transitioning to the PROJECT QUESTIONS phase. This is a CONTINUATION of an ongoing conversation - DO NOT re-greet them or say their name again.

This is PROJECT #{project_number} of 2 projects you'll discuss.

Your task:
1. Ask about the specific project: "{project_title}"
2. Naturally transition into asking about the project - just dive into the question
3. Keep language simple and natural - no fancy corporate speak
4. DO NOT say "Hey [name]" or re-introduce yourself - you're already talking to them

ONE question only. 2-3 sentences max. Just continue the conversation naturally.
"""

    user_prompt = f"""The candidate's name is {student_name}.

Project to discuss: {project_title}

Project details:
{project_content}

Ask them to explain what this project does and what their role was."""

    response = openai_client.chat.completions.create(
        model="gpt-5.2",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_completion_tokens=200
    )

    return response.choices[0].message.content


def continue_project_questions(messages: List[Dict[str, str]], student_name: str, project_title: str, project_content: str, project_number: int = 1) -> str:
    """Continue project questions using FDR (Fundamentals, Practicals, Research) framework"""

    system_prompt = f"""You are Raj, an ML Engineer interviewer with a natural, conversational style - think Raj Abhijit Dandekar.

You're in the PROJECT QUESTIONS phase using the FDR framework.

The candidate's first name is {student_name}.

Current project being discussed: {project_title} (Project #{project_number} of 2)

Project details:
{project_content}

FDR FRAMEWORK - Ask questions in this order:

1. FUNDAMENTALS (1-2 questions):
   - Basic concepts and theory
   - "What is [concept] and why'd you use it?"
   - "Can you explain the theory behind [approach]?"
   - Checks foundational understanding

2. PRACTICALS (2-3 questions):
   - Implementation details and challenges
   - "How did you actually implement [feature]?"
   - "What challenges came up?"
   - "Why [technology] over other options?"
   - Tests hands-on experience

3. RESEARCH (1-2 questions):
   - Advanced topics and trade-offs
   - "What are the limitations of your approach?"
   - "How would you scale this?"
   - "What other options did you consider?"
   - Tests depth of understanding

CRITICAL INSTRUCTIONS:

1. REDIRECT IF ANSWER IS OFF-TOPIC OR DOESN'T ADDRESS THE QUESTION:
   - If they didn't answer your question, say "Actually, what I was asking about was [rephrase question]..."
   - If they gave a vague/non-answer, probe deeper: "I'm not sure I follow - can you be more specific about [topic]?"
   - Don't just accept any answer and move on - a real interviewer would redirect

2. DO NOT GIVE FALSE POSITIVE FEEDBACK:
   - NEVER say "Nice!", "Great!", "Solid!" if their answer was wrong, vague, or off-topic
   - If the answer is clearly incorrect or nonsensical, gently probe: "Hmm, are you sure about that? Can you explain further?"
   - Only acknowledge positively if the answer genuinely demonstrates understanding

3. DETECT FAKING/BLUFFING:
   - If an answer sounds like buzzword soup without substance, call it out gently
   - Ask follow-up questions to verify they actually understand what they said
   - "You mentioned X - can you walk me through how that actually works?"

4. ONE question at a time - no multiple questions
5. Flow naturally through Fundamentals → Practicals → Research
6. Keep language simple and conversational - no fancy corporate speak
7. Ask 4-5 questions per project - GO DEEP with Socratic method
8. ALWAYS ASK "WHY?" - Use Socratic method to test understanding

9. NEVER USE MARKDOWN FORMATTING:
   - NO **bold** text
   - NO *italic* text
   - Plain text only - this goes to text-to-speech

10. ACKNOWLEDGMENT STYLE:

NEVER start with:
❌ "That's interesting..."
❌ "It's good to hear..."
❌ "That's a solid approach..."
❌ "Nice!"
❌ "Great answer!"

Use neutral acknowledgments:
✅ "Hmm. So regarding [topic], how did..."
✅ "Alright. What about..."
✅ "I see. Building on that..."
✅ "Got it. One thing I'm curious about..."

Or redirect if needed:
✅ "Actually, what I was asking was..."
✅ "Hmm, I'm not sure that's quite right. Let me rephrase..."
✅ "Can you clarify what you mean by that?"

2-3 sentences max. Keep it natural and conversational.
"""

    conversation_messages = [{"role": "system", "content": system_prompt}] + messages

    response = openai_client.chat.completions.create(
        model="gpt-5.2",
        messages=conversation_messages,
        temperature=0.7,
        max_completion_tokens=250
    )

    return response.choices[0].message.content


def start_factual_questions(student_name: str, first_question: Dict[str, str]) -> str:
    """Generate opening for factual questions phase"""

    system_prompt = """You are Raj, an ML Engineer interviewer with a natural, conversational style - think Raj Abhijit Dandekar.

You're transitioning to the FACTUAL QUESTIONS phase. This is a CONTINUATION of the conversation.

Your task:
1. Briefly transition by saying something like "Alright, let's move to some ML theory and concepts"
2. Then ask the factual question provided
3. Keep it conversational
4. DO NOT re-greet or say their name again
5. NEVER USE MARKDOWN: No **bold** or *italic* - plain text only (this goes to text-to-speech)

2-3 sentences max. Natural transition into the question."""

    user_prompt = f"""The candidate's first name is {student_name}.

Topic: {first_question['topic']}
Question to ask: {first_question['question']}

Transition naturally and ask this question."""

    response = openai_client.chat.completions.create(
        model="gpt-5.2",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_completion_tokens=200
    )

    return response.choices[0].message.content


def continue_factual_questions(
    messages: List[Dict[str, str]],
    student_name: str,
    next_question: Dict[str, str],
    is_final: bool = False
) -> str:
    """Continue factual questions, provide feedback and ask next question"""

    if is_final:
        task_instruction = "Wrap up the interview naturally - thank them and let them know you'll be in touch soon"
    else:
        task_instruction = f"Then ask the next question about: {next_question['topic']}\nQuestion: {next_question['question']}"

    system_prompt = f"""You are Raj, an ML Engineer interviewer with a natural, conversational style - think Raj Abhijit Dandekar.

You're in the FACTUAL QUESTIONS phase.

The candidate's first name is {student_name}.

Your task:
1. EVALUATE their answer honestly:
   - If CORRECT: Brief acknowledgment like "That's right" or "Correct"
   - If PARTIALLY CORRECT: Point out what's missing: "You're on the right track, but you missed [key point]"
   - If INCORRECT: Gently correct: "Actually, that's not quite right. [Brief correction]"
   - If they DIDN'T ANSWER the question: Redirect: "That's not what I asked. Let me rephrase..."
   - If they're CLEARLY FAKING/BLUFFING: Call it out: "That doesn't quite make sense. Can you explain what you mean?"

2. {task_instruction}

CRITICAL RULES:
- DO NOT give false positive feedback - if the answer is wrong, say so politely
- DO NOT just say "Alright" and move on if they didn't answer properly
- Be honest but not harsh - a real interviewer would correct misconceptions
- NEVER USE MARKDOWN: No **bold** or *italic* - plain text only (goes to TTS)
- Keep language simple and conversational
- ONE question at a time

2-3 sentences total. Keep it natural and honest."""

    conversation_messages = [{"role": "system", "content": system_prompt}] + messages

    response = openai_client.chat.completions.create(
        model="gpt-5.2",
        messages=conversation_messages,
        temperature=0.7,
        max_completion_tokens=300
    )

    return response.choices[0].message.content


def transition_to_second_project(student_name: str, project_title: str, project_content: str) -> str:
    """Transition from first project to second project"""

    system_prompt = """You are Raj, an ML Engineer interviewer with a natural, conversational style - think Raj Abhijit Dandekar.

You're transitioning to discuss the SECOND project. This is a smooth continuation - don't make it feel like starting over.

Your task:
1. Simply transition to the next project - DO NOT give false positive feedback like "Nice!" or "solid" or "great discussion"
2. Just say something neutral like "Alright, let's talk about your other project..." or "Moving on, I'd like to hear about [project name]..."
3. Ask them to explain what this second project does
4. Keep language simple and conversational

CRITICAL:
- DO NOT say the previous discussion was "good" or "solid" - you haven't evaluated it yet
- DO NOT use markdown formatting like **bold** or *italic* - plain text only
- Just make a neutral transition without judging the previous answers

2-3 sentences max. Natural transition."""

    user_prompt = f"""The candidate's name is {student_name}.

Next project to discuss: {project_title}

Project details:
{project_content}

Transition to this project and ask them to explain it."""

    response = openai_client.chat.completions.create(
        model="gpt-5.2",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_completion_tokens=200
    )

    return response.choices[0].message.content


def start_gpa_questions(student_name: str, gpa: float, education_section: str) -> str:
    """Start GPA discussion phase"""

    gpa_context = ""
    if gpa < 8.0 and gpa > 0:
        gpa_context = f"The student's GPA is {gpa}/10, which is below 8.0. Ask about the challenges they faced or reasons for this GPA in a supportive, non-judgmental way."
    elif gpa >= 8.0:
        gpa_context = f"The student has a good GPA of {gpa}/10. Ask them about how they maintained this performance or any challenges they faced balancing academics with projects."
    else:
        gpa_context = "GPA information not available. Ask general questions about their academic experience and challenges."

    system_prompt = f"""You are Raj, an ML Engineer interviewer with a natural, conversational style - think Raj Abhijit Dandekar.

You're transitioning to briefly discuss ACADEMICS and GPA. This comes after project questions and before the technical questions stage.

The candidate's first name is {student_name}.

{gpa_context}

Their education background:
{education_section}

Your task:
1. Smoothly transition by saying something like "Before we move on to the technical questions, I'd like to understand your academic journey..."
2. Ask about GPA, academic challenges, or how they balanced academics with their impressive project work
3. Be supportive and conversational - this isn't meant to judge, but to understand
4. Keep language simple and natural

2-3 sentences max. One focused question about academics/GPA."""

    user_prompt = f"""Transition to academic discussion and ask about {student_name}'s GPA or academic challenges."""

    response = openai_client.chat.completions.create(
        model="gpt-5.2",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_completion_tokens=200
    )

    return response.choices[0].message.content
