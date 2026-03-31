# Bug Taxonomy & Resolution Log

**Project:** Watch-Listen-Act (WLA)
**Phase:** 1 — Bug Hunting & Stabilization

---

## Bug Register

| ID | Category | Severity | Description | Resolution | Files Changed | Thesis Relevance |
|----|----------|----------|-------------|------------|---------------|-----------------|
| BUGS-01 | LLM Output Handling | High | FastAPI did not catch `JSONDecodeError` from malformed Ollama responses, causing unhandled 500s; empty ChromaDB results were not validated, causing downstream null-reference errors | Wrapped `json.loads` in `try/except JSONDecodeError` → `HTTPException(500)`; added empty-context guard → `HTTPException(422)` with user-facing message; `ragClient.js` forwards `detail` field to frontend | `services/api/routes/qg.py`, `api/src/ragClient.js` | Demonstrates fault isolation between LLM and RAG layers — evidence of systematic error boundary design in Chapter 4 |
| BUGS-02 | Quiz Flow | High | Quiz flow failed to complete end-to-end at all difficulty levels — question generation, answer submission, and feedback rendering had integration gaps | Traced and fixed data-flow issues across topic selection → question generation → answer → feedback cycle; verified at easy, medium, and hard difficulty | `web/src/`, `api/src/routes/` | Validates the core pedagogical loop works reliably before evaluation phases — prerequisite for RAG benchmarking in Chapter 5 |
| BUGS-03 | Auth / Session | Medium | Auth session was not persisted across browser refresh; authenticated users were not redirected away from `/login`, causing double-login confusion | Added `loading` state to `AuthContext` to prevent premature redirect on mount; added `AuthRedirect` component wrapping `/login` route to redirect authenticated users to `/` | `web/src/context/AuthContext.jsx`, `web/src/App.jsx` | Shows auth robustness required for multi-session user testing pilot (UTEST phase) |
| BUGS-04 | Validation | Low | Auth form submit button was not disabled on empty inputs, allowing empty-payload POST requests to reach the API | Added `isValid` derived state (email + password for sign-in; + username for sign-up); applied `disabled={!isValid}` to submit button | `web/src/pages/Auth.jsx` | Demonstrates defensive UX pattern — soft-fail validation without server round-trips; supports Chapter 4 implementation quality narrative |
| BUGS-05 | UI Consistency | Low | Hardcoded `border-radius: 0.6rem` values scattered across SCSS files with no shared token system, making future design changes brittle | Added `:root {}` block to `_variables.scss` with `--primary-color`, `--bg-color`, `--text-color`, `--border-radius`; replaced 3 hardcoded occurrences with `var(--border-radius)` | `web/src/styles/base/_variables.scss`, `_buttons.scss`, `_forms.scss` | Establishes token foundation for Phase 2 Design Token System; documents CSS architecture evolution in Chapter 4 |

---

## Categories

| Category | Description |
|----------|-------------|
| LLM Output Handling | Errors originating from malformed or missing LLM responses |
| Quiz Flow | End-to-end integration failures in the core quiz pipeline |
| Auth / Session | Authentication state management and session persistence issues |
| Validation | Missing or incomplete client-side input validation |
| UI Consistency | Visual inconsistencies, hardcoded values, and layout regressions |

---

## Severity Scale

| Level | Criteria |
|-------|----------|
| High | Blocks core user flow or causes unhandled crashes |
| Medium | Degrades UX or causes inconsistent behaviour across sessions |
| Low | Minor UX gap or code quality issue with no functional impact |
