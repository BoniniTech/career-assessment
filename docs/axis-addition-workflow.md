# Axis Addition Workflow

Follow all steps in order. Do not skip steps or defer them — incomplete axis additions create silent inconsistencies between `dimensions.yaml`, `categories.yaml`, and the skill files.

---

## Axis Types

| Type | Description | Scoring behaviour |
|---|---|---|
| **Bipolar** | Two opposing poles with a meaningful midpoint | Low = one preference, High = opposite preference, 4–6 = neutral |
| **Unipolar** | One meaningful pole; the other end is simply low signal | High = strong signal, Low = absence of signal (not a negative trait) |
| **Conditional** | Only activated and probed when upstream signal meets a defined threshold | Skipped entirely for profiles where it would produce noise |

Conditional axes are always either bipolar or unipolar in their own right — "conditional" describes when they are activated, not how they are scored.

---

## Step 1 — Define the Axis

Before touching any files, write out the full axis definition and answer every question below.

**Required fields**
- **ID** — snake_case, unique, descriptive (e.g. `animals_people`, `solo_group`)
- **Number** — next available integer in `dimensions.yaml`
- **Name** — short display name, use ↔ for bipolar axes (e.g. `People ↔ Animals`)
- **Type** — bipolar / unipolar / conditional bipolar / conditional unipolar
- **Score range** — always `[0, 10]`
- **Low pole label and description** — what a score near 0 means
- **High pole label and description** — what a score near 10 means
- **Notes** — any nuance about interpretation, interaction with other axes, or common misreadings

**Additional fields for conditional axes**
- **Activation condition** — the exact upstream signal required to activate this axis. Be precise — this condition is enforced in the adaptive logic.
- **Rationale for conditionality** — why probing this axis is noise for profiles that don't meet the condition

**Checklist before proceeding**
- [ ] Does this axis capture something genuinely distinct from all existing axes?
- [ ] Can a person meaningfully self-assess this preference?
- [ ] Is the low pole a neutral absence of signal, or a genuine opposite preference? (Determines unipolar vs. bipolar)
- [ ] If conditional: is the activation condition tight enough to skip it for profiles where it's noise, but broad enough not to miss profiles where it matters?
- [ ] Are there at least 3–4 scenario pairs that cleanly probe this axis without bleeding into existing axes?

Do not proceed to Step 2 until all checklist items are confirmed.

---

## Step 2 — Add to `dimensions.yaml`

Add the new axis entry following the existing format exactly. Place it after the last current axis entry, before the `scoring:` block.

```yaml
  - id: [axis_id]
    number: [next integer]
    name: "[Display Name]"
    type: [bipolar|unipolar]
    score_range: [0, 10]
    low_pole:
      label: "[Short label]"
      description: "[One sentence]"
    high_pole:
      label: "[Short label]"
      description: "[One sentence]"
    notes: >
      [Nuance, interactions, common misreadings. For conditional axes, state
      the activation condition here.]
```

For conditional axes, also add an `activation:` block:

```yaml
    activation:
      condition: "[axis_id] [operator] [threshold] [AND|OR] [axis_id] [operator] [threshold]"
      rationale: "[One sentence explaining why this axis is noise for non-activating profiles]"
```

**Validate:** confirm the new entry is well-formed YAML with no indentation errors before continuing.

---

## Step 3 — Re-score all categories in `categories.yaml`

Every category must receive a score for the new axis. Do not leave any category without a score — missing scores cause silent matching errors.

**Scoring guidance**
- Work through all categories systematically — do not skip categories that seem irrelevant
- For bipolar axes: assign 5 (neutral) only when the category genuinely sits at the midpoint. Do not use 5 as a default when uncertain — reason through each category.
- For unipolar axes: assign scores based on how central the axis trait is to the category. A score of 0–2 means the trait is genuinely absent or irrelevant; 8–10 means it is central.
- For conditional axes: score all categories as normal — the activation condition controls whether the axis is *probed*, not whether it *applies* to categories.

**Format (add to each category's `axes:` block)**
```yaml
      [axis_id]: [score]
```

**Validate:** confirm every category has the new axis scored before continuing.

---

## Step 4 — Update the career-assessment skill

Four sections of `live/career-assessment.md` require updates when a new axis is added:

**4a — Axis priority sequence**
Insert the new axis into the suggested opening sequence at the appropriate position. Consider:
- High-discrimination axes should appear earlier
- Conditional axes should appear after the axes that trigger their activation condition
- Add a note if the axis is conditional: *"Only probe if [condition] — skip otherwise"*

**4b — Question budget and rules**
If the new axis requires any special budget rules, early-exit conditions, or interaction rules with existing axes, add them to the Adaptive Logic section. For conditional axes, state explicitly what happens when the axis is not activated.

**4c — Example questions**
Add one illustrative example question for the new axis, clearly labelled as illustrative only. For conditional axes, note the activation condition in the example header.

**4d — Auto-debrief table**
Add a new row to the axis scores table in the auto-debrief block.

---

## Step 5 — Update design decisions and open a tracking issue

**5a — Design Decisions**
If the new axis required a non-obvious typing decision (bipolar vs. unipolar, conditional vs. unconditional), add an entry to `docs/design-decisions.md` explaining the reasoning and what problem it solves that existing axes could not.

**5b — GitHub Issue**
Open a `type: qa` issue noting that the new axis is unvalidated and what to watch for in early test sessions.

---

## Step 6 — Run validation test sessions

Run a minimum of 2 test sessions specifically designed to stress-test the new axis.

**Session A — Activation path (for conditional axes) / High-signal path (for unconditional)**
Design a profile that meets the activation condition (conditional) or naturally scores high on the axis (unconditional). Confirm:
- The axis activates correctly (conditional) or resolves with clear signal (unconditional)
- At least 1 question is asked on the new axis
- The axis score visibly affects the top 5 output in a way that makes sense

**Session B — Non-activation path (conditional) / Low-signal path (unconditional)**
Design a profile that does not meet the activation condition (conditional) or naturally scores low (unconditional). Confirm:
- The axis is skipped entirely (conditional) or resolved quickly with low signal (unconditional)
- The top 5 output is not affected in a way that seems wrong
- No question budget is wasted

**Session C — Edge case**
Design a profile near the activation threshold (conditional) or near the bipolar midpoint (bipolar). Confirm that the ambiguous case is handled gracefully.

**Debrief review checklist**
After each session:
- [ ] The new axis score and confidence are reported correctly in the auto-debrief
- [ ] The axis did or did not visibly affect the top 5 as expected
- [ ] No unexpected bleed between the new axis and existing axes
- [ ] Question framing was clean — no observed conflation with other axes

If any checklist item fails, return to Step 1 and revise before continuing.

---

## Step 7 — File a GitHub Issue (if applicable)

If test sessions surface any ambiguity, question design problems, or unexpected interactions, open a `type: qa` issue in GitHub.

---

## Summary Checklist

| Step | Action | Done |
|---|---|---|
| 1 | Full axis definition written and checklist confirmed | [ ] |
| 2 | Entry added to `dimensions.yaml` and validated | [ ] |
| 3 | All categories re-scored in `categories.yaml` | [ ] |
| 4a | Axis priority sequence updated in career-assessment skill | [ ] |
| 4b | Budget and special rules updated (if needed) | [ ] |
| 4c | Example question added | [ ] |
| 4d | Auto-debrief table row added | [ ] |
| 5a | Design Decisions entry added (if non-obvious typing decision) | [ ] |
| 5b | GitHub Issue opened for unvalidated axis | [ ] |
| 6 | 2–3 validation test sessions run and debriefs reviewed | [ ] |
| 7 | GitHub Issue filed if problems found | [ ] |
