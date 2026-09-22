# Find Fresh Axis — Internals

How the `career-assessment-find-fresh-axis` skill works — execution flow, internal logic, design decisions, and how to interpret its output. Read before modifying the skill or extending its behaviour.

---

## What It Does

The skill identifies the category pair that is hardest to distinguish under the current axis set — the pair with the smallest total score distance — and investigates why. It may find that one or both categories has a misaligned axis score (Prong 1), that the axis space is genuinely missing a dimension that would separate them (Prong 2), or both.

This is a reasoning skill: there is no script or algorithm backing it. All analysis is performed by Claude reading the live YAML files and reasoning over the category space. The output is a proposal for discussion only — no files are modified without facilitator approval.

---

## Execution Flow

```
(Optional) Pre-flight: analytics review for context
    ↓
Load source files
    ↓
Compute pairwise L1 distances across all categories
    ↓
Select the closest pair; output top 3–5 with distances
    ↓
Prong 1: misalignment check — review scores for the selected pair
    ↓
Pause: wait for facilitator to confirm or redirect before Prong 2
    ↓
Prong 2: assess whether a new axis would separate the pair
    ↓
Close: summary + recommended next step + pointer to axis-addition-workflow.md
```

The pause between Prong 1 and Prong 2 is load-bearing. Prong 2 is only reached if the facilitator decides the misalignment check alone is insufficient.

---

## The Closest-Pair Algorithm

The similarity metric is L1 distance summed across all axes:

```
distance(A, B) = sum of |A[axis] − B[axis]| for every axis in live/dimensions.yaml
```

Lower distance = more similar = higher priority for investigation. All axis IDs and scores are read fresh from `live/categories.yaml` and `live/dimensions.yaml` on each run — no hardcoded lists.

**Tie-breaking:** when two or more pairs share the same minimum distance, prefer the pair that is most conceptually distinct. A tie between two very similar sub-fields is less interesting than a tie between fields that feel like they should be easy to separate — the latter suggests a genuine gap in the axis model.

**Why L1 and not L2:** L1 is more interpretable here. The distance is a sum of per-axis score differences, so the contribution of each axis is visible and auditable. L2 would weight large single-axis gaps disproportionately, which doesn't reflect how the matching algorithm actually uses scores.

---

## Prong 1: Misalignment Check

Before looking for a new axis, the skill checks whether the closeness is an artefact — a score that doesn't accurately reflect the field it represents. Two categories can be scored too similarly if:

- A score was assigned conservatively (e.g. neutral 5) when the field clearly leans one way
- A score was carried over from an earlier version of the axis definition that has since been refined
- A category was scored before a related axis existed and was never revisited

The misalignment check is the more conservative diagnosis. A score correction is lower-cost than a new axis — it requires only editing `live/categories.yaml` rather than touching `live/dimensions.yaml`, `live/career-assessment.md`, `live/archetypes.yaml`, and all categories.

**Output:** for each suspected misalignment, the skill states the current score, the proposed correction, and whether the fix alone would meaningfully separate the pair. The facilitator decides whether to accept the correction before Prong 2 is attempted.

If no misalignments are found, the skill says so and proceeds to Prong 2 after the pause.

---

## The Facilitator Pause

After Prong 1, the skill always stops and asks explicitly whether to continue to Prong 2.

**Why it exists:** Prong 2 is a heavier analysis — and a proposed new axis is a significant change to the model. If the misalignment check surfaces a correction that would clearly separate the pair, Prong 2 is unnecessary. The pause lets the facilitator redirect, accept a score fix and close, or confirm that the axis gap investigation is still needed.

**Typical outcomes of the pause:**

- *"Yes, proceed to Prong 2"* — the score fix doesn't fully explain the closeness
- *"Apply the score change and recheck before Prong 2"* — facilitator wants to see whether the corrected distance still warrants a new axis
- *"The fix is enough, let's stop here"* — the session closes after Prong 1

---

## Prong 2: Missing Axis Proposal

If the closeness persists after misalignment review, the skill looks for a genuine dimension — a probaeable human preference or working-environment characteristic — that would separate the pair and is not captured by any existing axis.

### The checklist

Before proposing an axis, five conditions must hold:

1. **Genuinely distinct from all existing axes** — the closest existing axis is named and the difference explained. Variations on an existing axis (e.g. a finer-grained version of `things_people`) do not pass.
2. **Self-assessable by a young person** — the preference must be accessible to someone who has not yet worked. Abstract trait dimensions that require career experience to evaluate are excluded.
3. **Preference or trait, not skill, value, or personality type** — the assessment probes what kind of work a person would enjoy, not what they are good at or what they believe.
4. **Separates more than just this pair** — an axis that only separates the target pair and nothing else has low model value. The proposal should name other pairs or regions it would also clarify.
5. **Low pole determination** — whether the low pole is a genuine opposing preference (bipolar) or simply absence of signal (unipolar). This determines axis type and affects how scores are interpreted in matching.

If no axis satisfies all five, the skill says so. It does not propose an axis to fill space.

### Conditionality

If the proposed axis only adds discrimination value for a subset of profiles — i.e. it is noise for profiles that don't meet certain upstream conditions — the skill proposes it as a conditional axis and states the activation condition. Conditional axes are scored in `live/categories.yaml` like any other axis; the activation condition only controls whether the axis is probed during a session.

---

## Relationship to Other Skills

| Skill | What it does | When to use instead |
|---|---|---|
| `career-assessment-find-fresh-axis` | Finds the closest category pair; proposes score corrections or new axes | When two categories feel hard to distinguish |
| `career-assessment-find-fresh-category` | Identifies axis-space gaps; proposes new categories | When the taxonomy feels incomplete for a type of person |
| `career-assessment-analytics` | Batch scoring; category coverage and weak-axis diagnostics | When you want quantitative signal about what the taxonomy is doing |

The pre-flight analytics step (`python scripts/analytics.py review`) is optional but useful: the category coverage table shows low-coverage categories that may be close to a dominant neighbour, and the weak-axis report shows axes that contribute little discrimination — both are useful context for selecting which pair to investigate next if the computed closest pair has already been addressed.

**Recommended sequencing:** if analytics flags two categories with similar coverage patterns and neither surfaces clearly in top-5 results, they are good candidates for the closest-pair investigation even if they are not technically the computed minimum. Use the distance table to confirm.

---

## After Approval

If the facilitator approves a score correction from Prong 1, that is executed directly in `live/categories.yaml`. Run `python scripts/validate_yaml.py categories` after editing.

If the facilitator approves a new axis from Prong 2, the full addition is executed via `docs/axis-addition-workflow.md`. That workflow covers all files that need updating (`live/dimensions.yaml`, `live/categories.yaml`, `live/career-assessment.md`, `live/archetypes.yaml`) and the validation test sessions required before the axis is considered stable. The skill itself does not write to any file.
