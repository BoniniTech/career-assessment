---
name: career-assessment-find-fresh-category
description: >
  Analyses the existing category taxonomy against the current axis space to
  identify underserved regions — combinations of axis scores that no current
  category occupies. Proposes one new category per run derived from axis
  coverage gaps. May optionally surface a second category if a real-world
  gap is independently obvious. Does not write to any file without explicit
  facilitator approval.
---

# Career Assessment — Find Fresh Category

## Trigger

This skill runs when the opening message is `career-assessment-find-fresh-category`, optionally followed by flags or notes.

No other phrasing triggers this skill.

---

## Purpose

The category taxonomy may have blind spots — regions of the axis space that are legitimately occupied by real career fields but are not represented in `categories.yaml`. This skill surfaces those gaps systematically and proposes a concrete new category to fill them.

---

## Pre-flight (optional)

Run `python scripts/analytics.py review` before beginning the analysis. The category coverage table shows which categories surface rarely in top-5 results across synthetic profiles. Low-coverage categories point toward axis regions that may be underserved or scoring-misaligned — both are useful context for gap selection. Skip this step if the log is empty or stale.

---

## Behaviour on Invocation

### Step 1 — Load source files

Read `live/dimensions.yaml` and `live/categories.yaml` in full before doing any analysis. All axis IDs, types, score ranges, and activation conditions used in subsequent steps must come from these files — do not rely on memorised names or a hardcoded list.

---

### Step 2 — Classify axes and map the space

**Classify axes directly from `live/dimensions.yaml`:**
- **Primary axes** — all axes where no `activation:` field is present. These are always active during a session and define the primary coverage map.
- **Secondary axes** — all axes where an `activation:` field is present. These sharpen distinctions within a region but only activate for a subset of profiles; they are not useful for initial gap mapping.

Using the primary axes, assess coverage across the existing categories:
- For each bipolar primary axis, note which score regions (low 0–3, mid 4–6, high 7–10) are well-served, sparse, or empty across all categories.
- For each unipolar primary axis, note which combinations of high-signal vs. low-signal are well-served or absent.
- Focus on multi-axis combinations — single-axis extremes are already captured by existing categories; coherent gaps typically span at least two dimensions simultaneously.

**Heuristics for a meaningful gap:**
- At least 2 primary axes point clearly into this region
- No existing category scores close to this region on those axes
- The profile would produce a recognisably distinct type of work

Do not report every empty corner of the axis space — only regions that plausibly correspond to a missing real career field.

---

### Checkpoint — Gap Map

Present a brief gap map: 2–3 regions of the axis space that look sparsest or most under-served, with one sentence of reasoning per region. Then stop and ask:

> "Here's the gap landscape as I see it — which of these regions would you like me to develop into a full proposal? Or I can pick the most compelling one."

Wait for the facilitator to respond before writing the full proposal.

---

### Step 3 — Primary suggestion: axis-gap-derived category

Based on the confirmed gap, propose a category to fill it.

**Before proposing, confirm:**
- [ ] No existing category already covers this space. Compute the L1 distance between the proposed category and every existing category: L1 = sum of |proposed_score − existing_score| across all axes. Name the closest and state its L1 distance.
- [ ] The proposed category is meaningfully distinct from its nearest existing neighbour — the L1 distance and the nature of the differentiating axes should both support this.
- [ ] The category is coherent — it describes a real field, not an artificial construct built to fill a coordinate.

**Output format:**

> **Proposed category: [Name]**
>
> - **Gap this fills:** [Which primary axes, what score region, which existing categories come closest and why they don't fully cover this]
> - **Description:** [2–3 sentence description in the style of existing categories — what people in this field do, what it requires, what kind of person it suits]
> - **Role hint:** [One sentence describing illustrative job titles, matching the format in `categories.yaml`]
> - **Proposed axis scores:** [Full axis score table covering every axis in `live/dimensions.yaml`, with a one-line rationale for any score that might be non-obvious]
> - **Nearest existing category:** [Name, L1 distance, and a concrete explanation of why this new category is distinct enough to warrant a separate entry]

**Do not write to `categories.yaml`.** This is a proposal for discussion only.

---

### Step 4 — Optional secondary suggestion: real-world obvious gap

Only include this section if a real-world career field comes to mind that is clearly missing and would not have emerged from the axis-gap analysis alone — i.e. something that feels like an obvious omission rather than a coordinate-derived gap.

The bar for inclusion is: *if a young person said "I want to do X" and this assessment gave them no match, that would feel like a failure.*

This section appears in fewer than half of sessions. Do not force it. If nothing meets the bar, omit the section entirely without comment.

**Output format (if triggered):**

> **Optional: Real-world gap — [Name]**
>
> - **Why it's missing:** [One paragraph — why this field isn't captured by any existing category]
> - **Description:** [2–3 sentences in the style of existing categories]
> - **Role hint:** [One sentence]
> - **Proposed axis scores:** [Full axis score table covering every axis in `live/dimensions.yaml`, with rationale for non-obvious scores]
> - **Nearest existing category:** [Name, L1 distance, and why this is distinct]

---

### Step 5 — Close

After all suggestions, briefly note:

1. Other regions of the axis space that are sparse but not yet compelling enough to propose (one sentence each — plant seeds for future runs)
2. If the facilitator wants to proceed with adding a category, refer them to `docs/category-addition-workflow.md` for the full addition process.

---

## What This Skill Does Not Do

- Does not write to any file
- Does not propose more than two categories per session (and typically proposes one)
- Does not propose new axes (that is `career-assessment-find-fresh-axis`)
- Does not analyse category-pair closeness (that is `career-assessment-find-fresh-axis`)

---

## Session Statefulness

Each invocation analyses the current state of `live/categories.yaml` and `live/dimensions.yaml` fresh. No session history is tracked — the files themselves are the state. If a category was added in a previous session, the gap map will shift and a different gap should naturally emerge.
