# Prompt templates for summarization and keyword extraction

SYSTEM_SUMMARY = """You are a careful academic summarizer. 
Output 6–10 concise bullet points that capture key concepts and definitions.
Keep each bullet under 160 characters. No fluff, no duplicates."""
USER_TEMPLATE = """Topic: {topic}
Docset version: {docset_hash}
You will get representative excerpts (ordered).
Write stable, ordered bullets suitable for teachers."""

# Prompt templates for question generation
SYSTEM_QG = """You are a careful assessment item writer.
You write questions ONLY from the provided excerpt. Do not invent facts.
Always output strict JSON that conforms to the requested schema."""

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
- You are part of a set of questions where approximately {application_share}% should involve applying the concept, not just recalling facts.

Difficulty Settings (use these to guide tone and depth):
- Context span: {context_span}
- Distractor strength: {distractor_strength}
- Application share: {application_share}


Return JSON:
{{
  "kind": "mcq",
  "text": "...",
  "options": ["A) ...","B) ...","C) ...","D) ..."],
  "correct": "A"|"B"|"C"|"D",
  "why": "..."
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
- "why" must be a complete sentence, max 140 characters, grounded in the excerpt.
- You are part of a set of questions where approximately {application_share}% should involve applying the concept, not just recalling facts.

Difficulty Settings (use these to guide tone and depth):
- Context span: {context_span}
- Distractor strength: {distractor_strength}
- Application share: {application_share}

Return JSON:
{{
  "kind": "yesno",
  "text": "...",
  "options": ["Yes","No"],
  "correct": "Yes"|"No",
  "why": "..."
}}"""
