"""
Shared benchmark fixtures: golden questions and generator models.

Both the RAG retrieval benchmark and the LLM generation benchmark import
from this module so that the question set and the model list stay in sync
across the two pipelines.
"""

# ---------------------------------------------------------------------------
# Golden question set
#
# Each question is:
#   - Grounded in specific content from the corpus documents
#   - Paired with the corpus source it comes from (for traceability)
#   - Paired with a ground truth drawn from that document's actual content
#   - Paired with retrieval keywords (matching the taxonomy in keywords.yaml)
#     that the system would use to find relevant chunks
#
# Questions were drafted with AI assistance and then curated by the researcher:
# each question and ground-truth answer was verified against the cited PDF
# passage to ensure factual accuracy, source traceability, and coverage of
# both practitioner guides and academic papers in the corpus.
# ---------------------------------------------------------------------------
GOLDEN_QUESTIONS = [
    {
        # Source: annafreud_seven_ways_support_worried.pdf (Ways 1 & 3)
        "question": "When a student expresses worry, should a teacher immediately reassure them that everything will be fine?",
        "ground_truth": "No. Teachers should first listen, empathise and validate the student's feelings. Early reassurance like 'everything is fine' can feel dismissive. Recognising feelings as normal comes before offering solutions.",
        "keywords": ["common signs and symptoms", "somatic complaints"],
    },
    {
        # Source: annafreud_seven_ways_support_worried.pdf (Way 2)
        "question": "Why is it important for teachers to appear calm when supporting an anxious student, even if the teacher feels anxious themselves?",
        "ground_truth": "Children watch the behaviour of adults around them to judge whether they too should feel anxious. A calm teacher signals that the situation is manageable, which helps reassure the student.",
        "keywords": ["common signs and symptoms", "social evaluation fears"],
    },
    {
        # Source: annafreud_seven_ways_support_worried.pdf (Way 4)
        "question": "How can a teacher help a student challenge an anxious thought about a feared situation?",
        "ground_truth": "By introducing alternative perspectives — reminding the student that a worry is a thought, not necessarily a fact, and exploring how likely the feared outcome really is and what it would mean if it did happen.",
        "keywords": ["cognitive restructuring"],
    },
    {
        # Source: annafreud_seven_ways_support_worried.pdf (Way 7)
        "question": "What is the Anxiety Thermometer and how is it used to monitor a student's progress?",
        "ground_truth": "The Anxiety Thermometer is a 0-to-10 scale based on the child's response: 0 is calm and content, 10 is extremely anxious. It is used to track whether interventions are reducing anxiety over time.",
        "keywords": ["response systems", "autonomic arousal"],
    },
    {
        # Source: annafreud_school_attendance_mental_wellbeing.pdf (statistics)
        "question": "What does the research say about trends in persistent school absence in recent years?",
        "ground_truth": "Research from the Children's Commissioner found that persistent absence more than doubled: from 10.9% of all pupils in 2018/19 to 22.3% in 2022/23.",
        "keywords": ["attendance tracking", "somatic complaints"],
    },
    {
        # Source: annafreud_school_attendance_mental_wellbeing.pdf (early indicators)
        "question": "What early physical and behavioural signs might indicate that a student's non-attendance is rooted in anxiety?",
        "ground_truth": "Physical signs linked to stress such as stomach ache, sickness or headache; a parent reporting the child does not want to come to school; and behavioural changes like reduced engagement with others and learning.",
        "keywords": ["somatic complaints", "attendance tracking", "common signs and symptoms"],
    },
    {
        # Source: annafreud_school_attendance_mental_wellbeing.pdf (case study - graded exposure)
        "question": "Describe a graded exposure approach that can be used to support a student with anxiety-driven school non-attendance.",
        "ground_truth": "A stepladder approach creates a graded hierarchy of exposure to the feared situation. The student starts with smaller steps — such as meeting a friend from school or completing work at home — and gradually transitions to a safe space in school before rejoining peers in class.",
        "keywords": ["graduated exposure", "attendance tracking"],
    },
    {
        # Source: annafreud_school_attendance_mental_wellbeing.pdf (whole-school)
        "question": "What does a whole-school approach to mental health involve and why does it help with non-attendance?",
        "ground_truth": "It involves all aspects of the school community in promoting wellbeing, developing a culture that prioritises safety and support, and reducing the impact of non-attendance risk factors for pupils, staff and families.",
        "keywords": ["school social climate", "student–teacher relations", "parent-teacher collaboration"],
    },
    {
        # Source: johnson2023_teacher_mh_literacy_review.pdf
        "question": "According to the research, how does teacher recognition of anxiety compare to their recognition of ADHD in children?",
        "ground_truth": "Teachers appear to have good recognition of childhood ADHD, but their knowledge and recognition of internalising disorders such as anxiety is less clear. Little research has focused on these problems specifically.",
        "keywords": ["common signs and symptoms", "internalizing symptoms"],
    },
    {
        # Source: schlesier2023_bullying_anxiety_absenteeism.pdf
        "question": "How are school bullying, school anxiety and school absenteeism related to each other?",
        "ground_truth": "Research shows these three constructs are interconnected. Bullying victimisation can trigger school anxiety, and school anxiety in turn predicts absenteeism. Gender and grade level moderate these relationships in secondary school students.",
        "keywords": ["peer aggression", "social evaluation fears", "attendance tracking"],
    },
]


# ---------------------------------------------------------------------------
# Generator models — all local Ollama, Q4_0 quantized
#
# Pulled/removed sequentially during a benchmark run to keep disk usage
# bounded.
# ---------------------------------------------------------------------------
GENERATOR_MODELS = [
    {
        "name": "mistral-7b",
        "tag": "mistral:7b-instruct-q4_0",
        "pull_needed": True,
    },
    {
        "name": "llama3.1-8b",
        "tag": "llama3.1:8b-instruct-q4_0",
        "pull_needed": True,
    },
    {
        "name": "gemma2-9b",
        "tag": "gemma2:9b-instruct-q4_0",
        "pull_needed": True,
    },
    {
        "name": "phi3.5-3.8b",
        "tag": "phi3.5:3.8b-mini-instruct-q4_0",
        "pull_needed": True,
    },
]


# ---------------------------------------------------------------------------
# LLM benchmark CSV schema
#
# Shared by llm_benchmark.py (online scoring) and llm_ragas_score.py
# (offline rescoring) so the two stay in sync.
#
# `answer_relevancy` is retained for backward-compat with pre-Finding-5
# runs; it is no longer computed or used in the composite score.
# ---------------------------------------------------------------------------
LLM_CSV_FIELDS = [
    "timestamp",
    "generator_model",
    "emb_model",
    "chunk_size",
    "chunk_overlap",
    "retrieval_type",
    "question",
    "ground_truth",
    "format_compliance",
    "response_time_s",
    "raw_output",
    "generated_answer",
    "faithfulness",
    "answer_relevancy",
    "stem_clarity",
    "distractor_plausibility",
    "pedagogical_appropriateness",
    "mcq_quality",
    "context_relevancy",
    "composite_score",
]
