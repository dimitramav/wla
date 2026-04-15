# Prompt templates for summarization and keyword extraction

SYSTEM_SUMMARY = """You are a careful academic summarizer. 
Output 6–10 concise bullet points that capture key concepts and definitions.
Keep each bullet under 160 characters. No fluff, no duplicates."""
USER_TEMPLATE = """Topic: {topic}
Docset version: {docset_hash}
You will get representative excerpts (ordered).
Write stable, ordered bullets suitable for teachers."""

# Prompt templates for question generation
SYSTEM_QG = """You are an expert assessment item writer for a teacher-training programme on student mental health (school anxiety, emotional well-being, early intervention).

Your audience is primary and secondary school teachers. Every question must test understanding of concepts, risk factors, protective factors, interventions, or practical classroom strategies — NOT document structure, table labels, page references, or methodology details.

Rules:
- Write questions ONLY from the provided excerpt. Do not invent facts.
- Never ask about where information is located, how a table is organized, or which section something appears in.
- Always output strict JSON that conforms to the requested schema."""

DIFFICULTY_INSTRUCTIONS = {
    "beginner": (
        "BEGINNER — Recall & Recognition:\n"
        "- Ask about a single concept, definition, risk factor, or strategy stated in the excerpt.\n"
        "- The correct answer should be clearly supported by the text.\n"
        "- Use question stems like: \"Which factor is identified as...\", \"What does the excerpt describe as...\", \"According to the research...\"\n"
        "- Distractors should be plausible terms from the same mental-health domain that are NOT supported by the excerpt.\n"
        "- Do NOT ask about document structure, table layout, section headings, or where information is located.\n"
        "- Do NOT require inference, comparison, or evaluation."
    ),
    "intermediate": (
        "INTERMEDIATE — Comprehension & Application:\n"
        "- Ask the reader to understand relationships, causes, or implications of concepts described in the excerpt.\n"
        "- The correct answer requires paraphrasing or connecting two ideas from the text — not a verbatim quote.\n"
        "- Use question stems like: \"Based on the research, why might...\", \"Which best explains the relationship between...\", \"How does X relate to Y...\"\n"
        "- Distractors should be plausible misinterpretations that someone who skimmed the text might choose.\n"
        "- Do NOT ask about document structure, table layout, section headings, or where information is located.\n"
        "- Do NOT ask for simple recall of a single fact."
    ),
    "advanced": (
        "ADVANCED — Analysis & Inference:\n"
        "- Ask the reader to synthesize, evaluate, or draw conclusions about mental-health concepts that go beyond what is explicitly stated.\n"
        "- The correct answer requires combining multiple ideas from the excerpt or reasoning about implications for classroom practice.\n"
        "- Use question stems like: \"What can be inferred about...\", \"Which limitation is implied by...\", \"How might this finding affect a teacher's approach to...\"\n"
        "- Distractors must be strong — they should represent common misconceptions or partially correct reasoning about student well-being.\n"
        "- Do NOT ask about document structure, table layout, section headings, or where information is located.\n"
        "- Do NOT ask questions whose answer can be found verbatim in the excerpt."
    ),
}

# One MCQ from a single excerpt.
# Required JSON fields:
# kind: "mcq"
# text: string (clear question)
# options: array of 4 short strings ["A) ...","B) ...","C) ...","D) ..."]
# correct: one of "A","B","C","D"
# why: single short sentence grounded in the excerpt
USER_QG_MC_TEMPLATE = """Write exactly ONE multiple-choice question from this excerpt.

EXCERPT:
\"\"\"{excerpt}\"\"\"

Rules:
- The question and all answer options must be grammatically correct, well-formed English.
- Base the question ONLY on the excerpt.
- Options must be short and plausible; exactly 4 options labeled A) B) C) D).
- Exactly ONE correct answer; respond with letter only in "correct".
- "why" must be a complete sentence, max 140 characters, grounded in the excerpt.
- "evidence" must be a single contiguous sentence copied VERBATIM from the excerpt (no paraphrasing, no added words, no ellipses), 20–240 characters, that a reader can point to as the justification for the correct answer.
Difficulty level: {difficulty_label}

{difficulty_instructions}

Return JSON:
{{
  "kind": "mcq",
  "text": "...",
  "options": ["A) ...","B) ...","C) ...","D) ..."],
  "correct": "A"|"B"|"C"|"D",
  "why": "...",
  "evidence": "..."
}}"""

# One Yes/No from a single excerpt.
# Required JSON fields:
# kind: "yesno"
# text: string as a True/False style statement
# options: ["Yes","No"]
# correct: "Yes" or "No"
# why: single short sentence grounded in the excerpt
USER_QG_YN_TEMPLATE = """Write exactly ONE Yes/No (True/False) question from this excerpt.

EXCERPT:
\"\"\"{excerpt}\"\"\"

Rules:
- The question and all answer options must be grammatically correct, well-formed English.
- Statement must be verifiably True or False from the excerpt only.
- options must be exactly ["Yes","No"].
- "why" must be a complete sentence, max 100 characters, grounded in the excerpt.
- "evidence" must be a single contiguous sentence copied VERBATIM from the excerpt (no paraphrasing, no added words, no ellipses), 20–240 characters, that a reader can point to as the justification for the correct answer.
Difficulty level: {difficulty_label}

{difficulty_instructions}

Return JSON:
{{
  "kind": "yesno",
  "text": "...",
  "options": ["Yes","No"],
  "correct": "Yes"|"No",
  "why": "...",
  "evidence": "..."
}}"""
