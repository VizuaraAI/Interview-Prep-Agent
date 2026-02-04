"""
Script to evaluate Aditya's interview
"""

import os
from dotenv import load_dotenv
from supabase import create_client
import requests
import json

load_dotenv()

# Initialize Supabase
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

# Find Aditya's conversation
print("🔍 Searching for Aditya's conversation...")
conversations = supabase.table("conversations").select("*").order("created_at", desc=True).limit(10).execute()

if not conversations.data:
    print("❌ No conversations found for Aditya")
    exit(1)

print(f"\n📋 Found {len(conversations.data)} recent conversation(s):")

# Filter for Aditya
aditya_convs = []
for i, conv in enumerate(conversations.data):
    # Get student info
    student_result = supabase.table("students").select("name").eq("id", conv['student_id']).single().execute()
    student_name = student_result.data['name'] if student_result.data else "Unknown"

    print(f"\n{i+1}. ID: {conv['id']}")
    print(f"   Student: {student_name}")
    print(f"   Phase: {conv['phase']}")
    print(f"   Project Q Count: {conv.get('project_questions_count', 0)}")
    print(f"   Factual Q Count: {conv.get('factual_questions_count', 0)}")

    if "aditya" in student_name.lower():
        aditya_convs.append((conv, student_name))

if not aditya_convs:
    print("\n❌ No conversations found for Aditya")
    exit(1)

# Use the most recent Aditya conversation
latest_conv, student_name = aditya_convs[0]
conversation_id = latest_conv['id']

print(f"\n✅ Using most recent Aditya conversation: {conversation_id}")
print(f"   Student: {student_name}")

# Fetch messages to verify we have enough data
messages = supabase.table("messages").select("*").eq("conversation_id", conversation_id).order("created_at").execute()
print(f"\n📨 Total messages in conversation: {len(messages.data)}")

# Call evaluation endpoint
print(f"\n🎯 Generating evaluation report...")
try:
    response = requests.post(
        "http://localhost:8000/evaluate",
        params={"conversation_id": conversation_id}
    )

    if response.status_code == 200:
        result = response.json()
        evaluation = result["evaluation"]

        print("\n" + "="*80)
        print(f"📊 EVALUATION REPORT FOR {evaluation['student_name'].upper()}")
        print("="*80)

        print(f"\n🎯 FINAL SCORE: {evaluation['final_score']}/10")
        print(f"📈 PERFORMANCE LEVEL: {evaluation['performance_level']}")

        print("\n" + "-"*80)
        print("📁 PROJECT PHASE (Phase III)")
        print("-"*80)
        project = evaluation['project_phase']
        print(f"Overall Score: {project['overall_score']}/10")
        print(f"  • Detail Level: {project['detail_level']}/10")
        print(f"  • Clarity: {project['clarity']}/10")
        print(f"  • Socrates Metric: {project['socrates_metric']}/10")

        print(f"\n💪 Strengths:")
        for strength in project['strengths']:
            print(f"  • {strength}")

        print(f"\n⚠️  Weaknesses:")
        for weakness in project['weaknesses']:
            print(f"  • {weakness}")

        print(f"\n📝 Justifications:")
        print(f"  Detail: {project['justifications']['detail']}")
        print(f"  Clarity: {project['justifications']['clarity']}")
        print(f"  Socrates: {project['justifications']['socrates']}")

        print("\n" + "-"*80)
        print("🧠 FACTUAL PHASE (Phase IV)")
        print("-"*80)
        factual = evaluation['factual_phase']
        print(f"Overall Score: {factual['overall_score']}/10")
        print(f"Total Questions: {factual['total_questions']}")
        print(f"  ✅ Correct: {factual['correct_answers']}")
        print(f"  ⚠️  Partially Correct: {factual['partially_correct']}")
        print(f"  ❌ Incorrect: {factual['incorrect_answers']}")
        print(f"  📊 Accuracy Rate: {factual['accuracy_rate']}%")

        print("\n" + "-"*80)
        print("💡 IMPROVEMENT SUGGESTIONS")
        print("-"*80)
        for suggestion in evaluation['improvement_suggestions']:
            print(f"  • {suggestion}")

        print("\n" + "-"*80)
        print("🚀 NEXT STEPS")
        print("-"*80)
        for step in evaluation['next_steps']:
            print(f"  • {step}")

        print("\n" + "="*80)

        # Save to file
        with open(f"/tmp/aditya_evaluation_{conversation_id[:8]}.json", "w") as f:
            json.dump(evaluation, f, indent=2)
        print(f"\n💾 Full evaluation saved to: /tmp/aditya_evaluation_{conversation_id[:8]}.json")

    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"❌ Error calling evaluation endpoint: {e}")
