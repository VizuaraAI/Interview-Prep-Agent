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

CRITICAL: For Socrates metric, you MUST verify technical correctness. Penalize incorrect answers heavily.

Return ONLY a JSON object with this exact format:
{
    "detail_level": <score 0-10>,
    "detail_justification": "<2-3 sentence explanation>",
    "clarity": <score 0-10>,
    "clarity_justification": "<2-3 sentence explanation with examples>",
    "socrates_metric": <score 0-10>,
    "socrates_justification": "<2-3 sentence explanation, note any incorrect answers>",
    "overall_project_score": <average of 3 metrics>,
    "strengths": ["<strength 1>", "<strength 2>"],
    "weaknesses": ["<weakness 1>", "<weakness 2>"],
    "improvement_suggestions": ["<suggestion 1>", "<suggestion 2>"]
}"""

    user_prompt = f"""Evaluate {student_name}'s project discussion:

{conversation_text}

Provide scores and justifications for Detail Level, Clarity, and Socrates Metric."""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )

        import json
        evaluation = json.loads(response.choices[0].message.content)
        return evaluation

    except Exception as e:
        print(f"Error evaluating project phase: {e}")
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

Evaluate if the student's answer is:
- CORRECT (10 points): Accurate, demonstrates understanding
- PARTIALLY CORRECT (5-7 points): Has right idea but missing details or minor errors
- INCORRECT (0-3 points): Wrong or demonstrates misunderstanding

Return ONLY a JSON object:
{
    "score": <0-10>,
    "correctness": "<correct/partially_correct/incorrect>",
    "justification": "<why this score, what's right/wrong>",
    "expected_key_points": ["<key point 1>", "<key point 2>"]
}"""

        user_prompt = f"""Question: {qa['question']}

Student Answer: {qa['student_answer']}

Evaluate the correctness of this answer."""

        try:
            response = openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=500,
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
        "next_steps": generate_recommendations(final_score, project_evaluation, factual_evaluation)
    }

    return report


def generate_recommendations(
    final_score: float,
    project_eval: Dict,
    factual_eval: Dict
) -> List[str]:
    """Generate personalized recommendations based on performance."""

    recommendations = []

    # Based on detail level
    if project_eval.get("detail_level", 0) < 7:
        recommendations.append("Practice explaining your projects with more technical detail. Include specific numbers, architectures, and implementation challenges.")

    # Based on clarity
    if project_eval.get("clarity", 0) < 7:
        recommendations.append("Work on technical communication. Define technical terms precisely and use specific parameters (e.g., 'BERT-base with 768 dimensions' instead of 'BERT model').")

    # Based on Socrates metric
    if project_eval.get("socrates_metric", 0) < 7:
        recommendations.append("Deepen your understanding of project fundamentals. Be prepared to answer 'why' questions about your design choices.")

    # Based on factual correctness
    accuracy = factual_eval.get("correct_answers", 0) / max(factual_eval.get("total_questions", 1), 1)
    if accuracy < 0.7:
        recommendations.append("Review ML fundamentals. Focus on the topics where you struggled during factual questions.")

    # Add general recommendations
    if final_score < 7:
        recommendations.append("Consider taking a structured ML course to strengthen theoretical foundations.")
        recommendations.append("Build more projects and document your learning process in detail.")

    return recommendations
