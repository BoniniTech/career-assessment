# Career Matching Assessment

A career matching assessment for children and young people. A facilitator runs a session with one person at a time. Claude asks an adaptive series of "Would You Rather" questions, builds a personality profile across multiple dimensions, then outputs a ranked list of career categories with example job titles and a short explanation of why each matched.

---

## Repository Structure

```
career-assessment/
├── live/
│   ├── dimensions.yaml          # Scoring axes — source of truth for all axis IDs, score ranges, types, and activation conditions
│   ├── categories.yaml          # Career categories, each tagged with axis scores and a role_hint
│   └── career-assessment.md     # Main assessment skill, synced to Claude.ai
├── docs/
│   ├── design-decisions.md      # Non-obvious axis typing decisions — read before structural changes
│   └── axis-addition-workflow.md # Step-by-step process for adding a new axis
├── scripts/
│   ├── recalc.py                # Recomputes axis priority order from live data; runs automatically on commit
│   └── validate_yaml.py         # Validates dimensions.yaml and categories.yaml structure
└── skills/
    ├── career-assessment-analytics/
    ├── career-assessment-find-fresh-axis/
    └── career-assessment-find-fresh-category/
```

---

## Skills

Each skill has an exact trigger — Claude does not run a skill unless its trigger is matched precisely.

| Skill | Trigger | Description |
|---|---|---|
| Career Assessment | `career-assessment` or `career-assessment --debug` | Runs the full career matching assessment. Handles demographics, adaptive questioning, scoring, and output. `--debug` adds facilitator notes and auto-debrief. |
| Analytics & Validation | `career-assessment-analytics` | Generates synthetic profiles, runs batch scoring, and produces diagnostic reports to identify weak axes and category coverage gaps. |
| Find Fresh Axis | `career-assessment-find-fresh-axis` | Identifies the closest-scoring category pair, checks for dimension misalignments, and proposes a new axis that would differentiate the pair. Discussion-only — does not write to any file without approval. |
| Find Fresh Category | `career-assessment-find-fresh-category` | Analyses the axis space for underserved regions and proposes one new category per run. Discussion-only — does not write to any file without approval. |

### Adding a new skill
1. Add a row to the table above with the skill name, trigger, and a one-line description.
2. Ensure the skill's `SKILL.md` clearly states its own trigger so it is self-contained.
3. Verify the new trigger does not conflict with any existing trigger.

---

## Data Files

### `dimensions.yaml`
Defines the 10 scoring axes used to profile a person's working preferences. Each axis has:
- `id` — used as the key in `categories.yaml` scoring
- `type` — `bipolar`, `unipolar`, or `conditional`
- `score_range` — always `[0, 10]`
- `priority` — session probing order (1 = first)
- `min_questions` — minimum confirmed answers before axis is treated as resolved
- `dominant` — optional; marks axes that warrant guaranteed Tier 1 placement

Current axes: `things_people`, `master_create`, `analyze`, `flexible_structured`, `nurturing`, `solo_group`, `indoors_outdoors`, `inform_express`, `concrete_abstract`, `animals_people`

Conditional axes (`concrete_abstract`, `animals_people`) are only probed when their upstream activation condition is met.

### `categories.yaml`
Defines career categories, each scored against all 10 axes. Used by the main assessment skill to rank and match categories to a profile. The `role_hint` field guides Claude in generating 4–6 illustrative job title examples per matched category.

---

## Session Behaviour

If the opening message matches a skill trigger exactly, load and follow that skill's `SKILL.md`. If the input is not a recognised skill command, respond:

> "To start the career assessment, type: `career-assessment`"

---

## License

[MIT](LICENSE)
