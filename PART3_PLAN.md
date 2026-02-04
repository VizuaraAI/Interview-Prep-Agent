# Part 3: Project-based Questions (FDR Framework)

Part 3 adds deep technical questioning about the candidate's projects using the FDR (Fundamentals, Practicals, Research) framework.

## What's New in Part 3

- **Project selection** - AI picks one interesting project from the candidate's resume
- **Deep technical questioning** - Uses FDR framework to probe understanding:
  - **Fundamentals**: Basic concepts, theory, and foundational knowledge
  - **Practicals**: Implementation details, challenges faced, decisions made
  - **Research**: Advanced topics, trade-offs, alternatives considered
- **Dynamic follow-ups** - AI generates contextual follow-up questions based on responses
- **Phase tracking** - Conversation phase updates from 'greeting' to 'project_questions'
- **Quality assessment** - Internal evaluation of response depth and quality

## Architecture Changes

### Backend Changes

1. **Update conversation.py**
   - Add `ask_project_question()` function for initial project question
   - Add `continue_project_questions()` function for FDR-based follow-ups
   - Add FDR framework logic to guide questioning strategy
   - Add response evaluation (optional, for future scoring)

2. **Update main.py**
   - Add transition logic from greeting to project phase
   - Detect when candidate is "ready" and trigger phase change
   - Update `/continue-conversation` to handle different phases

3. **Database schema (optional)**
   - Could add `project_questions` table to track questions asked
   - Could add `evaluations` table to store response quality scores

### Frontend Changes

1. **Update interview page**
   - Show current phase indicator (Greeting → Projects → Factual)
   - Visual distinction for different interview phases
   - Progress indicator

## FDR Framework Implementation

### Phase 1: Select Project
- AI analyzes candidate's projects from resume
- Picks the most interesting/complex project
- Asks opening question about the project

### Phase 2: Fundamentals
- Questions about basic concepts and theory
- "What is [concept] and why did you use it?"
- "Can you explain the theory behind [approach]?"
- Validates foundational understanding

### Phase 3: Practicals
- Questions about implementation and challenges
- "How did you implement [feature]?"
- "What challenges did you face with [component]?"
- "Why did you choose [technology] over alternatives?"
- Probes hands-on experience

### Phase 4: Research
- Questions about advanced topics and trade-offs
- "What are the limitations of your approach?"
- "How would you scale this to handle [scenario]?"
- "What alternative approaches did you consider?"
- Tests depth of understanding and critical thinking

## Conversation Flow

```
1. Greeting Phase (Part 2) ✓
   "Hi! How are you?" → "Ready to start?"

2. Transition to Projects
   User: "Yes, I'm ready!"
   Raj: "Great! I'd like to dive into one of your projects..."

3. Project Questions Phase (Part 3)
   - Opening question about project
   - 3-4 follow-up questions using FDR framework
   - Each question builds on previous answer

4. Transition to Factual (Part 4)
   After sufficient project discussion
   Raj: "Excellent! Now let's test some fundamental ML concepts..."
```

## Example Project Interview Flow

**Opening:**
"I see you worked on an RLHF system at IIT Madras. Can you walk me through what this system does and what your role was?"

**Fundamentals:**
- "What is RLHF and how does it differ from traditional supervised learning?"
- "Can you explain the reward model component?"

**Practicals:**
- "How did you collect the human feedback data?"
- "What challenges did you face when training the reward model?"
- "Walk me through your implementation of the PPO algorithm."

**Research:**
- "What are the limitations of RLHF compared to other alignment methods?"
- "How would you handle edge cases where human feedback is inconsistent?"
- "What alternative approaches did you consider for improving model alignment?"

## Implementation Plan

### Step 1: Update conversation logic
- Add phase detection (when to move from greeting to projects)
- Add project selection logic
- Add FDR question generation

### Step 2: Update API endpoints
- Modify `/continue-conversation` to handle phase transitions
- Add phase tracking in database

### Step 3: Update frontend
- Add phase indicator UI
- Show progress through interview

### Step 4: Testing
- Test greeting → project transition
- Test FDR question flow
- Verify questions are contextual and build on previous answers

## Success Criteria

Part 3 is successful when:
✅ System automatically transitions from greeting to projects when candidate is ready
✅ AI picks an interesting project from candidate's resume
✅ AI asks 3-4 deep technical questions following FDR framework
✅ Questions are contextual and build on previous answers
✅ Conversation feels natural and technically rigorous
✅ Phase indicator shows current interview stage
✅ Ready to transition to Part 4 (Factual Questions)

---

## Next Steps

1. Do you want to implement all of FDR (Fundamentals, Practicals, Research) or start with a simpler version?
2. Should we add visible phase indicators in the UI or keep it seamless?
3. How many project questions should we ask before moving to Part 4? (I suggest 4-5)
4. Should we track/score response quality or just have a conversation?
