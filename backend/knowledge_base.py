"""
Knowledge Base Management for ML Interview Questions
Handles storage and retrieval of factual ML questions using RAG
"""

import os
import numpy as np
from typing import List, Dict, Tuple
from openai import OpenAI
from supabase import Client

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ML Questions Bank from andrewekhalel/MLQuestions and huyenchip.com/ml-interviews-book
# Sources:
# 1. https://github.com/andrewekhalel/MLQuestions
# 2. https://huyenchip.com/ml-interviews-book/
ML_QUESTIONS = {
    "Fundamentals & Theory": [
        "What's the trade-off between bias and variance?",
        "What is gradient descent?",
        "Explain over-fitting and under-fitting and how to combat them?",
        "How do you combat the curse of dimensionality?",
        "What is regularization, why do we use it, and give some examples of common methods?",
        "Explain Principal Component Analysis (PCA)?",
        "What is data normalization and why do we need it?",
        "Can you explain the differences between supervised, unsupervised, and reinforcement learning?",
        "Define Learning Rate.",
        "What is the difference between Bayesian vs frequentist statistics?",
        "What is the difference between LDA and PCA for dimensionality reduction?",
        "What is t-SNE?",
        "What is the difference between t-SNE and PCA for dimensionality reduction?",
        "What is UMAP?",
        "What is the difference between t-SNE and UMAP for dimensionality reduction?",
        "What's the difference between a generative and discriminative model?",
        "Instance-Based Versus Model-Based Learning.",
    ],

    "Neural Networks & Deep Learning": [
        "Why is ReLU better and more often used than Sigmoid in Neural Networks?",
        "What is batch normalization and why does it work?",
        "What is vanishing gradient?",
        "What is Momentum (w.r.t NN optimization)?",
        "What is the difference between Batch Gradient Descent and Stochastic Gradient Descent?",
        "List different activation neurons or functions.",
        "What is cost function?",
        "Epoch vs. Batch vs. Iteration.",
        "What are dropouts?",
        "When building a neural network, should you overfit or underfit it first?",
        "Write the vanilla gradient update.",
        "Draw graphs for sigmoid, tanh, ReLU, and leaky ReLU activation functions.",
        "What are pros and cons of each activation function?",
        "Is ReLU differentiable? What to do when it's not?",
        "Derive derivatives for sigmoid function when x is a vector.",
        "What's the motivation for skip connections in neural networks?",
        "How do we detect exploding gradients and prevent them?",
        "Why are RNNs especially susceptible to vanishing/exploding gradients?",
        "How does weight normalization help with training?",
        "Why is validation loss lower than training loss in large language models?",
        "What criteria would you use for early stopping?",
        "Compare gradient descent vs SGD vs mini-batch SGD.",
        "Why use epochs (sampling without replacement) instead of sampling with replacement?",
        "How do weight fluctuations during training affect performance?",
        "What happens with learning rate too high, too low, or acceptable?",
        "What's learning rate warmup and why is it needed?",
        "Compare batch norm and layer norm.",
        "Why prefer squared L2 norm over L2 norm for regularization?",
        "What is weight decay and why is it useful?",
        "What is the motivation for reducing learning rate throughout training?",
        "What are exceptions to reducing learning rate?",
        "What are the effects of decreasing batch size to 1?",
        "What are the effects of using entire training data in one batch?",
        "How to adjust learning rate with batch size changes?",
        "Why is Adagrad favored for sparse gradient problems?",
        "Adam vs. SGD convergence and generalization ability?",
        "What are additional differences between Adam and SGD optimizers?",
    ],

    "Computer Vision": [
        "Why do we use convolutions for images rather than just FC layers?",
        "What makes CNNs translation invariant?",
        "Why do we have max-pooling in classification CNNs?",
        "Describe how convolution works. What about grayscale vs RGB imagery?",
        "Why do segmentation CNNs typically have an encoder-decoder structure?",
        "What is the significance of Residual Networks?",
        "Why would you use many small convolutional kernels such as 3x3 rather than a few large ones?",
        "Given stride S and kernel sizes for each layer of a (1-dimensional) CNN, create a function to compute the receptive field.",
        "Implement connected components on an image/matrix.",
        "How would you remove outliers when trying to estimate a flat plane from noisy samples?",
        "How does CBIR work?",
        "How does image registration work? Sparse vs. dense optical flow.",
        "Talk me through how you would create a 3D model of an object from imagery and depth sensor measurements.",
        "Implement non maximal suppression as efficiently as you can.",
        "What are RCNNs?",
        "How do filter sizes affect accuracy and computational efficiency?",
        "What is ideal filter size selection?",
        "What makes convolutional layers locally connected?",
        "What's the role of zero padding?",
        "What is the need for upsampling and what are the methods?",
        "What is the function of 1x1 convolutional layers?",
        "What are the differences between max-pooling versus average pooling?",
        "When to use max-pooling vs average pooling?",
        "What are the consequences of pooling removal?",
        "What happens when replacing 2x2 max pool with stride-2 conv layer?",
        "How do depthwise separable convolutions reduce parameters?",
        "How to use ImageNet-trained models (256x256) on different-sized images (320x360)?",
        "How to convert fully-connected layers to convolutional layers?",
        "What are the trade-offs between FFT-based versus Winograd-based convolution?",
    ],

    "Natural Language Processing": [
        "What's the motivation for RNN?",
        "Define LSTM.",
        "List the key components of LSTM.",
        "What's the motivation for LSTM?",
        "List the variants of RNN.",
        "What is the basic difference between LSTM and Transformers?",
        "How would you do dropouts in an RNN?",
        "What's density estimation? Why do we say a language model is a density estimator?",
        "Language models are often referred to as unsupervised learning, but some say its mechanism isn't that different from supervised learning. What are your thoughts?",
        "Why do we need word embeddings?",
        "What's the difference between count-based and prediction-based word embeddings?",
        "Most word embedding algorithms assume words appearing in similar contexts have similar meanings. What are problems with context-based embeddings?",
        "Would you use n-gram or neural language model for a 10,000-token dataset?",
        "For n-gram language models, does increasing context length improve performance?",
        "What problems occur using softmax for word-level language models? How do we fix it?",
        "What's the Levenshtein distance of the two words 'doctor' and 'bottle'?",
        "BLEU is popular for machine translation. What are its pros and cons?",
        "Character-level entropy of 2 vs. word-level entropy of 6—which model to deploy?",
        "Would you make a NER training corpus case-sensitive or case-insensitive?",
        "Why does removing stop words sometimes hurt sentiment analysis?",
        "Why do many models use relative position embedding instead of absolute?",
        "Why do some NLP models share weights between embedding and pre-softmax layers?",
    ],

    "Ensemble Methods": [
        "Why do ensembles typically have higher scores than individual models?",
        "What's the difference between boosting and bagging?",
    ],

    "Model Evaluation & Metrics": [
        "Why do we need a validation set and test set? What is the difference between them?",
        "What is stratified cross-validation and when should we use it?",
        "What is Precision?",
        "What is Recall?",
        "Define F1-score.",
        "Explain how a ROC curve works.",
        "What's the difference between Type I and Type II error?",
        "What is an imbalanced dataset? Can you list some ways to deal with it?",
    ],

    "Data Preprocessing & Augmentation": [
        "What is data augmentation? Can you give some examples?",
        "When to use a Label Encoding vs. One Hot Encoding?",
    ],

    "Autoencoders & Generative Models": [
        "What is Autoencoder, name few applications.",
        "What are the components of GAN?",
    ],

    "Math - Vectors & Matrices": [
        "What's the geometric interpretation of the dot product of two vectors?",
        "Given a vector u, find vector v of unit length such that the dot product of u and v is maximum.",
        "Given two vectors a = [3, 2, 1] and b = [-1, 0, 1]. Calculate the outer product a^Tb?",
        "Give an example of how the outer product can be useful in ML.",
        "What does it mean for two vectors to be linearly independent?",
        "Given two sets of vectors A and B. How do you check that they share the same basis?",
        "Given n vectors, each of d dimensions. What is the dimension of their span?",
        "What's a norm? What is L_0, L_1, L_2, L_∞ norm?",
        "How do norm and metric differ? Given a norm, make a metric. Given a metric, can we make a norm?",
        "Why do we say that matrices are linear transformations?",
        "What's the inverse of a matrix? Do all matrices have an inverse? Is the inverse always unique?",
        "What does the determinant of a matrix represent?",
        "What happens to the determinant if we multiply one of its rows by a scalar t?",
        "What's the difference between the covariance matrix A^TA and the Gram matrix AA^T?",
    ],

    "Miscellaneous": [
        "What is Turing test?",
        "How Random Number Generator Works, e.g. rand() function in python works?",
    ]
}


def get_embedding(text: str) -> List[float]:
    """Generate embedding for text using OpenAI"""
    try:
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return []


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    if not vec1 or not vec2:
        return 0.0

    vec1_arr = np.array(vec1)
    vec2_arr = np.array(vec2)

    dot_product = np.dot(vec1_arr, vec2_arr)
    norm1 = np.linalg.norm(vec1_arr)
    norm2 = np.linalg.norm(vec2_arr)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return float(dot_product / (norm1 * norm2))


def extract_student_topics(resume_sections: Dict[str, str]) -> List[str]:
    """Use LLM to analyze student resume and extract ML topics of interest"""

    # Combine relevant resume sections
    resume_text = ""
    for section_name in ["Projects", "Work Experience", "Technical Skills"]:
        if section_name in resume_sections:
            resume_text += f"\n{section_name}:\n{resume_sections[section_name]}\n"

    system_prompt = """You are an ML interview expert. Analyze the student's resume and identify their areas of expertise and interest in machine learning.

Output ONLY a comma-separated list of broad ML topics from the following options:
- Fundamentals & Theory
- Neural Networks & Deep Learning
- Computer Vision
- Natural Language Processing
- Ensemble Methods
- Model Evaluation & Metrics
- Data Preprocessing & Augmentation
- Autoencoders & Generative Models
- Math - Vectors & Matrices
- Miscellaneous

IMPORTANT: Select AT LEAST 3-4 topics to ensure interview diversity. Include both specific areas of expertise and foundational topics."""

    user_prompt = f"""Analyze this resume and list 3-4 ML topics this student should be interviewed on:

{resume_text}

Output format: Topic1, Topic2, Topic3, Topic4 (comma-separated, no explanations)
Include their specific areas AND foundational topics for variety."""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-5.2",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_completion_tokens=200
        )

        topics_str = response.choices[0].message.content.strip()
        topics = [t.strip() for t in topics_str.split(',')]

        # Validate topics against our question bank
        valid_topics = [t for t in topics if t in ML_QUESTIONS]

        # Ensure we have at least 3-4 topics for diversity
        default_topics = [
            "Fundamentals & Theory",
            "Neural Networks & Deep Learning",
            "Model Evaluation & Metrics",
            "Computer Vision"
        ]

        # Add default topics if we don't have enough
        for default_topic in default_topics:
            if len(valid_topics) >= 4:
                break
            if default_topic not in valid_topics and default_topic in ML_QUESTIONS:
                valid_topics.append(default_topic)

        print(f"📊 Extracted {len(valid_topics)} topics for interview: {valid_topics}")

        return valid_topics

    except Exception as e:
        print(f"Error extracting topics: {e}")
        return ["Fundamentals & Theory"]


def get_questions_for_topics(topics: List[str], num_questions: int = 10) -> List[Dict[str, str]]:
    """Get relevant questions based on student's topics"""

    questions = []
    questions_per_topic = max(1, num_questions // len(topics))

    for topic in topics:
        if topic in ML_QUESTIONS:
            topic_questions = ML_QUESTIONS[topic][:questions_per_topic]
            for q in topic_questions:
                questions.append({
                    "topic": topic,
                    "question": q
                })

    return questions[:num_questions]


def select_next_question(
    asked_questions: List[str],
    student_topics: List[str],
    resume_text: str = "",
    difficulty: str = "medium",
    topics_covered: Dict[str, int] = None
) -> Dict[str, any]:
    """
    Select next question with topic diversity to ensure variety across 3-4 topics.
    Limits questions from same topic to 1-2 before switching.
    """

    if topics_covered is None:
        topics_covered = {}

    # Get all available questions for student's topics
    available_questions = []
    for topic in student_topics:
        if topic in ML_QUESTIONS:
            for q in ML_QUESTIONS[topic]:
                if q not in asked_questions:
                    available_questions.append({
                        "topic": topic,
                        "question": q
                    })

    # If all questions exhausted, wrap around or pick from any topic
    if not available_questions:
        for topic, questions in ML_QUESTIONS.items():
            for q in questions:
                if q not in asked_questions:
                    available_questions.append({
                        "topic": topic,
                        "question": q
                    })

    # If we have resume text, calculate similarity scores
    if available_questions and resume_text:
        # Generate embedding for resume
        resume_embedding = get_embedding(resume_text)

        # Calculate similarity scores for each question
        scored_questions = []
        for q_data in available_questions:
            # Combine topic and question for better context matching
            question_text = f"{q_data['topic']}: {q_data['question']}"
            question_embedding = get_embedding(question_text)

            similarity = cosine_similarity(resume_embedding, question_embedding)

            scored_questions.append({
                "topic": q_data["topic"],
                "question": q_data["question"],
                "similarity_score": round(similarity, 3),
                "match_reason": f"Matched based on {q_data['topic']} expertise in resume"
            })

        # Sort by similarity score (highest first)
        scored_questions.sort(key=lambda x: x["similarity_score"], reverse=True)

        # TOPIC DIVERSITY LOGIC - Ensure we ask from 3-4 different topics
        # Priority: Topics with 0 questions > Topics with 1 question > Topics with 2+ questions

        # Calculate current topic coverage
        topics_not_asked = [topic for topic in student_topics if topics_covered.get(topic, 0) == 0]
        topics_asked_once = [topic for topic in student_topics if topics_covered.get(topic, 0) == 1]

        print(f"📊 Topics not asked yet: {topics_not_asked}")
        print(f"📊 Topics asked once: {topics_asked_once}")
        print(f"📊 Topics covered: {topics_covered}")

        # PRIORITY 1: Pick from topics not asked yet (to ensure diversity across 3-4 topics)
        if topics_not_asked:
            candidate_questions = [q for q in scored_questions if q["topic"] in topics_not_asked]
            if candidate_questions:
                best_match = candidate_questions[0]
                print(f"✅ Selected from new topic: {best_match['topic']}")
            else:
                best_match = scored_questions[0]

        # PRIORITY 2: Pick from topics asked only once (to balance coverage)
        elif topics_asked_once:
            candidate_questions = [q for q in scored_questions if q["topic"] in topics_asked_once]
            if candidate_questions:
                best_match = candidate_questions[0]
                print(f"✅ Selected from topic asked once: {best_match['topic']}")
            else:
                best_match = scored_questions[0]

        # PRIORITY 3: All topics covered at least twice, pick highest similarity
        else:
            best_match = scored_questions[0]
            print(f"✅ All topics covered, picking highest similarity: {best_match['topic']}")

        all_scores = [q["similarity_score"] for q in scored_questions]

        return {
            "topic": best_match["topic"],
            "question": best_match["question"],
            "similarity_score": best_match["similarity_score"],
            "max_similarity": max(all_scores),
            "match_reason": best_match["match_reason"],
            "matched_topics": student_topics
        }

    # Return first available question (no similarity scoring)
    if available_questions:
        return {
            "topic": available_questions[0]["topic"],
            "question": available_questions[0]["question"],
            "similarity_score": None,
            "max_similarity": None,
            "match_reason": f"Selected from {available_questions[0]['topic']} topic",
            "matched_topics": student_topics
        }

    # Fallback
    return {
        "topic": "Fundamentals & Theory",
        "question": "Explain the bias-variance tradeoff in machine learning?",
        "similarity_score": None,
        "max_similarity": None,
        "match_reason": "Default fallback question",
        "matched_topics": []
    }
