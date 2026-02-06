"""
Evaluation Framework for ML Interview Simulation
Evaluates candidates on Project Questions and Factual Questions
"""

import os
from openai import OpenAI
from typing import List, Dict, Tuple
from supabase import Client

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def evaluate_project_phase(messages: List[Dict[str, str]], student_name: str) -> Dict[str, any]:
    """
    Evaluate Project Phase (Phase III) based on 3 metrics:
    1. Detail Level: How thoroughly do they explain their project?
    2. Clarity: How precisely do they use technical terms?
    3. Socrates Metric: How well do they answer follow-up questions? Are answers correct?
    """

    # Extract only project-related conversation
    conversation_text = "\n".join([
        f"{msg['role'].upper()}: {msg['content']}"
        for msg in messages
    ])

    system_prompt = """You are an expert ML interviewer evaluating a candidate's project discussion.

CRITICAL: Your evaluation MUST reference SPECIFIC things the student said in the interview. Quote their exact words when possible. Point out specific mistakes, good answers, or areas where they struggled. Avoid generic feedback.

Evaluate the candidate on THREE metrics (0-10 scale):

1. DETAIL LEVEL (0-10):
   - 9-10: Extremely detailed, explains implementation specifics, mentions exact numbers, architectures, challenges
   - 7-8: Good detail, covers main implementation points
   - 5-6: Moderate detail, covers basics but lacks depth
   - 3-4: Surface-level, vague descriptions
   - 0-2: Minimal detail, just mentions project name

2. CLARITY (0-10):
   - 9-10: Precise technical language, explains acronyms, mentions specific dimensions/parameters (e.g., "384-dim embeddings")
   - 7-8: Clear technical terms, mostly precise
   - 5-6: Mix of precise and vague terms
   - 3-4: Mostly vague, uses buzzwords without explanation
   - 0-2: Unclear, confusing explanations

3. SOCRATES METRIC (0-10):
   - Measures response quality to follow-up questions
   - 9-10: Insightful answers that go beyond surface, demonstrates deep understanding, answers are CORRECT
   - 7-8: Good answers, shows understanding, mostly correct
   - 5-6: Adequate answers but lacks depth, some correctness issues
   - 3-4: Struggles with follow-ups, incorrect or incomplete answers
   - 0-2: Cannot answer follow-ups, demonstrates lack of understanding

CRITICAL EVALUATION RULES:
1. For Socrates metric, you MUST verify technical correctness. Penalize incorrect answers heavily. QUOTE specific incorrect statements.
2. DETECT FAKING/BLUFFING: If the student gave answers that sound like buzzword soup, are technically nonsensical, or clearly don't understand what they're saying, call it out explicitly in the weaknesses.
3. If a student answered a different question than what was asked, note this as a weakness.
4. If the student said something technically INCORRECT, quote it and explain why it's wrong.

FAKING DETECTION EXAMPLES:
- "The fetching happens through the server component on Firebase" - This is vague and possibly incorrect. What does "fetching through server component" mean?
- "The cryptography helps analyze the transaction through noticing the difference between the public and private keys" - This is nonsensical. Cryptography doesn't "notice differences."
- If answers don't make technical sense, the student may be bluffing. Note this.

Return ONLY a JSON object with this exact format:
{
    "detail_level": <score 0-10>,
    "detail_justification": "<MUST include specific examples from interview. Quote what they said. E.g., 'When asked about X, they said \"...\" which shows...'  NOT generic statements>",
    "clarity": <score 0-10>,
    "clarity_justification": "<MUST quote specific technical terms they used or failed to use. E.g., 'They said \"...\" which was vague' or 'They precisely mentioned \"...\"'  NOT generic>",
    "socrates_metric": <score 0-10>,
    "socrates_justification": "<MUST reference specific Q&A exchanges. E.g., 'When asked about Y, they answered \"...\" which is incorrect because...' NOT generic>",
    "overall_project_score": <average of 3 metrics>,
    "faking_detected": <true/false - were there signs the student was bluffing or making things up?>,
    "faking_examples": ["<Quote nonsensical or bluffed answers if any>"],
    "strengths": ["<specific strength with EXACT quote or example from interview>", "<specific strength with quote>"],
    "weaknesses": ["<specific weakness with EXACT quote or example from interview>", "<specific weakness with quote>"],
    "improvement_suggestions": ["<specific, actionable suggestion directly tied to something they said or failed to explain>", "<specific suggestion>"],
    "honesty_note": "<If faking was detected, include advice like: 'It's better to say \"I don't know\" than to give incorrect answers that damage credibility.'>"
}"""

    user_prompt = f"""Evaluate {student_name}'s project discussion:

{conversation_text}

Provide scores and justifications for Detail Level, Clarity, and Socrates Metric."""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-5.2",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_completion_tokens=3000,
            response_format={"type": "json_object"}
        )

        import json
        raw_content = response.choices[0].message.content
        print(f"Project evaluation raw response length: {len(raw_content)}")
        evaluation = json.loads(raw_content)
        print(f"Project evaluation scores: detail={evaluation.get('detail_level')}, clarity={evaluation.get('clarity')}, socrates={evaluation.get('socrates_metric')}")
        return evaluation

    except Exception as e:
        print(f"Error evaluating project phase: {e}")
        import traceback
        traceback.print_exc()
        return {
            "detail_level": 0,
            "clarity": 0,
            "socrates_metric": 0,
            "overall_project_score": 0,
            "error": str(e)
        }


def evaluate_factual_phase(messages: List[Dict[str, str]], questions_asked: List[str]) -> Dict[str, any]:
    """
    Evaluate Factual Phase (Phase IV) based on correctness of answers.
    """

    # Extract Q&A pairs
    qa_pairs = []
    for i in range(len(messages) - 1):
        if messages[i]['role'] == 'assistant' and messages[i+1]['role'] == 'user':
            # Extract question from assistant message
            question = messages[i]['content']
            answer = messages[i+1]['content']
            qa_pairs.append({
                "question": question,
                "student_answer": answer
            })

    if not qa_pairs:
        return {
            "factual_score": 0,
            "total_questions": 0,
            "correct_answers": 0,
            "error": "No Q&A pairs found"
        }

    # Evaluate each answer
    evaluations = []
    for qa in qa_pairs:
        system_prompt = """You are an expert ML interviewer evaluating factual answers.

The question is from a curated ML interview question bank (andrewekhalel/MLQuestions or huyenchip.com/ml-interviews-book).

CRITICAL: Your justification MUST be SPECIFIC. Quote what the student said. Point out exactly what was wrong or right about their answer.

Evaluate if the student's answer is:
- CORRECT (10 points): Accurate, demonstrates understanding
- PARTIALLY CORRECT (5-7 points): Has right idea but missing details or minor errors
- INCORRECT (0-3 points): Wrong or demonstrates misunderstanding
- BLUFFING/FAKING (0-2 points): Answer is nonsensical, uses buzzwords without substance, or clearly shows they don't know but are trying to fake it

FAKING DETECTION:
- If the answer sounds like random technical words strung together without making sense
- If they answered a completely different question than what was asked
- If the answer is technically nonsensical (e.g., "cryptography analyzes by noticing differences")
- Note: It's better to say "I don't know" than to bluff - penalize faking heavily

Return ONLY a JSON object:
{
    "score": <0-10>,
    "correctness": "<correct/partially_correct/incorrect/bluffing>",
    "justification": "<MUST quote their answer and explain what's right/wrong. E.g., 'The student said \"...\" which is incorrect because... The correct answer should mention...' If bluffing detected, explain why the answer makes no sense.>",
    "expected_key_points": ["<key point 1>", "<key point 2>"],
    "appears_to_be_faking": <true/false>
}"""

        user_prompt = f"""Question: {qa['question']}

Student Answer: {qa['student_answer']}

Evaluate the correctness of this answer."""

        try:
            response = openai_client.chat.completions.create(
                model="gpt-5.2",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_completion_tokens=1500,
                response_format={"type": "json_object"}
            )

            import json
            eval_result = json.loads(response.choices[0].message.content)
            eval_result["question"] = qa["question"]
            eval_result["student_answer"] = qa["student_answer"]
            evaluations.append(eval_result)

        except Exception as e:
            print(f"Error evaluating Q&A: {e}")
            evaluations.append({
                "score": 0,
                "question": qa["question"],
                "error": str(e)
            })

    # Calculate overall factual score
    total_score = sum([e.get("score", 0) for e in evaluations])
    max_score = len(evaluations) * 10
    factual_score = (total_score / max_score * 10) if max_score > 0 else 0

    correct_count = sum([1 for e in evaluations if e.get("correctness") == "correct"])
    partial_count = sum([1 for e in evaluations if e.get("correctness") == "partially_correct"])

    return {
        "factual_score": round(factual_score, 2),
        "total_questions": len(evaluations),
        "correct_answers": correct_count,
        "partially_correct_answers": partial_count,
        "incorrect_answers": len(evaluations) - correct_count - partial_count,
        "detailed_evaluations": evaluations
    }


def generate_final_report(
    student_name: str,
    project_evaluation: Dict,
    factual_evaluation: Dict
) -> Dict[str, any]:
    """
    Generate comprehensive evaluation report combining both phases.
    """

    # Calculate weighted final score
    # Project Phase: 60% (more important - shows practical skills)
    # Factual Phase: 40% (tests theoretical knowledge)
    project_score = project_evaluation.get("overall_project_score", 0)
    factual_score = factual_evaluation.get("factual_score", 0)

    final_score = (project_score * 0.6) + (factual_score * 0.4)

    # Determine performance level
    if final_score >= 9:
        performance_level = "Exceptional"
    elif final_score >= 8:
        performance_level = "Excellent"
    elif final_score >= 7:
        performance_level = "Good"
    elif final_score >= 6:
        performance_level = "Satisfactory"
    elif final_score >= 5:
        performance_level = "Needs Improvement"
    else:
        performance_level = "Poor"

    report = {
        "student_name": student_name,
        "final_score": round(final_score, 2),
        "performance_level": performance_level,
        "project_phase": {
            "overall_score": project_score,
            "detail_level": project_evaluation.get("detail_level", 0),
            "clarity": project_evaluation.get("clarity", 0),
            "socrates_metric": project_evaluation.get("socrates_metric", 0),
            "strengths": project_evaluation.get("strengths", []),
            "weaknesses": project_evaluation.get("weaknesses", []),
            "justifications": {
                "detail": project_evaluation.get("detail_justification", ""),
                "clarity": project_evaluation.get("clarity_justification", ""),
                "socrates": project_evaluation.get("socrates_justification", "")
            }
        },
        "factual_phase": {
            "overall_score": factual_score,
            "total_questions": factual_evaluation.get("total_questions", 0),
            "correct_answers": factual_evaluation.get("correct_answers", 0),
            "partially_correct": factual_evaluation.get("partially_correct_answers", 0),
            "incorrect_answers": factual_evaluation.get("incorrect_answers", 0),
            "accuracy_rate": round(
                (factual_evaluation.get("correct_answers", 0) /
                 max(factual_evaluation.get("total_questions", 1), 1)) * 100, 1
            )
        },
        "improvement_suggestions": project_evaluation.get("improvement_suggestions", []),
        "next_steps": []  # Populated by dynamic recommendations stored in evaluations table
    }

    return report


def generate_dynamic_recommendations(
    eval_type: str,
    evaluation_data: Dict,
    conversation_messages: List[Dict[str, str]]
) -> List[str]:
    """Generate personalized recommendations using GPT based on actual conversation content."""

    import json

    conversation_text = "\n".join([
        f"{msg['role'].upper()}: {msg['content']}"
        for msg in conversation_messages
    ])

    if eval_type == "project":
        system_prompt = """You are an expert ML interview coach. Based on the student's actual project discussion and their evaluation scores, generate 3-5 specific, actionable recommendations.

CRITICAL RULES:
- Every recommendation MUST reference something specific the student said or failed to say
- Quote their exact words when pointing out issues
- Suggest concrete actions (not generic advice like "take a course")
- If they struggled explaining a concept, tell them exactly which concept and how to improve
- If they gave incorrect information, identify it and suggest what to study

Return a JSON object: {"recommendations": ["rec1", "rec2", ...]}"""
    else:
        system_prompt = """You are an expert ML interview coach. Based on the student's factual Q&A performance and their evaluation, generate 3-5 specific, actionable recommendations.

CRITICAL RULES:
- Reference the specific questions they got wrong or partially correct
- Quote their incorrect statements and explain the correct answer
- Suggest specific topics/papers/resources for the concepts they struggled with
- Be concrete: "Review backpropagation through time for RNNs" not "Study ML fundamentals"

Return a JSON object: {"recommendations": ["rec1", "rec2", ...]}"""

    user_prompt = f"""Evaluation results:
{json.dumps(evaluation_data, indent=2)}

Conversation transcript:
{conversation_text}

Generate specific, personalized recommendations."""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-5.2",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.4,
            max_completion_tokens=800,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)
        return result.get("recommendations", [])

    except Exception as e:
        print(f"Error generating dynamic recommendations: {e}")
        return ["Review the areas where you struggled during the interview."]
