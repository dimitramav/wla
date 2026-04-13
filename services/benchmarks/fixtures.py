"""
Golden question fixture for the benchmark pipelines.

Each question is:
  - Grounded in specific content from the corpus documents
  - Paired with the corpus source it comes from (for traceability)
  - Paired with a ground truth drawn from that document's actual content
  - Paired with retrieval keywords (matching the taxonomy in keywords.yaml)
    that the system would use to find relevant chunks

Questions were drafted with AI assistance and then curated by the researcher:
each question and ground-truth answer was verified against the cited PDF
passage to ensure factual accuracy, source traceability, and coverage of
both practitioner guides and academic papers in the corpus.
"""

GOLDEN_QUESTIONS = [
    {
        # Source: annafreud_seven_ways_support_worried.pdf (Ways 1 & 3)
        "question": "When a student expresses worry, should a teacher immediately reassure them that everything will be fine?",
        "ground_truth": "No. Teachers should first listen, empathise and validate the student's feelings. Early reassurance like 'everything is fine' can feel dismissive. Recognising feelings as normal comes before offering solutions.",
        "keywords": ["anxiety symptoms", "wellbeing"],
    },
    {
        # Source: annafreud_seven_ways_support_worried.pdf (Way 2)
        "question": "Why is it important for teachers to appear calm when supporting an anxious student, even if the teacher feels anxious themselves?",
        "ground_truth": "Children watch the behaviour of adults around them to judge whether they too should feel anxious. A calm teacher signals that the situation is manageable, which helps reassure the student.",
        "keywords": ["anxiety symptoms", "coping"],
    },
    {
        # Source: annafreud_seven_ways_support_worried.pdf (Way 4)
        "question": "How can a teacher help a student challenge an anxious thought about a feared situation?",
        "ground_truth": "By introducing alternative perspectives — reminding the student that a worry is a thought, not necessarily a fact, and exploring how likely the feared outcome really is and what it would mean if it did happen.",
        "keywords": ["coping"],
    },
    {
        # Source: annafreud_seven_ways_support_worried.pdf (Way 7)
        "question": "What is the Anxiety Thermometer and how is it used to monitor a student's progress?",
        "ground_truth": "The Anxiety Thermometer is a 0-to-10 scale based on the child's response: 0 is calm and content, 10 is extremely anxious. It is used to track whether interventions are reducing anxiety over time.",
        "keywords": ["anxiety symptoms", "early intervention"],
    },
    {
        # Source: annafreud_school_attendance_mental_wellbeing.pdf (statistics)
        "question": "What does the research say about trends in persistent school absence in recent years?",
        "ground_truth": "Research from the Children's Commissioner found that persistent absence more than doubled: from 10.9% of all pupils in 2018/19 to 22.3% in 2022/23.",
        "keywords": ["non-attendance", "wellbeing"],
    },
    {
        # Source: annafreud_school_attendance_mental_wellbeing.pdf (early indicators)
        "question": "What early physical and behavioural signs might indicate that a student's non-attendance is rooted in anxiety?",
        "ground_truth": "Physical signs linked to stress such as stomach ache, sickness or headache; a parent reporting the child does not want to come to school; and behavioural changes like reduced engagement with others and learning.",
        "keywords": ["non-attendance", "anxiety symptoms"],
    },
    {
        # Source: annafreud_school_attendance_mental_wellbeing.pdf (case study - graded exposure)
        "question": "Describe a graded exposure approach that can be used to support a student with anxiety-driven school non-attendance.",
        "ground_truth": "A stepladder approach creates a graded hierarchy of exposure to the feared situation. The student starts with smaller steps — such as meeting a friend from school or completing work at home — and gradually transitions to a safe space in school before rejoining peers in class.",
        "keywords": ["early intervention", "non-attendance"],
    },
    {
        # Source: annafreud_school_attendance_mental_wellbeing.pdf (whole-school)
        "question": "What does a whole-school approach to mental health involve and why does it help with non-attendance?",
        "ground_truth": "It involves all aspects of the school community in promoting wellbeing, developing a culture that prioritises safety and support, and reducing the impact of non-attendance risk factors for pupils, staff and families.",
        "keywords": ["school-based intervention", "protective factors"],
    },
    {
        # Source: johnson2023_teacher_mh_literacy_review.pdf
        "question": "According to the research, how does teacher recognition of anxiety compare to their recognition of ADHD in children?",
        "ground_truth": "Teachers appear to have good recognition of childhood ADHD, but their knowledge and recognition of internalising disorders such as anxiety is less clear. Little research has focused on these problems specifically.",
        "keywords": ["mental health literacy", "anxiety symptoms"],
    },
    {
        # Source: schlesier2023_bullying_anxiety_absenteeism.pdf
        "question": "How are school bullying, school anxiety and school absenteeism related to each other?",
        "ground_truth": "Research shows these three constructs are interconnected. Bullying victimisation can trigger school anxiety, and school anxiety in turn predicts absenteeism. Gender and grade level moderate these relationships in secondary school students.",
        "keywords": ["bullying", "non-attendance", "risk factor"],
    },
]
