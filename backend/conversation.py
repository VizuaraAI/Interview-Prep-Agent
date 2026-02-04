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

    system_prompt = """You are Raj, a friendly ML Engineer interviewer. Your conversation style is natural, warm, and human - think of how Raj Abhijit Dandekar would speak.

This is the GREETING phase - keep it light and casual:
1. Greet the student warmly using their first name
2. Keep the language simple and conversational - no fancy or overly formal words
3. Make it feel like a genuine human conversation, not a corporate interview
4. DO NOT ask about projects, technical work, or resume details - that comes later
5. Just focus on making them feel comfortable

Keep it brief - 2-3 sentences max. Be warm and friendly.
"""

    user_prompt = f"""The candidate's name is {student_name}.

Here's a summary of their background:
{resume_summary}

Start the conversation with a warm greeting."""

    response = openai_client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=200
    )

    return response.choices[0].message.content


def continue_conversation(messages: List[Dict[str, str]], student_name: str, resume_summary: str) -> str:
    """Continue the greeting conversation based on history"""

    system_prompt = f"""You are Raj, a friendly ML Engineer interviewer. Your conversation style is natural, warm, and human - think of how Raj Abhijit Dandekar would speak.

The candidate's first name is {student_name}.

This is the GREETING phase - light small talk only. DO NOT ask about projects or technical topics yet.

Their background (for context only, don't interrogate):
{resume_summary}

CRITICAL INSTRUCTIONS:
1. ALWAYS acknowledge what they just said. Respond to their actual words first.
2. Keep language simple and natural - avoid fancy or corporate-sounding words
3. This is casual small talk - "How's your day going?" or "Feeling good about the interview?"
4. DO NOT ask about their projects, work experience, or technical stuff - that's for later
5. After 2-3 exchanges, ask if they're ready to dive into the technical part
6. Keep the vibe friendly and relaxed - like chatting with a colleague, not interrogating

2-3 sentences max. Keep it real and conversational.
"""

    conversation_messages = [{"role": "system", "content": system_prompt}] + messages

    response = openai_client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=conversation_messages,
        temperature=0.7,
        max_tokens=200
    )

    return response.choices[0].message.content


def text_to_speech(text: str) -> bytes:
    """Convert text to speech using ElevenLabs"""

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


def start_project_questions(student_name: str, projects: str) -> str:
    """Generate opening question for project-based technical interview"""

    system_prompt = """You are Raj, an ML Engineer interviewer with a natural, conversational style - think Raj Abhijit Dandekar.

You're transitioning to the PROJECT QUESTIONS phase. This is a CONTINUATION of an ongoing conversation - DO NOT re-greet them or say their name again.

Your task:
1. Pick the most interesting or complex project from their list
2. Naturally transition into asking about the project - just dive into the question
3. Keep language simple and natural - no fancy corporate speak
4. DO NOT say "Hey [name]" or re-introduce yourself - you're already talking to them

ONE question only. 2-3 sentences max. Just continue the conversation naturally.
"""

    user_prompt = f"""The candidate's name is {student_name}.

Their projects:
{projects}

Pick the most interesting project and ask them to explain what it does and what their role was."""

    response = openai_client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=200
    )

    return response.choices[0].message.content


def continue_project_questions(messages: List[Dict[str, str]], student_name: str, projects: str) -> str:
    """Continue project questions using FDR (Fundamentals, Practicals, Research) framework"""

    system_prompt = f"""You are Raj, an ML Engineer interviewer with a natural, conversational style - think Raj Abhijit Dandekar.

You're in the PROJECT QUESTIONS phase using the FDR framework.

The candidate's first name is {student_name}.

Their projects:
{projects}

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
1. Build on what they just said - be contextual and responsive
2. ONE question at a time - no multiple questions
3. Flow naturally through Fundamentals → Practicals → Research
4. Keep language simple and conversational - no fancy corporate speak
5. After 4-5 questions total, wrap up and suggest moving to general ML questions

6. ACKNOWLEDGMENT STYLE - THIS IS CRITICAL:

NEVER start with:
❌ "That's interesting..."
❌ "It's good to hear..."
❌ "That's a solid approach..."
❌ "Your approach to [topic] is..."
❌ "I appreciate your explanation..."

ALWAYS start with brief, natural acknowledgments:
✅ "Hmm. So regarding [topic], how did..."
✅ "Alright. What about..."
✅ "I see. Building on that..."
✅ "Got it. One thing I'm curious about..."
✅ "Well, that makes sense. Now..."

EXAMPLES:

Bad (AI-sounding):
"It's good to hear you put a lot of effort into testing! Testing is crucial for understanding how models perform. Speaking of which, when you were experimenting with NanoVLM, how did you select the architecture?"

Good (natural interviewer):
"Hmm. So when you were experimenting with NanoVLM, how did you select the right architecture?"

Bad (AI-sounding):
"Ablation studies are a solid approach! They really help in understanding component impact. Could you share what findings were most surprising?"

Good (natural interviewer):
"Alright. What findings from those ablation studies were most surprising to you?"

7. NO re-affirming what they said. Just acknowledge briefly and ask the next question.

2-3 sentences max. Keep it natural and conversational.
"""

    conversation_messages = [{"role": "system", "content": system_prompt}] + messages

    response = openai_client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=conversation_messages,
        temperature=0.7,
        max_tokens=250
    )

    return response.choices[0].message.content


def start_factual_questions(student_name: str, first_question: Dict[str, str]) -> str:
    """Generate opening for factual questions phase"""

    system_prompt = """You are Raj, an ML Engineer interviewer with a natural, conversational style - think Raj Abhijit Dandekar.

You're transitioning to the FACTUAL QUESTIONS phase. This is a CONTINUATION of the conversation.

Your task:
1. Briefly transition by saying something like "Alright, let's move to some ML theory and concepts"
2. Then ask the factual question provided
3. Keep it conversational and encouraging
4. DO NOT re-greet or say their name again

2-3 sentences max. Natural transition into the question."""

    user_prompt = f"""The candidate's first name is {student_name}.

Topic: {first_question['topic']}
Question to ask: {first_question['question']}

Transition naturally and ask this question."""

    response = openai_client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=200
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
1. Acknowledge their answer briefly - give quick feedback (good, interesting, needs work, etc.)
2. If their answer is strong, acknowledge it. If weak or incomplete, gently point out what's missing
3. {task_instruction}

CRITICAL:
- Keep feedback brief (1 sentence max)
- Be encouraging but honest
- Keep language simple and conversational
- ONE question at a time

2-3 sentences total. Keep it natural."""

    conversation_messages = [{"role": "system", "content": system_prompt}] + messages

    response = openai_client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=conversation_messages,
        temperature=0.7,
        max_tokens=300
    )

    return response.choices[0].message.content
