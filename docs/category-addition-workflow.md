# Category Addition Workflow

Step-by-step process for adding an approved category to `live/categories.yaml`. Follow all steps in order.

A category is "approved" when the facilitator has reviewed a proposal from `career-assessment-find-fresh-category` (or another source) and confirmed it should be added. Do not begin this workflow until you have a full set of axis scores and a confirmed category description.

---

## Step 1 — Verify the proposal is complete

Before touching any file, confirm the proposal has all required fields:

- **id** — unique, lowercase, underscore-separated (e.g. `sports_coaching`, `forensic_science`)
- **name** — short display name in title case
- **description** — 2–3 sentences: what people in this field do, what it requires, what kind of person it suits. Match the register of existing descriptions.
- **role_hint** — one sentence of illustrative job titles, e.g. `"Roles in X, Y, and Z"`
- **axis scores** — a score for every axis defined in `live/dimensions.yaml`. No omissions. Check the file directly to confirm the current axis list — do not rely on memory.

If any field is missing, complete it before proceeding.

---

## Step 2 — Add the entry to `live/categories.yaml`

Open `live/categories.yaml`. Place the new entry in the most appropriate section (Sciences, Engineering & Technology, Medicine & Care, Arts & Design, Business & Law, Education & Community, Trades & Practical Skills, Nature & Environment, Craft & Making, Data & Analysis, People & Influence, Outdoor & Adventure Services). Add a new section header if the category genuinely doesn't fit any existing one.

Use this format exactly:

```yaml
  - id: [category_id]
    name: "[Display Name]"
    description: >
      [First sentence — what people do.]
      [Second sentence — what it requires.]
      [Third sentence — who it suits.]
    role_hint: "[One sentence of illustrative job titles]"
    axes:
      things_people: [score]
      master_create: [score]       # optional inline rationale for non-obvious scores
      analyze: [score]
      concrete_abstract: [score]
      flexible_structured: [score]
      nurturing: [score]
      solo_group: [score]
      indoors_outdoors: [score]
      inform_express: [score]
      animals_people: [score]
```

**Axis ordering:** match the order used in existing entries (things_people first, animals_people last). This is a readability convention — the YAML parser doesn't care, but diffs are easier to review.

**Inline comments:** add a short rationale comment (`# ...`) for any score that a reviewer might question. No need to comment obvious scores.

**Do not omit any axis.** A missing axis key causes a silent matching error — the category receives a neutral score on that axis without warning, which may push it into the wrong matches.

---

## Step 3 — Validate

```
python scripts/validate_yaml.py categories
```

Fix any errors before continuing. Common issues:

- Missing axis key (every axis in `dimensions.yaml` must appear in every category)
- Score out of range (all scores must be integers in [0, 10])
- Duplicate category ID
- YAML indentation error

The validator also checks that all axis IDs in `categories.yaml` exist in `dimensions.yaml`. If you're adding a category with a newly created axis, ensure that axis is already committed to `dimensions.yaml` first.

---

## Step 4 — Run analytics to check coverage impact (recommended)

```
python scripts/analytics.py run 100
```

Check the batch summary:

- Does the new category appear in top-5 results for at least one archetype? If it never surfaces across 100 profiles, its axis scores may not be distinct enough — it may be too close to an existing category to compete.
- Did any existing category's coverage drop sharply? A large drop suggests the new category is pulling profiles away from an existing one — confirm this is intentional (i.e. the new category is genuinely more accurate for those profiles, not just similar).
- Are there any new "COVERAGE GAP" flags on existing categories? If so, note for future review.

This step doesn't block the commit, but the output is useful context for the PR description.

---

## Step 5 — Commit

Stage `live/categories.yaml` only. Do not stage unrelated files.

```
git add live/categories.yaml
```

If the addition required any corrections to existing axis scores (e.g. re-scoring an existing category after noticing a misalignment), those corrections go in the same commit with a clear explanation in the commit message.

Commit message format:
```
feat: add [Category Name] category

[One sentence explaining the gap it fills and why it was added.]
```

---

## Step 6 — Run a validation test session (recommended for significant additions)

For categories that occupy a genuinely new region of the axis space, run a short test session using `career-assessment` with a synthetic profile designed to surface the new category. Verify:

- The new category appears in the top 5 for a profile that should match it
- The category does not appear in the top 5 for profiles clearly outside its region
- The description and role_hint read naturally when presented in an assessment debrief

For minor additions (e.g. a sub-field that is very similar to an existing category), this step can be skipped.

---

## Summary

| Step | Action | Required |
|---|---|---|
| 1 | Proposal has all required fields | Yes |
| 2 | Entry added to `categories.yaml` with all axes scored | Yes |
| 3 | `python scripts/validate_yaml.py categories` passes | Yes |
| 4 | Analytics run to check coverage impact | Recommended |
| 5 | Commit staged | Yes |
| 6 | Validation test session | Recommended for new regions |
