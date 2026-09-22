# Career Assessment — Find Fresh Axis

## Trigger

This skill runs when the opening message is `career-assessment-find-fresh-axis`, optionally followed by flags or notes.

No other phrasing triggers this skill.

---

## Purpose

The existing axes may not fully differentiate all category pairs. Two categories can score similarly across all current axes while being meaningfully distinct in ways the model does not yet capture. This skill surfaces those pairs systematically and proposes a targeted fix — either correcting a dimension misalignment or introducing a new axis.

---

## Pre-flight (optional)

Run `python scripts/analytics.py review` before beginning the analysis. The category coverage table shows which categories surface rarely in top-5 results across synthetic profiles, and the weak-axis report shows which axes discriminate least. Low-coverage category pairs and weak axes are both useful signals for identifying where a new axis would add the most value. Skip this step if the log is empty or stale.

---

## Behaviour on Invocation

### Step 1 — Load source files

Read `live/dimensions.yaml` and `live/categories.yaml` in full before doing any analysis. All axis IDs, types, score ranges, and activation conditions used in subsequent steps must come from these files — do not rely on memorised names or a hardcoded list.

---

### Step 2 — Find the closest category pair

Compute pairwise similarity across all categories using the following method:

**Similarity score = sum of |axis_a_score − axis_b_score| across all shared axes**

Lower total = more similar = higher priority for analysis.

Select the **single pair with the lowest total distance**. If there is a tie, prefer the pair where the two categories are most conceptually distinct (i.e. a tie between superficially similar categories is less interesting than a tie between categories that feel like they should be easy to separate).

Do not analyse more than one pair per run.

**State your working.** Output a brief table showing the top 3–5 closest pairs and their distances, so the facilitator can see why this pair was chosen. Then proceed with the selected pair.

---

### Step 3 — Prong 1: Misalignment Check

For each category in the selected pair, review every axis score and ask: *does this score accurately reflect what someone working in this field actually experiences?*

Focus particularly on axes where the two categories score similarly but probably shouldn't — these are the most likely candidates for a misalignment that is artificially inflating closeness.

**Output format:**

> **Misalignment check: [Category A] vs [Category B]**
>
> For each axis where you suspect a misalignment, state:
> - Which category, which axis, current score
> - What score you think it should be and why
> - Whether fixing this misalignment alone would meaningfully separate the pair (i.e. would the fix solve the problem without a new axis)

If no misalignments are found, say so clearly. Do not invent problems.

**Do not write to `live/categories.yaml`.** Present the proposed fix as a clearly formatted proposed change, waiting for approval.

---

### Pause — Facilitator Review

After completing the Prong 1 output, **always stop and wait for facilitator feedback** before proceeding to Prong 2.

Ask explicitly:

> "That's the misalignment check done. Want me to proceed to Prong 2 (missing axis proposal), or would you like to adjust any scores first?"

Do not proceed until the facilitator responds. Their response may:
- Confirm to proceed to Prong 2 as-is
- Request a score change before proceeding — in which case, apply the change in discussion and then ask again whether to proceed
- Conclude the session without Prong 2 (e.g. if the misalignment fix is sufficient)

---

### Step 4 — Prong 2: Missing Axis Proposal

Identify whether there is a genuine dimension — a real, probaeable human preference or working-environment characteristic — that would separate this pair but is not captured by any existing axis.

Before proposing a new axis, check the following:

- [ ] Is this genuinely distinct from all existing axes in `live/dimensions.yaml`? (Name the closest existing axis and explain why this is different.)
- [ ] Can a young person meaningfully self-assess this preference via a Would You Rather question?
- [ ] Is it a preference or a trait — not a skill, value, or personality type?
- [ ] Does it separate at least this pair cleanly, and likely others too?
- [ ] Is the low pole a neutral absence of signal, or a genuine opposite preference? (Determines unipolar vs. bipolar)

If no genuine axis gap exists, say so. Do not manufacture an axis to fill space.

**Output format (if a new axis is proposed):**

> **Proposed axis: [Name]**
>
> - **Type:** bipolar / unipolar / conditional [bipolar|unipolar]
> - **Low pole:** [Label] — [One sentence description]
> - **High pole:** [Label] — [One sentence description]
> - **Why it's distinct from existing axes:** [Paragraph — name the closest existing axis and explain the difference]
> - **Why it separates this pair:** [Concrete explanation — what score would each category receive and why]
> - **Likely secondary benefit:** [Other pairs or categories this axis would also help differentiate]
> - **Conditionality:** [State whether this should be conditional and why, or why not]
> - **Draft notes field:** [Any nuance about interpretation, scoring, or interaction with existing axes]
> - **Illustrative question pair:** [One Would You Rather scenario that cleanly probes this axis without bleeding into existing axes]

**Do not write to `live/dimensions.yaml`.** This is a proposal for discussion only.

---

### Step 5 — Close

After both prongs, summarise:

1. Whether the pair's closeness is likely a misalignment problem, an axis gap problem, or both
2. Recommended next step — fix the misalignment, add the axis, or do both
3. If the facilitator wants to proceed with adding an axis, refer them to `docs/axis-addition-workflow.md` for the full addition process.

---

## What This Skill Does Not Do

- Does not write to any file
- Does not run the full axis addition workflow — refer to `docs/axis-addition-workflow.md` for that
- Does not analyse more than one pair per session
- Does not propose more than one new axis per session

---

## Session Statefulness

Each invocation picks the closest pair fresh from the current state of `live/categories.yaml` and `live/dimensions.yaml`. If an axis was added in a previous session, the distances will have changed and a different pair should naturally emerge. No session history is tracked — the files themselves are the state.
