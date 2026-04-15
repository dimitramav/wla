"""
Golden question fixture for the benchmark pipelines.

Each question is:
  - Grounded in specific content from the corpus documents
  - Paired with the corpus source it comes from (for traceability)
  - Paired with a ground truth drawn from that document's actual content
  - Tagged with exactly ONE retrieval keyword (matching the taxonomy in
    keywords.yaml) so the benchmark tests retrieval the same way the
    production system queries: one keyword per retrieval call
  - The question's cognitive demand matches its keyword's difficulty level:
    Level 1 (beginner) = recognition & recall
    Level 2 (intermediate) = understanding & application
    Level 3 (advanced) = analysis & synthesis

Questions were drafted with AI assistance and then curated by the researcher:
each question and ground-truth answer was verified against the cited PDF
passage to ensure factual accuracy, source traceability, and coverage of
both practitioner guides and academic papers in the corpus.
"""

GOLDEN_QUESTIONS = [
    # -----------------------------------------------------------------------
    # Level 1 — Beginner (recognition & recall)
    # -----------------------------------------------------------------------
    {
        # Source: annafreud_school_attendance_mental_wellbeing.pdf (statistics)
        "question": "What does the research say about trends in persistent school absence in recent years?",
        "ground_truth": "Research from the Children's Commissioner found that persistent absence more than doubled: from 10.9% of all pupils in 2018/19 to 22.3% in 2022/23.",
        "keywords": ["non-attendance"],
    },
    {
        # Source: schlesier2023_bullying_anxiety_absenteeism.pdf (introduction)
        "question": "What forms of bullying are identified in the research on school-age children?",
        "ground_truth": "Research identifies both traditional bullying (physical, verbal, relational aggression in school settings) and cyberbullying (aggression via digital means). Some studies suggest that teenage girls are as likely to bully or be bullied as boys.",
        "keywords": ["bullying"],
    },
    {
        # Source: annafreud_school_attendance_mental_wellbeing.pdf (early indicators)
        "question": "What early physical and behavioural signs might indicate that a student's non-attendance is rooted in anxiety?",
        "ground_truth": "Physical signs linked to stress such as stomach ache, sickness or headache; a parent reporting the child does not want to come to school; and behavioural changes like reduced engagement with others and learning.",
        "keywords": ["anxiety symptoms"],
    },
    {
        # Source: farmakopoulou2024_greek_anxiety_family_selfesteem.pdf (literature review)
        "question": "According to the research, what protective effects does high self-esteem have on adolescents?",
        "ground_truth": "Teens with high self-esteem have more social support, more extensive social networks, and friendly interactions. Self-esteem also protects teens from delinquency, aggression, and academic underachievement.",
        "keywords": ["self-esteem"],
    },
    {
        # Source: shamionov2021_wellbeing_anxiety_variations.pdf (introduction)
        "question": "What are the potential consequences of poor academic wellbeing for junior adolescents?",
        "ground_truth": "School anxiety and poor academic wellbeing in junior adolescents can lead to deterioration of health, behavioural problems, and a dramatic decrease in academic performance.",
        "keywords": ["wellbeing"],
    },
    # -----------------------------------------------------------------------
    # Level 2 — Intermediate (understanding & application)
    # -----------------------------------------------------------------------
    {
        # Source: johnson2023_teacher_mh_literacy_review.pdf (discussion)
        "question": "How does teacher knowledge of ADHD compare to their knowledge of internalising disorders like anxiety, and what does this imply for teacher training?",
        "ground_truth": "Teachers generally score highest on knowledge of ADHD symptoms and diagnosis, likely because ADHD has clear impacts on learning and classroom management. However, their knowledge and recognition of internalising disorders such as anxiety is less clear and less well researched. This implies that teacher training needs to focus on a wider range of childhood mental health problems beyond ADHD.",
        "keywords": ["mental health literacy"],
    },
    {
        # Source: johnson2023_teacher_mh_literacy_review.pdf (findings on help-seeking)
        "question": "How does adult recognition of child mental health problems influence their help-seeking behaviour?",
        "ground_truth": "Preliminary research suggests that adults who have sufficient knowledge of child mental health problems for problem recognition are more likely to endorse appropriate professionals as sources of help and to seek information about mental health services. Adults who lack this knowledge are more likely to endorse inappropriate sources of help.",
        "keywords": ["help-seeking"],
    },
    {
        # Source: annafreud_seven_ways_support_worried.pdf (Way 4)
        "question": "How can a teacher help a student challenge an anxious thought about a feared situation?",
        "ground_truth": "By introducing alternative perspectives — reminding the student that a worry is a thought, not necessarily a fact, and exploring how likely the feared outcome really is and what it would mean if it did happen.",
        "keywords": ["coping"],
    },
    {
        # Source: annafreud_school_attendance_mental_wellbeing.pdf (whole-school approach)
        "question": "What does a whole-school approach to mental health involve and why does it help with non-attendance?",
        "ground_truth": "It involves all aspects of the school community in promoting wellbeing, developing a culture that prioritises safety and support, and reducing the impact of non-attendance risk factors for pupils, staff and families.",
        "keywords": ["protective factors"],
    },
    {
        # Source: annafreud_school_attendance_mental_wellbeing.pdf (case study - graded exposure)
        "question": "How does a graded exposure approach address the avoidance cycle in anxiety-driven school non-attendance?",
        "ground_truth": "A stepladder approach breaks the avoidance cycle by creating a graded hierarchy of exposure to the feared situation. The student starts with smaller steps — such as meeting a friend from school or completing work at home — and gradually transitions to a safe space in school before rejoining peers in class, rebuilding tolerance at each stage rather than reinforcing avoidance.",
        "keywords": ["early intervention"],
    },
    # -----------------------------------------------------------------------
    # Level 3 — Advanced (analysis & synthesis)
    # -----------------------------------------------------------------------
    {
        # Source: huttunen2025_socioemotional_profiles_anxiety.pdf (discussion)
        "question": "Why might adolescents with high empathy but low stress resistance experience elevated school anxiety despite having strong social-emotional skills overall?",
        "ground_truth": "The combination of high empathy and lower stress resistance (an emotional regulation skill) is particularly linked to school anxiety. Highly empathic adolescents may feel more intensely pressured to meet their own or others' standards and may be more sensitive to distress in their peer group, while lacking the emotional regulation capacity to manage these feelings effectively.",
        "keywords": ["emotional regulation"],
    },
    {
        # Source: huttunen2025_socioemotional_profiles_anxiety.pdf (conclusions + discussion)
        "question": "How can different combinations of social-emotional skills serve as resilience factors for adolescents, and what does this imply for school support practices?",
        "ground_truth": "Social-emotional skills may serve as resilience factors by helping adolescents adjust to educational transitions. Adolescents with different social-emotional skills profiles can experience positive school outcomes through distinct strengths — for example, empathy and cooperation versus emotional regulation and energy. This implies that school practices should be strength-based and targeted to different subgroups rather than one-size-fits-all.",
        "keywords": ["resilience"],
    },
    {
        # Source: troy2022_school_structural_mh_promotion_review.pdf (review findings)
        "question": "What challenges have researchers identified with implementing whole-school mental health promotion interventions, and what does this suggest about the evidence base?",
        "ground_truth": "Research suggests that whole-school approaches to mental health may have been ineffective partly due to challenges in implementing complex interventions. The evidence base for school-based interventions targeting structural and organisational changes remains limited, with most studies focusing on individual-level interventions rather than systemic changes to the school environment.",
        "keywords": ["school-based intervention"],
    },
    {
        # Source: schlesier2023_bullying_anxiety_absenteeism.pdf (structural model)
        "question": "How are bullying victimisation, school anxiety, and absenteeism structurally related, and what does this imply about identifying at-risk students?",
        "ground_truth": "Research shows these three constructs are interconnected: bullying victimisation can trigger school anxiety, and school anxiety in turn predicts absenteeism. Gender and grade level moderate these relationships. This implies that bullying is not just a behavioural issue but a risk factor for a cascade of negative outcomes, and that early identification of bullying victims could prevent downstream anxiety and absence.",
        "keywords": ["risk factor"],
    },
    {
        # Source: farmakopoulou2024_greek_anxiety_family_selfesteem.pdf (results + discussion)
        "question": "How does family cohesion relate to adolescent anxiety, and what distinguishes cohesion from adaptability in this relationship?",
        "ground_truth": "Family cohesion was negatively correlated with both state anxiety (rho=-0.25) and trait anxiety (rho=-0.46) in adolescents, meaning higher family cohesion is associated with lower anxiety. However, family adaptability did not show a significant correlation with anxiety, suggesting that the emotional bonds between family members matter more for adolescent anxiety than the family's ability to change its structure or rules.",
        "keywords": ["family cohesion"],
    },
]
