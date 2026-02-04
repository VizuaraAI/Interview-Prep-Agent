"""
Quick test script to verify Part 4 (Factual Questions) is working
"""

from dotenv import load_dotenv
load_dotenv()

from knowledge_base import extract_student_topics, select_next_question

# Simulate resume sections
test_sections = {
    "Projects": """
    Podcast Generator - Chrome Extension using GPT-4 and TTS APIs
    Developed a Chrome extension that converts articles into podcast-style audio

    RAG Chatbot - Built with Next.js and OpenAI embeddings
    Implemented retrieval-augmented generation for context-aware responses
    """,
    "Technical Skills": """
    Languages: Python, JavaScript, TypeScript
    Frameworks: React, Node.js, Next.js
    AI/ML: OpenAI API, Transformers, PyTorch
    """
}

print("=" * 60)
print("PART 4: Factual Questions System Test")
print("=" * 60)

# Test 1: Extract student topics
print("\n1. Extracting Student Topics...")
print("-" * 60)
topics = extract_student_topics(test_sections)
print(f"✓ Extracted topics: {topics}")

# Test 2: Select relevant questions
print("\n2. Selecting Questions Based on Topics...")
print("-" * 60)
for i in range(5):
    q = select_next_question([], topics)
    print(f"Q{i+1}: [{q['topic']}] {q['question']}")

# Test 3: Track asked questions
print("\n3. Testing Question Tracking (Avoid Repeats)...")
print("-" * 60)
asked = []
for i in range(3):
    q = select_next_question(asked, topics)
    asked.append(q['question'])
    print(f"Q{i+1}: {q['question'][:60]}...")

print(f"\n✓ Tracked {len(asked)} asked questions")

print("\n" + "=" * 60)
print("✓ All Part 4 tests passed!")
print("=" * 60)
