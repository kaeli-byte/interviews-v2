---
phase: 1
slug: core-foundation
status: draft
shadcn_initialized: false
preset: none
created: 2026-03-27
---

# Phase 1 — UI Design Contract

> Visual and interaction contract for frontend phases. Generated for Phase 1: Core Foundation.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none (vanilla JS) |
| Preset | not applicable |
| Component library | none (vanilla HTML/CSS) |
| Icon library | Lucide icons (via CDN) |
| Font | System fonts (-apple-system, BlinkMacSystemFont, Segoe UI, Roboto) |

---

## Spacing Scale

Declared values (must be multiples of 4):

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Icon gaps, inline padding |
| sm | 8px | Compact element spacing |
| md | 16px | Default element spacing |
| lg | 24px | Section padding |
| xl | 32px | Layout gaps |
| 2xl | 48px | Major section breaks |
| 3xl | 64px | Page-level spacing |

Exceptions: none

---

## Typography

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
| Body | 16px | 400 | 1.5 |
| Label | 14px | 500 | 1.4 |
| Heading | 24px | 600 | 1.3 |
| Display | 32px | 700 | 1.2 |

---

## Color

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | #ffffff | Background, surfaces |
| Secondary (30%) | #f8fafc | Cards, sidebar, nav |
| Accent (10%) | #0ea5e9 | Primary buttons, links, active states |
| Destructive | #ef4444 | Delete actions, errors |

Accent reserved for: primary CTAs, active button states, links, status indicators

---

## Copywriting Contract

| Element | Copy |
|---------|------|
| Primary CTA | "Start Interview" |
| Empty state heading | "No documents yet" |
| Empty state body | "Upload a resume or paste a job description to get started" |
| Error state | "Something went wrong. Please try again." |
| Destructive confirmation | "Delete document: This action cannot be undone." |

---

## Page Layouts

### 1. Landing/Auth Page
- Centered card layout
- Logo/title at top
- Sign up / Login tabs
- Email, password fields
- Submit button

### 2. Dashboard (Post-Auth)
- Top navigation bar with user menu
- Left sidebar: navigation (Documents, Sessions, Settings)
- Main content area:
  - Document list with upload buttons
  - Recent sessions list
  - Quick actions (New Interview)

### 3. Document Upload Modal
- Tab interface: Upload File / Paste Text / Import from URL
- File: drag-and-drop zone + file picker
- Text: textarea
- URL: input field + import button
- Progress indicator during processing

### 4. Profile View Panel
- Extracted data display (name, headline, skills, experience)
- Confidence score badge
- Edit option (future phase)

### 5. Interview Context Creation
- Two-column: Resume profile | Job profile
- "Create Interview" button to bind them
- Interview type selector (HR Manager, Hiring Manager, etc.)

### 6. Live Interview Session
- Existing layout from index.html
- Left panel: video preview, controls (mic, camera, screen share)
- Right panel: chat log, text input
- Status indicator (connecting, active, paused)
- Pause/Resume/End buttons

---

## Component States

### Buttons
- Default: accent background, white text
- Hover: slightly darker accent
- Active: pressed effect
- Disabled: gray, reduced opacity

### Form Inputs
- Default: border, white background
- Focus: accent border, subtle glow
- Error: red border, error message below
- Disabled: gray background

### Cards
- White background
- Subtle shadow (0 1px 3px rgba(0,0,0,0.1))
- Border radius: 8px
- Hover: slight elevation increase

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| none (vanilla) | N/A | N/A |

---

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** pending