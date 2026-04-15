
/**
 * @fileoverview Defines configuration for assessment levels used by the application.
 *
 * Exports a LEVELS mapping where each numeric key represents an assessment level and
 * maps to an object describing the composition and difficulty profile for that level.
 *
 * Structure of each level entry:
 *  - mix: Object describing the distribution of question types
 *      - mcq {number}      Number of multiple-choice questions
 *      - yesno {number}    Number of yes/no questions
 *
 *  - difficulty_profile: Object controlling difficulty characteristics
 *      - difficulty_label {string}    "beginner" | "intermediate" | "advanced" — maps to
 *        cognitive-level instructions in services/llm/prompts.py DIFFICULTY_INSTRUCTIONS
 */
export const LEVELS = {
    1: {
        mix: { mcq: 7, yesno: 3 },
        difficulty_profile: { difficulty_label: "beginner" },
    },
    2: {
        mix: { mcq: 8, yesno: 2 },
        difficulty_profile: { difficulty_label: "intermediate" },
    },
    3: {
        mix: { mcq: 9, yesno: 1 },
        difficulty_profile: { difficulty_label: "advanced" },
    },
};
