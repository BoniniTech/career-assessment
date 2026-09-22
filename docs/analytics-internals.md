---
title: Analytics Internals
description: How scripts/analytics.py works — profile generation, scoring, weak-axis detection, and diagnostic thresholds. Reference before fine-tuning.
---

# Analytics Internals

How `scripts/analytics.py` works under the hood. Read before adjusting thresholds, modifying the scoring formula, or adding archetypes.

---

## Data sources

Everything is read live at startup — no values are hard-coded in the script.

| Source | Used for |
|---|---|
| `live/dimensions.yaml` | Axis IDs, types (bipolar/unipolar), scoring thresholds (neutral band, unipolar hi/lo), conditional activation condition strings |
| `live/categories.yaml` | Category axis scores used in matching |
| `analytics/archetypes.yaml` | Archetype seed values, sigma config |
| `analytics/log.json` | Persistent run log; appended to on each `run` invocation |

The script validates archetype completeness at startup: if any archetype is missing a seed for an axis defined in `dimensions.yaml`, it errors before generating any profiles. This is the safety net for axis additions.

---

## Profile generation

Profiles are generated from archetype seeds with Gaussian noise applied per axis.

### Sigma derivation

Each axis seed maps to a noise level automatically based on its distance from the neutral midpoint (5):

- Seed **<= 2 or >= 8** (strong, outside neutral band): sigma = `sigma.primary` (default 1.5) — tighter noise, the axis defines the archetype
- Seed **3–7** (moderate or neutral): sigma = `sigma.secondary` (default 2.5) — wider noise, the axis is open in this archetype

Both sigma values are stored in `live/archetypes.yaml` and can be adjusted there. Tightening primary sigma makes archetypes more "pure" — generated profiles cluster closer to the seed. Widening secondary sigma allows more variation on the axes an archetype doesn't strongly define.

The original skill had a hand-maintained "primary *" column per archetype. The auto-derivation rule replaces it: seed extremity IS the primary designation.

### Generation steps

1. For each non-conditional axis: `score = clamp(round(seed + N(0, sigma)), 0, 10)`
2. Conditional axes are generated in a second pass, AFTER non-conditional scores exist — so their activation conditions evaluate against the actual generated profile, not the seeds.
3. For each conditional axis: evaluate the activation condition string (parsed from `dimensions.yaml`). If activated, generate score using the same noise formula. If not activated, set score to `null`.

Conditional activation condition strings are evaluated by a simple clause parser that handles `AND`, `OR`, and the six comparison operators (`>=`, `<=`, `>`, `<`, `==`, `!=`). Adding a new conditional axis with its condition defined in `dimensions.yaml` requires no changes to the script.

---

## Scoring and matching

For each profile, every category in `categories.yaml` receives a match score (0–1). Categories are then ranked by score.

### Axis weight

Before computing contributions, each active axis is assigned a weight based on the **profile's** score on that axis — not the category's:

| Profile score | Weight | Rationale |
|---|---|---|
| <= 2 or >= 8 | 1.3 | Strong signal — this axis meaningfully defines the profile |
| 3 or 7 | 1.0 | Moderate signal |
| 4, 5, or 6 (neutral band) | 0.7 | Weak signal — don't over-index on axes where the profile has no preference |

The neutral band boundaries come from `dimensions.yaml` (`scoring.bipolar_neutral_band`).

### Bipolar axis contribution

```
contribution = 1 - |profile_score - category_score| / 10
```

Ranges from 1.0 (perfect alignment) to 0.0 (poles apart). Symmetric — a profile of 2 vs category of 8 is the same distance as a profile of 8 vs category of 2.

### Unipolar axis contribution (analyze, nurturing)

Unipolar axes have one meaningful pole. Low profile scores indicate absence of signal, not a negative preference — so a low-nurturing profile should not be penalised for matching a high-nurturing category.

```
if profile_score <= low_thresh (3):
    contribution = 1.0   # no signal, no penalty

else:
    profile_signal = (profile_score - low_thresh) / (10 - low_thresh)   # 0 to 1
    category_gap   = max(0, (low_thresh + 1) - category_score) / (low_thresh + 1)   # 0 to 1
    contribution   = max(0, 1 - profile_signal * category_gap)
```

In plain terms: if the profile scores HIGH on nurturing (>3), the penalty scales with how strongly the profile signals nurturing AND how far below the low threshold the category sits. A high-nurturing profile (score 9) matched against a low-nurturing category (score 1) gets close to zero contribution. A mid-nurturing profile (score 5) against a low-nurturing category gets a partial penalty.

`low_thresh` and `high_thresh` come from `dimensions.yaml` (`scoring.unipolar_threshold_low`, `scoring.unipolar_threshold_high`).

### Final match score

```
match_score = sum(weight_i * contribution_i) / sum(weight_i)
              for all active (non-null) axes
```

Normalised weighted average across active axes. Conditional axes excluded if not activated for this profile.

---

## Driving, neutral, opposing classification

For each top-5 category match, every active axis is classified:

- **Driving** — profile and category scores within 2 points of each other, AND neither is in the neutral band (4–6). The axis had something meaningful to align on and they aligned.
- **Opposing** — profile and category scores differ by 4 or more points. The axis actively pulled this category down.
- **Neutral** — everything else: small difference but both in neutral band, or mid-range difference that's neither strongly aligned nor strongly opposed.

The "both in neutral band" check is important: two scores of 5 are aligned but carry no signal — they should not count as driving.

---

## Weak axis detection

An axis is **weak for a given profile** if it failed to discriminate across the top-5 matched categories.

```
cat_scores = [category[axis] for category in top_5]
score_range = max(cat_scores) - min(cat_scores)

if score_range <= WEAK_RANGE_THRESHOLD (default 2):
    mark axis as weak
```

A range of 0–2 across the top 5 categories means all top-matching categories scored similarly on this axis — the axis had no discriminating power for this profile, regardless of how the profile itself scored.

### Structural vs neutral-profile weak

If the profile's score on the weak axis was itself in the neutral band (4–6), the axis may legitimately not discriminate — the profile had no preference, so it's unsurprising that top categories don't split on it. These are marked `neutral_profile: true` and excluded from the **structural weak %** column.

**Structural weak %** is the cleaner diagnostic signal: it measures how often an axis fails to discriminate even when the profile has a clear position on it. An axis with high structural weak % is the one to scrutinise — it may be scoring categories too uniformly, or it may be genuinely redundant given other axes.

---

## Diagnostic thresholds

These are policy constants defined at the top of `scripts/analytics.py`. Adjust as the dataset and category count grow.

| Constant | Default | Meaning |
|---|---|---|
| `WEAK_RANGE_THRESHOLD` | 2 | Top-5 category score range at or below this → axis weak for this profile |
| `CHOPPING_BLOCK_CUTOFF` | 0.40 | Structural weak % above this → "CHOPPING BLOCK" flag |
| `COVERAGE_GAP_CUTOFF` | 0.03 | Category appearing in fewer than this fraction of top-5 results → "COVERAGE GAP" flag |
| `DOMINANT_CATEGORY_CUTOFF` | 0.25 | Category appearing in more than this fraction of top-5 results → "DOMINANT" flag |
| `TIGHT_CLUSTER_MARGIN` | 0.05 | top1→top2 match margin below this → tightly clustered |
| `TIGHT_CLUSTER_TOP5_MARGIN` | 0.08 | top5→top6 margin below this (used alongside above for `tightly_clustered` flag) |
| `WELL_SPREAD_MARGIN` | 0.15 | top5→top6 margin above this → well spread |

**On the chopping block threshold:** 40% is calibrated for the current axis set. An axis that is structurally weak >40% of the time when active is probably not earning its session question budget. The threshold should be revisited if the category count grows significantly — more categories increase the chance any axis discriminates somewhere.

**On tightly clustered:** The current baseline from smoke testing is ~90% tightly clustered, which indicates the match scores are compressed into a narrow band. This is worth investigating — it may mean the scoring formula weights are too uniform, or that categories are not differentiated enough on the axes that matter.

---

## Log schema

```json
{
  "run_id": "<uuid-v4>",
  "batch_id": "<uuid-v4>",
  "timestamp": "<ISO8601 UTC>",
  "archetype": "<archetype_id>",
  "axis_scores": {
    "things_people": 3,
    "concrete_abstract": null
  },
  "conditional_axes": {
    "concrete_abstract": { "activated": false, "reason": "condition not met: analyze >= 6 OR master_create >= 7" },
    "animals_people":    { "activated": true,  "reason": "nurturing >= 7 OR things_people >= 7" }
  },
  "top_5": [
    {
      "rank": 1,
      "category_id": "clinical_medicine",
      "match_score": 0.8412,
      "driving_axes": ["nurturing", "things_people"],
      "neutral_axes": ["flexible_structured"],
      "opposing_axes": ["master_create"]
    }
  ],
  "match_margin": {
    "top1_to_top2": 0.031,
    "top5_to_top6": 0.009
  },
  "weak_axes": [
    { "axis": "indoors_outdoors", "neutral_profile": false, "range": 1 }
  ],
  "tightly_clustered": true
}
```

`batch_id` is shared across all records generated in the same `run` invocation. `axis_scores` stores `null` for conditional axes that were not activated. The log is append-only — never overwrite it.

---

## Archetype design principles

Archetypes are meant to model realistic person-types, not just axis-space extremes. A good archetype:

- Maps to 2–3 intuitively obvious career categories (verify with `--archetype <id>` after adding)
- Has at least 3–4 axes with seeds outside the neutral band (otherwise the archetype doesn't strongly define a profile type)
- Does not duplicate an existing archetype — if seeds are nearly identical, the new archetype adds noise without new coverage

Archetype seeds for **conditional axes** should be set consistently with the activation condition. For example, if `concrete_abstract` only activates when `analyze >= 6 OR master_create >= 7`, an archetype with `analyze: 3` and `master_create: 4` will almost never activate `concrete_abstract` — so its seed value is irrelevant in practice. Set it to 5 (neutral) to signal intent.

When adding a new axis to `dimensions.yaml`:
1. Add a seed to every archetype in `live/archetypes.yaml`
2. For archetypes where the new axis is not conceptually defining, use a neutral seed (5)
3. For archetypes where the new axis matters, choose a seed that reflects the archetype's persona
4. Run `python scripts/analytics.py run 100` and verify per-archetype top categories still look right

---

## Maintenance contract

| Change | Files to update | Validation |
|---|---|---|
| Add an axis | `dimensions.yaml`, `categories.yaml`, `archetypes.yaml` (seed per archetype) | `validate_yaml.py dimensions`, `validate_yaml.py categories`, `validate_yaml.py archetypes` |
| Add a category | `categories.yaml` | `validate_yaml.py categories` |
| Add an archetype | `archetypes.yaml` | `validate_yaml.py archetypes` |
| Change a scoring threshold or constant | `scripts/analytics.py` | Run `analytics.py run 100` and compare report |
| Change the scoring formula | `scripts/analytics.py` AND `live/career-assessment.md` | Both must stay in sync — analytics results are only meaningful if the script matches the live session logic |
