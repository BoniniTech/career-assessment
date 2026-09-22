# Find Fresh Category — Internals

How the `career-assessment-find-fresh-category` skill works — execution flow, internal logic, design decisions, and how to interpret its output. Read before modifying the skill or extending its behaviour.

---

## What It Does

The skill analyses the existing category taxonomy to find regions of the axis space that are underserved — axis score combinations that plausibly correspond to a real career field but are not represented in `live/categories.yaml`. It proposes one new category per run to fill the most compelling gap, with an optional second category if a real-world omission is independently obvious.

This is a reasoning skill: there is no script or algorithm backing it. All analysis is performed by Claude reading the live YAML files and reasoning over the axis space. The output is a proposal for discussion only — no files are modified without facilitator approval.

---

## Execution Flow

```
Load source files
    ↓
Classify axes (primary vs. secondary) from dimensions.yaml
    ↓
Map coverage across existing categories
    ↓
Checkpoint: present gap map, wait for facilitator direction
    ↓
Develop confirmed gap into a full category proposal
    ↓
(Optional) Surface a real-world obvious gap
    ↓
Close: sparse regions + pointer to category-addition-workflow.md
```

The checkpoint is load-bearing — the skill does not write a full proposal until the facilitator has confirmed which gap to pursue. This keeps the session interactive and prevents wasted effort on the wrong region.

---

## Axis Classification

Axes are classified directly from `live/dimensions.yaml` on each run. No hardcoded axis lists.

| Class | Rule | Role in gap analysis |
|---|---|---|
| **Primary** | No `activation:` field present | Always active; define the main coverage map |
| **Secondary** | `activation:` field present | Conditional; only activate for a subset of profiles — not useful for top-level gap mapping |

Primary axes form the coordinate space for the gap map. Secondary axes are noted after the fact — once a gap region is identified using primary axes, secondary axes may further define what the proposed category looks like on those dimensions.

This classification is stable as long as `dimensions.yaml` is the source of truth. If an axis is made conditional or unconditional, its classification here updates automatically — the skill re-derives it from the file each run.

---

## Gap Analysis

The axis space is conceptually N-dimensional, where N = number of primary axes. The skill partitions this space heuristically, not exhaustively — it is looking for meaningful real-world gaps, not geometric holes.

### What counts as a meaningful gap

A region is worth developing into a proposal if it satisfies all three:

1. **At least 2 primary axes point into it** — single-axis extremes are already served by existing categories. A genuine gap occupies a distinct position on multiple dimensions simultaneously.
2. **No existing category is close** — assessed informally during gap mapping, then verified precisely with L1 distance during proposal development.
3. **The profile corresponds to a real field** — an empty coordinate is only interesting if real people work there.

### How gap size is assessed

During the gap map (checkpoint output), coverage is assessed qualitatively by scanning the axis scores of all categories in `live/categories.yaml`. The skill is looking for score regions that no category occupies or that only one category thinly covers.

After the gap is confirmed, the nearest existing category is computed with a precise L1 distance:

```
L1 = sum of |proposed_score − existing_score| across all axes
```

This is the same metric used in `career-assessment-find-fresh-axis` for category-pair closeness. A higher L1 = more distinct from the nearest neighbour. What counts as "distinct enough" depends on which axes drive the distance — two categories can have a large L1 but still feel redundant if the distance is spread across axes that don't affect matching, or a moderate L1 but be clearly distinct if the distance is concentrated on a dominant axis like `things_people` or `nurturing`.

---

## The Facilitator Checkpoint

The skill always pauses between the gap map and the full proposal. This is intentional.

**Why it exists:** A full category proposal is detailed work — axis scores, description, role hint, nearest-neighbour analysis. Writing that for the wrong gap wastes session time and produces output the facilitator won't use. The checkpoint lets the facilitator redirect to a different gap, suggest modifications to the framing, or decide the current taxonomy is sufficient and close the session early.

**What a good checkpoint response looks like:**

> "Here's the gap landscape as I see it:
> - High `analyze`, low `nurturing`, high `inform_express` — well covered by physical_sciences and mathematics_statistics; no gap here.
> - High `master_create`, high `nurturing`, low `things_people` — biomedical_engineering comes closest but is engineer-not-carer. A craft-meets-care field feels absent.
> - High `indoors_outdoors`, high `nurturing`, low `analyze` — outdoor_adventure_services covers this partially but not the animal-welfare angle.
>
> Which of these should I develop? Or I can take the second one."

The facilitator can say "second one" or redirect entirely. The proposal is only written after that response.

---

## The Optional Secondary Suggestion

The skill may surface a second category in Step 4, but only if a real-world field meets a high bar independently of the gap analysis: if a young person said "I want to do X" and the assessment gave them no useful match, that would be a failure.

This section is present in fewer than half of sessions. The right signal is a strong intuition about a known, legitimate career field that is genuinely absent — not a borderline case, not a sub-field of something already covered. If the secondary suggestion doesn't feel obviously necessary, the section is omitted without comment.

---

## Relationship to Other Skills

| Skill | What it does | When to use instead |
|---|---|---|
| `career-assessment-find-fresh-category` | Identifies axis-space gaps; proposes new categories | When the taxonomy feels incomplete for a type of person |
| `career-assessment-find-fresh-axis` | Finds the closest category pair; proposes new axes or score corrections | When two categories feel too similar and hard to distinguish |
| `career-assessment-analytics` | Batch scoring; category coverage and weak-axis diagnostics | When you want quantitative signal about what the taxonomy is doing |

These skills are complementary. `analytics` can flag low-coverage categories (a possible sign of a misplaced gap), `find-fresh-axis` can flag category pairs that are too close (a possible sign of redundancy or missing discrimination), and `find-fresh-category` can fill the gaps that emerge from both signals.

**Recommended sequencing:** run `analytics review` before `find-fresh-category` to have quantitative coverage data in hand. If analytics flags a category with very low coverage, that can inform which region of the axis space to target.

---

## What Makes a Good Proposal

Strong proposals share these characteristics:

- **Coherent field** — the category maps to something a young person would recognise as a real job family, not a theoretical axis construct
- **Distinct from nearest neighbour** — the L1 distance is substantial AND the differentiating axes are ones that matter to matching (dominant axes like `things_people` and `nurturing` carry more weight than weak axes like `indoors_outdoors`)
- **Internally consistent scores** — the axis scores tell a coherent story about the kind of person who does this work; no scores contradict the description
- **Role hint is concrete** — job titles are recognisable and specific enough that a young person could google them

Weak proposals tend to:
- Describe a sub-field of an existing category rather than a genuinely new one
- Have a large L1 distance driven mostly by axes in the neutral band
- Require the facilitator to squint to see how it's different from the nearest neighbour

---

## After Approval

Once the facilitator approves a proposal, the addition is executed via `docs/category-addition-workflow.md`. The skill itself does not write to any file.
