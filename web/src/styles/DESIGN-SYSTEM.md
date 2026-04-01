# WLA Design System

## Rationale

The WLA design token system uses semantic SCSS variables with rem scaling to establish a consistent, accessible visual foundation across the platform. By centralizing all design decisions as named tokens — rather than scattering hardcoded values across component files — future UI phases can change a single variable and have the effect propagate everywhere.

Key principles:
- **Semantic naming** (`$color-primary`, `$spacing-md`) over raw values (`#10b981`, `16px`)
- **rem units** throughout spacing and typography for accessibility scaling (user font size preferences respected)
- **Fixed breakpoint scale** for typography — mathematically proportional rhythm across 1024px, 1550px, and desktop
- **Dark-mode readiness** — CSS custom properties on `:root` mirror the SCSS variables, enabling a future theme switch without component changes

Feeds thesis Chapter 4 — Implementation: design system rationale and component library.

---

## Token Files

All tokens live in `web/src/styles/base/` and are imported via `_variables.scss`:

| File | Purpose |
|------|---------|
| `_colors.scss` | Brand palette, semantic aliases, feedback colors, component color tokens |
| `_typography.scss` | Font families, size scale, weights, line heights, responsive rules |
| `_spacing.scss` | Spacing scale, elevation shadows, border-radius tokens |
| `_animations.scss` | Transition timing tokens |

---

## Color Palette

### Brand

| Token | Value | Role |
|-------|-------|------|
| `$color-primary` | `#10b981` | Primary actions, progress indicators |
| `$color-primary-light` | `#cbf7e0` | Hover states, backgrounds |
| `$color-primary-dark` | `#065f46` | Active states, focus rings |
| `$color-secondary` | `#f59e0b` | Secondary actions, creativity accent |
| `$color-accent` | `#3b82f6` | Trust, focus, informational |

### Surface

| Token | Value | Role |
|-------|-------|------|
| `$color-bg` | `#fafafa` | Page background |
| `$color-bg-card` | `#f5f5f5` | Card / panel surfaces |
| `$color-text` | `#1f2937` | Primary text |
| `$color-text-secondary` | `#4b5563` | Secondary text |
| `$color-text-muted` | `#9ca3af` | Placeholders, hints |
| `$color-border` | `#e5e7eb` | Dividers, input borders |

### Feedback

| Token | Value | Role |
|-------|-------|------|
| `$color-success` | `#22c55e` | Correct answers, success states |
| `$color-warning` | `#facc15` | Caution indicators |
| `$color-error` | `#ef4444` | Errors, incorrect answers |
| `$color-info` | `#0ea5e9` | Informational notices |

---

## Typography Scale

Fonts: **Inter** (headings, 700) · **Source Sans Pro** (body, 400/700)

| Token | Value | Breakpoint behavior |
|-------|-------|-------------------|
| `$font-size-h1` | `2.5rem` | Scales down at ≤1550px and ≤1024px |
| `$font-size-h2` | `1.875rem` | Scales proportionally |
| `$font-size-h3` | `1.5rem` | Scales proportionally |
| `$font-size-h4` | `1.125rem` | Scales proportionally |
| `$font-size-base` | `1rem` (16px) | Body text baseline |
| `$font-size-sm` | `0.875rem` (14px) | Secondary text, labels |

The base font size is set in `_typography.scss` at `16px`. At ≤1550px and ≤1024px, headings step down proportionally via `@media` rules — rem units mean user browser font size preferences are always respected.

---

## Spacing & Elevation

All spacing uses `rem` to scale with the base font size.

| Token | Value | px equivalent |
|-------|-------|--------------|
| `$spacing-xs` | `0.25rem` | 4px |
| `$spacing-sm` | `0.5rem` | 8px |
| `$spacing-md` | `1rem` | 16px |
| `$spacing-lg` | `1.5rem` | 24px |
| `$spacing-xl` | `2rem` | 32px |
| `$spacing-2xl` | `3rem` | 48px |
| `$spacing-3xl` | `4rem` | 64px |

### Elevation

| Token | Value |
|-------|-------|
| `$elevation-1` | `0 1px 3px rgba(0,0,0,0.1)` |
| `$elevation-2` | `0 4px 6px rgba(0,0,0,0.1)` |
| `$elevation-3` | `0 10px 15px rgba(0,0,0,0.1)` |

---

## Animation Timings

| Token | Value | Use case |
|-------|-------|---------|
| `$transition-fast` | `150ms ease-in-out` | Hover feedback, button states |
| `$transition-standard` | `300ms ease-in-out` | Panel transitions, dropdowns |
| `$transition-slow` | `500ms ease-in-out` | Page-level transitions |

---

## Usage

Import tokens in any SCSS file via the main entry point:

```scss
// Already imported globally via web/src/styles/main.scss
// Direct use in component files:
.my-component {
  color: $color-primary;
  padding: $spacing-md;
  transition: color $transition-fast;
  box-shadow: $elevation-1;
}
```

---

## Component Library

All base components live in `web/src/styles/base/` and `web/src/styles/components/`. They consume tokens from the design system — no hardcoded values.

### Buttons (`_buttons.scss`)

Base class `.btn` + one variant modifier. Optionally `.btn-sm`, `.btn-lg`, `.btn-block`.

| Class | Token backing | Use case |
|-------|--------------|---------|
| `.btn-primary` | `$btn-primary-bg`, `$btn-primary-hover` | Main CTA — submit, confirm |
| `.btn-secondary` | `$btn-secondary-bg`, `$btn-secondary-hover` | Supporting action |
| `.btn-accent` | `$btn-accent-bg`, `$btn-accent-hover` | Informational action |
| `.btn-outline-primary` | `$primary`, `$primary-light` | Low-weight primary |
| `.btn-outline-accent` | `$accent`, `$accent-light` | Low-weight accent |
| `.btn-success` | `$color-success` | Correct / positive outcome |
| `.btn-warning` | `$color-warning` | Caution action |
| `.btn-error` | `$color-error` | Destructive / incorrect |

All buttons share: `$font-family-heading` (Inter 700), `$focus-ring` focus ring, `var(--border-radius)` radius, `transform: translateY(1px)` on `:active`. Disabled state uses `$btn-disabled-bg`.

### Form Inputs (`_forms.scss`)

Classes `.input` and `.textarea`. State modifiers:

| Modifier | Token | When |
|----------|-------|------|
| *(default)* | `$border-color`, `$bg-card` | Idle |
| `:hover` | `$gray-300` border | Mouse over |
| `:focus` | `$focus-ring` border + ring | Keyboard/click focus |
| `.is-error` | `$color-error` border + ring | Validation failure |
| `.is-success` | `$color-success` border + ring | Validation pass |
| `:disabled` / `.is-disabled` | `$gray-100` bg, `$text-secondary` | Non-interactive |

### Layout Components

| Component | File | Key tokens |
|-----------|------|-----------|
| Navbar | `components/_navbar.scss` | `$navbar-bg` (`$color-text`), `$navbar-text` (#fff) |
| Sidebar | `components/_sidebar.scss` | `$sidebar-bg`, `$sidebar-hover`, `$sidebar-active` |
| Panel | `components/_panel.scss` | `$bg-card`, `$border-color`, `$elevation-1/2` |
| Header | `components/_header.scss` | `$color-text`, `$color-bg` |
| Footer | `components/_footer.scss` | `$color-text-muted`, `$color-border` |

### Quiz Components (`components/_quiz.scss`)

Quiz answer feedback uses the feedback color system:
- Correct answer → `$color-success`
- Incorrect answer → `$color-error`
- Neutral/unselected → `$color-bg-card`, `$color-border`

### Progress Charts (`components/_progress.scss`)

Progress visualizations use `$color-primary` as the primary data series color, with `$color-accent` for secondary series and `$gray-200` for grid/background tracks.

---

## Component Token Dependency Map

```
Buttons ──────── $btn-*-bg, $btn-*-hover, $focus-ring, $btn-disabled-bg
Forms ──────────  $border-color, $bg-card, $text-primary, $text-muted, $focus-ring, $color-error, $color-success
Navbar ──────────  $navbar-bg → $color-text, $navbar-text
Sidebar ─────────  $sidebar-bg, $sidebar-hover, $sidebar-active → $color-primary-light
Quiz ────────────  $color-success, $color-error, $color-bg-card
Progress ────────  $color-primary, $color-accent, $gray-200
```

All component tokens resolve to the 19 semantic `$color-*` primitives defined in `_colors.scss`. Changing a primitive propagates through every component that uses it.

---

*Design system established: 2026-04-01 — Phase 2 (UI-01, UI-08)*
