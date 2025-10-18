
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
 *      - context_span {number}        How many contextual items/steps are included (integer)
 *      - distractor_strength {number} How strong/convincing the incorrect options are (integer, higher = harder)
 *      - application_share {number}   Fraction between 0 and 1 indicating proportion of application-style questions
 */
export const LEVELS = {
    1: {
        mix: { mcq: 7, yesno: 3 },
        difficulty_profile: { context_span: 1, distractor_strength: 1, application_share: 0.2 },
    },
    2: {
        mix: { mcq: 8, yesno: 2 },
        difficulty_profile: { context_span: 2, distractor_strength: 2, application_share: 0.5 },
    },
    3: {
        mix: { mcq: 9, yesno: 1 },
        difficulty_profile: { context_span: 2, distractor_strength: 3, application_share: 0.7 },
    },
};
