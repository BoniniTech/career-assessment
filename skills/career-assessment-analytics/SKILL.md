---
name: career-assessment-analytics
description: >
  Analytics and validation tool for the career matching assessment. Triggers ONLY
  on the exact command "career-assessment-analytics", optionally followed by
  subcommands. Generates synthetic profiles, runs them through the scoring and
  matching logic, and produces diagnostic output to identify weak axes and
  category coverage gaps. Do not trigger on any other phrasing.
---

# Career Assessment — Analytics & Validation

## Trigger

This skill runs when the opening message is `career-assessment-analytics`, optionally
followed by a subcommand:

- `career-assessment-analytics run <n>` — batch mode, generate and score N synthetic profiles
- `career-assessment-analytics run <n> --verbose` — batch mode with full per-profile diagnostic output
- `career-assessment-analytics run <n> --archetype <n>` — batch restricted to one archetype seed
- `career-assessment-analytics review` — load and summarise the existing session log without running new profiles

No other phrasing triggers this skill.

---

## Behaviour on invocation

### `run <n>`
1. Generate N synthetic profiles using the profile generation algorithm below
2. Run scoring and matching on each profile using the matching logic from the assessment skill
3. Append all N records to the session log JSON file
4. Output a batch summary report (see Batch Summary Report below)

### `run <n> --verbose`
Same as `run <n>` but also output the full per-profile diagnostic for every profile
after the batch summary. Use sparingly — verbose output for large batches is long.

### `run <n> --archetype <n>`
Same as `run <n>` but all profiles are generated from the named archetype seed only.
Useful for stress-testing a specific corner of the axis space.

### `review`
Load the session log, compute aggregate statistics across all records, and output
a review report (see Review Report below). Does not generate new profiles.

### Bare invocation
Output a brief status: number of records in the session log, date of last run,
and a one-line summary of the current top weak axes from the log. Then wait.

---

## Session Log

**File path:** `analytics/log.json` (repo-relative, gitignored)

The log is a JSON array of profile run records. Each batch run appends N new records.
The file is created on first run if it does not exist.

**Never overwrite the log.** Always append. The log is the cumulative dataset.

### Record schema

```json
{
  "run_id": "<uuid-v4>",
  "timestamp": "<ISO8601>",
  "batch_id": "<uuid-v4>",
  "archetype": "<archetype_name>",
  "axis_scores": {
    "things_people": 0,
    "master_create": 0,
    "analyze": 0,
    "flexible_structured": 0,
    "nurturing": 0,
    "solo_group": 0,
    "indoors_outdoors": 0,
    "inform_express": 0,
    "concrete_abstract": 0,
    "animals_people": 0
  },
  "conditional_axes": {
    "concrete_abstract": { "activated": true, "reason": "analyze >= 6" },
    "animals_people": { "activated": false, "reason": "condition not met" }
  },
  "top_5": [
    {
      "rank": 1,
      "category_id": "<id>",
      "match_score": 0.0,
      "driving_axes": [],
      "neutral_axes": [],
      "opposing_axes": []
    }
  ],
  "match_margin": {
    "top1_to_top2": 0.0,
    "top5_to_top6": 0.0
  },
  "weak_axes": [],
  "tightly_clustered": false
}
```

**Field notes:**
- `batch_id` — shared across all records in the same `run` invocation
- `axis_scores` — raw 0–10 scores. Conditional axes that were not activated are stored as `null`, not 0
- `conditional_axes` — always present for both conditional axes, records activation decision and reason
- `match_score` — normalised 0–1, higher is better match
- `driving_axes` — axes where the profile score and category score were closely aligned and the category score was far from neutral (i.e. the axis actively pulled this category up)
- `opposing_axes` — axes where the profile score and category score diverged significantly (pulled the category down)
- `neutral_axes` — axes where either the profile or the category scored in the neutral band and the axis had little discriminating effect
- `weak_axes` — axes that were active for this profile but did not affect the top 5 ranking (i.e. score variation across top 5 categories on this axis was below threshold)
- `tightly_clustered` — true if top1_to_top2 margin < 0.05 AND top5_to_top6 margin < 0.08

---

## Profile Generation Algorithm

Profiles are generated from archetype seeds with gaussian noise applied per axis.
This produces realistic variance without generating statistically implausible profiles.

### Generation steps

1. Select an archetype seed (randomly, or as specified by `--archetype`)
2. For each axis in the seed, apply gaussian noise: `score = clamp(seed_value + N(0, σ), 0, 10)`
   - Use σ = 1.5 for primary axes (the axes that define the archetype)
   - Use σ = 2.5 for secondary axes (axes the archetype doesn't strongly define)
   - Round to nearest integer
3. Enforce conditional axis rules:
   - If `analyze < 6 AND master_create < 7`: set `concrete_abstract` to `null` (not activated)
   - If `nurturing < 7 AND things_people < 7`: set `animals_people` to `null` (not activated)
   - If activated, generate the conditional axis score using the same noise algorithm
4. Validate: no axis score outside [0, 10]. Re-clamp if noise pushed beyond bounds.

### Archetype seeds

Each archetype is defined by its axis scores. Primary axes (σ = 1.5) are marked with *.

---

**`analytical_indoor`**
The researcher, scientist, mathematician. Strong analytical drive, abstract thinking,
works alone, indoors, informs rather than expresses.

| Axis | Seed | Primary |
|---|---|---|
| things_people | 2 | * |
| master_create | 4 | |
| analyze | 9 | * |
| flexible_structured | 7 | * |
| nurturing | 3 | |
| solo_group | 3 | * |
| indoors_outdoors | 2 | * |
| inform_express | 2 | * |
| concrete_abstract | 8 | * |
| animals_people | 5 | |

---

**`creative_expressive`**
The artist, designer, writer. Strong creative drive, expressive, flexible, works solo
or in small groups, indoor studio environment.

| Axis | Seed | Primary |
|---|---|---|
| things_people | 4 | |
| master_create | 9 | * |
| analyze | 3 | |
| flexible_structured | 3 | * |
| nurturing | 4 | |
| solo_group | 3 | * |
| indoors_outdoors | 3 | * |
| inform_express | 9 | * |
| concrete_abstract | 5 | |
| animals_people | 5 | |

---

**`care_dominant`**
The nurse, social worker, counsellor. Strong caring and people drive, team-oriented,
indoors, informs, people over animals.

| Axis | Seed | Primary |
|---|---|---|
| things_people | 8 | * |
| master_create | 3 | |
| analyze | 5 | |
| flexible_structured | 6 | |
| nurturing | 9 | * |
| solo_group | 6 | * |
| indoors_outdoors | 2 | * |
| inform_express | 3 | * |
| concrete_abstract | 4 | |
| animals_people | 8 | * |

---

**`practical_outdoor`**
The ecologist, ranger, outdoor instructor. Outdoors, concrete, things-oriented,
moderate caring drive, flexible, solo or small team.

| Axis | Seed | Primary |
|---|---|---|
| things_people | 3 | |
| master_create | 4 | |
| analyze | 6 | |
| flexible_structured | 4 | * |
| nurturing | 5 | |
| solo_group | 4 | |
| indoors_outdoors | 8 | * |
| inform_express | 3 | |
| concrete_abstract | 3 | * |
| animals_people | 4 | |

---

**`builder_engineer`**
The engineer, software developer, architect. Makes new things, analytical, structured,
indoors, things-oriented, team or solo depending on subdiscipline.

| Axis | Seed | Primary |
|---|---|---|
| things_people | 2 | * |
| master_create | 7 | * |
| analyze | 7 | * |
| flexible_structured | 7 | * |
| nurturing | 3 | |
| solo_group | 5 | |
| indoors_outdoors | 2 | * |
| inform_express | 3 | |
| concrete_abstract | 6 | * |
| animals_people | 5 | |

---

**`people_leader`**
The entrepreneur, manager, sales lead, recruiter. People-facing, team-oriented,
moderate create drive, flexible, indoors, mix of express and inform.

| Axis | Seed | Primary |
|---|---|---|
| things_people | 8 | * |
| master_create | 6 | |
| analyze | 5 | |
| flexible_structured | 5 | |
| nurturing | 5 | |
| solo_group | 8 | * |
| indoors_outdoors | 2 | * |
| inform_express | 6 | * |
| concrete_abstract | 5 | |
| animals_people | 7 | * |

---

**`master_craftsperson`**
The skilled tradesperson, clinical practitioner, specialist. Deep mastery drive,
concrete, structured, low create, moderate caring, variable on people/things.

| Axis | Seed | Primary |
|---|---|---|
| things_people | 5 | |
| master_create | 2 | * |
| analyze | 5 | |
| flexible_structured | 7 | * |
| nurturing | 6 | |
| solo_group | 4 | |
| indoors_outdoors | 3 | |
| inform_express | 3 | * |
| concrete_abstract | 3 | * |
| animals_people | 6 | |

---

**`analytical_helper`**
The doctor, researcher, lawyer, policy analyst. High analysis, high nurturing or people
drive, structured, indoors, informs. Straddles science and care.

| Axis | Seed | Primary |
|---|---|---|
| things_people | 6 | |
| master_create | 4 | |
| analyze | 8 | * |
| flexible_structured | 7 | * |
| nurturing | 7 | * |
| solo_group | 5 | |
| indoors_outdoors | 2 | * |
| inform_express | 3 | * |
| concrete_abstract | 6 | * |
| animals_people | 7 | * |

---

## Scoring & Matching Logic

Use the same logic as the assessment skill. Reproduced here for self-containment.

### Match score calculation

For each category, compute a match score (0–1) as follows:

1. For each **bipolar axis** that was active (not null):
   - penalty = |profile_score - category_score| / 10
   - contribution = 1 - penalty

2. For each **unipolar axis** (analyze, nurturing):
   - If profile scores HIGH (≥7) and category scores LOW (≤3): large penalty
   - If profile scores LOW (≤3): no penalty regardless of category score — low unipolar signal is neutral
   - Otherwise: scaled partial penalty

3. For each **conditional axis** that was NOT activated: exclude entirely — do not penalise distance

4. Weight axes by signal strength:
   - Axes with scores ≤2 or ≥8 on the profile: weight 1.3 (strong signal)
   - Axes with scores 3–4 or 6–7: weight 1.0 (moderate signal)
   - Axes with scores 4–6 (neutral band): weight 0.7 (weak signal — don't over-index)

5. Final match score = weighted average of all active axis contributions, normalised to [0, 1]

### Identifying driving, neutral, and opposing axes

For each top-5 category match, classify each active axis:

- **Driving:** profile and category scores within 2 points of each other, AND at least one of them is outside the neutral band (i.e. the axis had something meaningful to align on)
- **Opposing:** profile and category scores differ by 4 or more points
- **Neutral:** everything else — one or both scores in the neutral band, or difference < 4 but not closely aligned

### Identifying weak axes

An axis is **weak for a given profile** if, across the top 5 matched categories, the
variation in that category's axis score is below threshold:

- Compute the range of category scores for this axis across the top 5 matches
- If range ≤ 2: the axis made no discriminating contribution — mark as weak
- Exception: if the profile score on this axis is in the neutral band (4–6), the axis
  may legitimately not discriminate — flag as **neutral-profile weak** rather than
  structurally weak, and weight it less in aggregate analysis

---

## Batch Summary Report

Output after every `run <n>` invocation. Covers all N profiles in the batch.

---

**📊 Batch Summary — [N] profiles — [timestamp]**
*Archetypes: [distribution of archetypes in this batch]*

**Weak Axis Ranking**
Axes ranked by how often they failed to discriminate across the top 5, as a percentage
of profiles where the axis was active. Higher = weaker.

| Axis | Active in N profiles | Weak in N profiles | Weak % | Structurally weak % |
|---|---|---|---|---|
| ... | | | | |

*Structurally weak % excludes profiles where the axis was neutral-band on the profile
itself — a fairer measure of whether the axis is earning its keep.*

**Category Coverage**
How often each category appeared in a top 5, across all N profiles.

| Category | Appearances | % of profiles |
|---|---|---|
| ... | | |

*Flag any category with < 5% appearance rate — may be under-differentiated or redundant.*

**Match Tightness**
- Tightly clustered profiles (top1_to_top2 < 0.05): N / % of batch
- Well-spread profiles (top5_to_top6 > 0.15): N / % of batch
- Average top1_to_top2 margin: X
- Average top5_to_top6 margin: X

**Per-Archetype Summary**
For each archetype that appeared in this batch, list the top 3 most frequent
top-5 categories. Flag if an archetype's expected categories are absent.

| Archetype | Most frequent top-5 categories | Any expected category absent? |
|---|---|---|
| analytical_indoor | physical_sciences, mathematics_statistics, computer_science_ai | No |
| ... | | |

**Observations**
One short paragraph noting anything anomalous: archetypes that produced unexpected
matches, axes that were consistently weak across all archetypes, categories that
dominated across multiple archetypes (possible over-broad scoring), or any structural
pattern worth investigating in dev-mode.

---

## Review Report

Output for `review` invocations. Covers the full session log.

---

**📊 Session Log Review — [total records] profiles — log started [date] — last run [date]**

Same sections as the Batch Summary Report but computed across the full log.

Additional section:

**Trend over time**
If the log contains records from multiple dates, note whether weak axis rankings
have shifted across runs. A consistently weak axis across many batches is a strong
signal for the chopping block. A newly-weak axis may reflect a recent change to
category scoring or axis definitions.

---

## Diagnostic Flags

The following conditions should be explicitly called out in any report where they appear:

- **Chopping block candidate:** any axis that is structurally weak in > 40% of profiles
  where it was active. Name it explicitly.
- **Coverage gap:** any category appearing in < 3% of top-5 results across the full log.
- **Dominant category:** any category appearing in > 25% of top-5 results — may indicate
  over-broad axis scoring pulling too many profiles toward it.
- **Archetype mismatch:** any archetype whose top-3 most frequent categories do not include
  at least 2 intuitively expected categories (e.g. `analytical_indoor` not surfacing any
  of physical_sciences, mathematics_statistics, computer_science_ai, biological_sciences).
  Flag for review in dev-mode.
