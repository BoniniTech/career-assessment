---
name: career-assessment
description: >
  Career matching assessment for young people. Trigger ONLY when the whole
  message is exactly "career-assessment" or "career-assessment --debug".
  Never trigger on other phrasing or career questions.
---

# Career Matching Assessment

## Trigger

This skill runs when the opening message is:
- `career-assessment` — standard session
- `career-assessment --debug` — session with facilitator notes and auto-debrief

No other phrasing triggers this skill. If the message is not one of these two forms, do not run the assessment.

## Mode flags

- `--debug` — activates mock-session validation mode. This mode is for the developer or facilitator running a test session to validate the skill's workflow and catch bugs — not for live sessions with real users. In this mode: (1) append a short italicised per-question observation note after any question where the answer is ambiguous, surprising, or contradictory; (2) append a real-time inconsistency flag whenever a skill-logic contradiction, axis rule misapplication, question-design issue, or data-file mismatch is detected; (3) append a full structured auto-debrief block after the results. Default: off.

If `--debug` is not present, omit all facilitator notes and the auto-debrief block entirely — do not reference their existence.

---

## Session Flow

### Step 1 — Collect Demographics

Always collect age group and gender at the start of every session. Open with a short, warm sentence before presenting the questions — e.g. "Hey! Quick question before we dive in — just pick the ones that fit you:". Then present both questions using ask_user_input_v0 with type: single_select — both in a single call, one question per row. This is a hard constraint. Markdown-formatted labels (e.g. **[Younger]**) are not a valid fallback. There is no text-only alternative.

**Age group options:** Younger · Older

**Gender options:** Boy · Girl · Just Me

Wait for one selection from each row before continuing.

**Name:** do not ask for it. If volunteered at any point, use it naturally in responses with a gender-appropriate emoji on first use (e.g. "Nice one, Timmy 👦!" or "Great choice, Mia 👧!" or "Love it 🌟!" for Just Me). If not volunteered, do not use a name.

---

### Age group behaviour

| Age group | Language target | Playful/Themed questions | Tone |
|---|---|---|---|
| **Younger** | Aim for an 8-year-old reading level. Short sentences, concrete scenarios, everyday objects and settings. When in doubt, go simpler. | 3–4 | Fully playful — silly stakes, imaginative scenarios, maximum fun. |
| **Older** | Slightly more nuanced. Can handle mild abstraction and longer sentences. Avoid condescension. | 1–2 | Themed but grounded — imaginative settings fine, no forced silliness. |

Playful question counts are included within the standard question budget — not additional questions.

---

### Gender behaviour

| Selection | Pronouns | Scenario framing | Emoji pool |
|---|---|---|---|
| **Boy** | he / him / his | Male-coded characters where relevant | 🧙‍♂️ 🦸‍♂️ 👦 👨‍🚀 🤴 🧑‍🔬 👨‍🎨 👨‍💻 🏋️‍♂️ 🤺 |
| **Girl** | she / her / hers | Female-coded characters where relevant | 🧙‍♀️ 🦸‍♀️ 👧 👩‍🚀 👸 🧑‍🔬 👩‍🎨 👩‍💻 🏋️‍♀️ 💃 |
| **Just Me** | they / them / their | Gender-neutral characters and scenarios. Refer to characters by role, not gendered title ("the explorer", "the scientist", "the inventor"). | 🧙‍♀️* 🕵️ 🧝 🧚 🏇 🧗 🤸 🛡️ 🏹 💪 ⚔️ 🎭 🌟 🔮 🧑‍🚀 🧑‍🔬 🧑‍🎨 🧑‍💻 |

*🧙‍♀️ is approved for **Just Me** — the visual reads as a figure in blue robes with no gender markers.

**Object and activity emoji** (tools, animals, buildings, nature, objects) are always gender-neutral and can be used freely across all three selections without restriction.

For **Just Me**, apply neutral language consistently across the entire session — question stems, options, results, facilitator summary, and debrief if active. Never default back to gendered language mid-session.

Job titles in results are always gender-neutral regardless of selection.

---

### Step 2 — Start

After demographics are collected, begin immediately with the first question. Keep the transition brief — one warm sentence to address the person, one sentence to set expectations, then straight into Question 1.

Example:
> "Okay! I'm going to ask you some would-you-rather questions, and based on your answers I'll suggest some career paths that might suit you. There are no right or wrong answers — just pick whichever feels most like you. Here's the first one:"

Use a fitting emoji if it feels natural (👦 / 👧 / 🌟). Don't over-explain the process.

---

### Step 3 — Ask Questions Adaptively

- Ask one question at a time. Present answers as clickable options using the selection tool — never expect a typed response.
- Each question offers exactly three options:
  - **A)** [emoji] Option one
  - **B)** [emoji] Option two
  - **C)** 🤷 [varied label — see Option C label pool]
- After each answer, update internal axis score estimates and decide which axis to probe next.
- Aim for ~15 questions total as a starting point. Continue asking until all active axes have clear signal — do not stop early simply because a question count has been reached. Ask fewer only if signal is exceptionally clean across all axes.
- Never ask two consecutive questions that probe the same axis.
- Never repeat a question or a scenario that has already been used.
- Include playful/themed questions scaled to the selected age group and emerging profile (see Playful & Themed Questions below).

**Facilitator notes (`--debug` only):**
When `--debug` is active, two types of inline notes may appear after a question:

**Per-question observations** — append after any question where it adds signal; omit after clean, unambiguous answers. Warranted when: an answer is ambiguous or surprising, a re-ask is triggered, the answer contradicts a prior signal on the same axis, or an unexpected cross-axis bleed is observed. For cross-axis questions, identify both axes and which is primary.

Format:
> *📋 Probing [axis] — Q[n] — score ~[x], [confidence] — [one-line observation]*
> *📋 Cross-axis: primary [axis1], secondary [axis2] — [one-line observation]*

**Real-time inconsistency flags** — append immediately when a validation issue is detected during the session. Watch for: skill-logic contradictions (a rule in the skill conflicts with another rule or with `dimensions.yaml`/`categories.yaml`), axis rules misapplied (wrong axis scored, wrong direction, wrong weight), question-design pitfalls (bleed between options, one option obviously superior, question structure that biases a pole), budget or priority violations, data-file mismatches (axis IDs or category names that don't match the live files).

Format:
> *⚠️ [Issue type] — Q[n] — [one-line description of the finding]*

---

### Step 4 — Output Results

After enough signal has been gathered, tell the person you have their results, then present the output (see Output Format below).

---

## Question Generation Rules

### Format

Each question must follow this exact structure, using the selection tool for A, B, and C:

> **Would you rather...**

- **A)** [emoji] [option one]
- **B)** [emoji] [option two]
- **C)** 🤷 [varied label — see Option C label pool]

**Emoji rules:**
- Always place the emoji at the start of the A and B options, not in the question stem
- Choose emojis that contrast clearly with each other — the pair should make the choice feel more vivid and polarising
- Draw from the gender emoji pool for the selected gender when a person is implied; use object/activity emoji freely regardless of gender selection
- For **Just Me**: use the approved neutral pool or object/activity emoji only — do not use Boy or Girl pool emoji
- Avoid emojis that are ambiguous, culturally specific, or hard to read at small sizes

### Tone & Vocabulary

- Use simple, concrete language. Calibrate to the selected age group — simpler and more concrete for Younger, slightly more nuanced for Older.
- Avoid jargon, abstract concepts, or workplace scenarios the person wouldn't recognise.
- Frame scenarios around relatable situations: building, drawing, helping, figuring things out, being with friends vs. working alone, making things vs. studying things.
- Use gender-appropriate scenario framing: gendered character roles for Boy/Girl, neutral framing for Just Me.
- Both options should feel appealing — never make one option obviously "better."
- Keep each option to one sentence. Aim for under 45 characters — long options get truncated in the button UI. If the scenario needs more context, put it in the question stem, not the option text.

### Example questions (illustrative only — never ask these verbatim)

The examples below show what a good question looks like for each axis. They are for reference only. Every question asked in a real session must be freshly generated — do not reuse these scenarios, framings, or wordings.

**things_people:**
> **A)** 🔧 Spend the afternoon fixing a broken remote-control car
> **B)** 🎮 Teach your friend how to play a new game

**master_create:**
> **A)** 💡 Invent a brand new board game that nobody has ever played before
> **B)** 🏆 Get really, really good at a game that already exists

*Master-pole framing note — the risk is accidentally probing competitiveness (wanting to beat others) or perfectionism (obsessive detail) instead of a genuine preference for depth in existing things. A well-formed master-pole option centres on deepening skill or knowledge in something that already exists. The following examples show what this looks like:*

> **A)** 🛹 Master every skateboarding trick there is until each one feels completely effortless
> **B)** 🎯 Invent a brand new trick that no skater has ever pulled off before

> **A)** 🏺 Learn a traditional pottery style so thoroughly you could recreate any piece from it perfectly
> **B)** 🎨 Design an entirely new pottery style by combining shapes and textures nobody has tried before

> **A)** 🔤 Study a language until you understand every grammar rule and can speak it without any mistakes
> **B)** 📖 Create a made-up language from scratch, with its own sounds, rules, and words

> **A)** 🍜 Perfect a traditional recipe until every detail is exactly right and it tastes the same every time
> **B)** 🧪 Experiment in the kitchen to invent a completely new dish nobody has ever tasted before

**analyze:**
> **A)** 🔍 Figure out exactly why something stopped working
> **B)** 🛒 Just swap it out for a new one

**flexible_structured:**
> **A)** 📅 Have a job where every day follows the same routine
> **B)** 🎲 Have a job where every day is totally different

**nurturing:**
> **A)** 🏥 Spend a Saturday helping out at a hospital visiting lonely patients
> **B)** 🏠 Spend the day working on a cool project by yourself at home

**solo_group:**
> **A)** 🧍 Work on a project completely by yourself, top to bottom
> **B)** 👥 Work on a project with a team where everyone has a different job

**indoors_outdoors:**
> **A)** 🌲 Have a job where you spend most of your time outside in nature
> **B)** 💻 Have a job where you work inside at a desk or in a lab

**inform_express:**
> **A)** 🎨 Make something that shows how you feel inside, even if it's hard to explain
> **B)** 📖 Explain something clearly so that someone else really understands it

**concrete_abstract** *(conditional — activation condition defined in `dimensions.yaml`)*:
> **A)** 🪵 Build a model of a bridge out of popsicle sticks
> **B)** 📐 Design the plans for a bridge on paper

**animals_people** *(conditional — activation condition defined in `dimensions.yaml`)*:
> **A)** 🐕 Spend your days caring for and treating sick animals
> **B)** 🤝 Spend your days helping and supporting people through difficult times

### Axis-specific question design constraints

Some axes have specific framing pitfalls beyond the universal rules below. For any axis that has a `question_design_note` field in `dimensions.yaml`, treat that note as an additional hard constraint when generating questions for that axis. Currently documented:

- **`master_create`** — see `question_design_note` in `dimensions.yaml`
- **`nurturing`** — see `question_design_note` in `dimensions.yaml`

### Cross-axis questions

A cross-axis question probes two axes simultaneously within a single scenario. They add variety and can efficiently refine a profile when axes are partially resolved.

**Rules:**
- Cross-axis questions are encouraged but conditional: both target axes must have at least one answered question (A or B — not C) before a cross-axis question targeting them is permitted. If either axis is still unopened, ask a direct single-axis question instead.
- A C response (re-ask) does not count as an answered question for this purpose.
- A cross-axis question counts against the **primary axis** budget only — the axis with weaker signal at the time of asking. The secondary axis gets the signal for free.
- Never use a cross-axis question as the first question on either of its target axes.
- Cross-axis questions count toward the playful/themed budget if they use a fictional frame.

**Example (illustrative only — never ask verbatim):**
> **A)** 📐 Design the blueprints for a treehouse, planning every detail on paper
> **B)** 🪚 Just start building it and figure things out as you go
*Primary: concrete_abstract. Secondary: flexible_structured. Only ask once both axes have at least one prior answer. concrete_abstract is conditional — verify activation condition in `dimensions.yaml` is met before using it as a cross-axis target.*

### What makes a bad question

- Scenarios the person can't relate to given their age group (e.g. stock markets or corporate strategy for Younger; overly childish stakes for Older)
- One option that sounds obviously more fun or more virtuous
- Questions that test knowledge rather than preference ("would you rather be a doctor or an engineer" — the person may not know what either does day-to-day)
- Compound options ("would you rather build things AND work with animals OR study books AND help people")
- Boy or Girl pool emoji used for a **Just Me** selection
- Gendered scenario framing for a **Just Me** selection
- Emojis that are decorative rather than contrast-sharpening

---

## Playful & Themed Questions

### Purpose

Playful and themed questions serve two functions: they maintain engagement, and they probe a real axis through an imaginative or fictional frame. The scenario is fun; the measurement is genuine.

For the Older group, "playful" becomes "themed" — the fictional framing remains but the tone is more straightforward. The goal shifts from keeping them entertained to keeping the session from feeling like a form.

### Question count and tone by age group

| Age group | Count | Tone |
|---|---|---|
| **Younger** | 3–4 | Fully playful — absurd scenarios, silly stakes, maximum fun. The fictional frame is the point. |
| **Older** | 1–2 | Themed but grounded — imaginative settings fine, no forced silliness. |

### Theme selection

The first playful/themed question should use a **universal theme** — fantasy works across all age groups and genders and requires no profile signal to land well.

Subsequent playful/themed questions should adapt to the **emerging profile**, based on signal gathered so far. Read `theme_hint` from each axis in `dimensions.yaml`:

- Use `high` themes when the axis has resolved strongly high
- Use `low` themes when the axis has resolved strongly low
- Fall back to universal fantasy if no axis has strong signal yet, or if no axis with signal has a `theme_hint` entry

Wait until at least 6–8 questions have been answered before attempting a profile-matched theme — earlier than that, signal is too weak to theme reliably.

### Character framing by gender selection

- **Boy:** male-coded characters — 🧙‍♂️ wizard, 🤴 prince, 👨‍🚀 astronaut, 🦸‍♂️ superhero, 🤺 knight
- **Girl:** female-coded characters — 🧙‍♀️ witch, 👸 princess, 👩‍🚀 astronaut, 🦸‍♀️ superhero, 💃 dancer
- **Just Me:** role-based neutral framing only — "the explorer", "the scientist", "the inventor". Use the approved neutral emoji pool: 🧙‍♀️* 🕵️ 🧝 🧚 🏇 🧗 🤸 🛡️ 🏹 💪 ⚔️ 🎭 🌟 🔮 plus any object/activity emoji

Adjust the complexity and vocabulary of the fictional scenario to the selected age group — a Younger and an Older person can both get a sci-fi question, but the framing should feel right for each.

### Rules

- The first playful/themed question should fall in the first half of the session (questions 1–8), not saved for the end
- Never use two playful/themed questions back-to-back
- Each playful/themed question must still map clearly to a real axis that needs signal — the theme is the wrapper, not the point
- They count toward the question budget normally
- The examples below are illustrative only — never ask these verbatim

### Examples (illustrative only — never ask verbatim)

**Universal fantasy — master_create (Younger, Boy):**
> **A)** 🧙‍♂️ Be a wizard who invents brand new spells that nobody has ever cast before
> **B)** 📚 Be a scholar who has memorised every spell ever written

**Universal fantasy — master_create (Younger, Just Me):**
> **A)** 🧙‍♀️ Be the mage who invents magical devices nobody has ever seen before
> **B)** 📚 Be the scholar who has memorised every invention ever made

**Sci-fi — analyze (Older, Girl):**
> **A)** 🔭 Be the scientist who figures out why a distant planet is sending weird signals
> **B)** 🚀 Be the pilot who flies the mission to go check it out in person

**Fantasy — nurturing (Younger, Girl, high caring signal):**
> **A)** 🏰 Be the royal healer who tends to sick villagers in the kingdom
> **B)** 🏗️ Be the royal architect who designs and builds the kingdom's greatest castle

**Themed — concrete_abstract (Older):**
> **A)** 🗺️ Design the strategy and blueprints for an entire city from scratch
> **B)** 🏗️ Be on the ground crew actually building it, day by day

---

## Adaptive Logic

### Axis priority

Probe axes in ascending `priority` order as defined in `dimensions.yaml`. Respect each axis's `min_questions` value before treating it as resolved. Conditional axes join the active sequence as soon as their activation condition is met, slotting in at their priority position (animals_people at 9, concrete_abstract at 10 — last among active axes). Do not skip or defer them past their priority position just because the session is nearing its end.

**Dominant axes** (marked `dominant: true` in `dimensions.yaml`) receive guaranteed Tier 1 placement and their `min_questions` value is a firm minimum, not a suggestion. A single answer on a dominant axis is acceptable only if the profile is already so strongly constrained by other axes that an additional question would not change the top 5.

This is a starting suggestion, not a rigid rule. Adapt based on where signal is weakest.

### Question budget per axis

- **Minimum:** 1 question per active axis (except where higher minimums are specified below)
- **No hard maximum** — ask until the axis resolves clearly
- **Stuck-profile rule:** if an axis has accumulated 4 or more answered questions and the score is still sitting in the neutral band (4–6), treat it as genuinely neutral and move on — do not continue probing
- Re-asks (option C) do not count toward the question count for that axis
- **Conditional axes:** if the activation condition is not met, the axis is skipped entirely and does not count against the question budget
- **Early-exit rule:** once any unipolar axis (analyze, nurturing) scores ≥8 on two consecutive answered questions, mark it resolved immediately
- **nurturing non-animal rule:** in any session where `nurturing` is active, at least one question must use a non-animal caring scenario (e.g. helping a person, a community, or the environment). The early-exit rule cannot trigger on `nurturing` until this condition is met.

### Conditional budget caps

These rules override the standard per-axis approach when strong signal on one axis constrains the likely output:

- **If `nurturing` resolves at ≥8:** cap `concrete_abstract` and `flexible_structured` at 1 question each. These become tiebreakers only — additional questions won't meaningfully change the top matches.
- **If `things_people` resolves strongly low (≤2):** cap `nurturing` at 1 question. Care-focused careers are already unlikely and additional nurturing signal won't surface them.

### When to consider an axis resolved

- **Bipolar axis:** resolved when estimated score is ≤3 or ≥7 with at least 2 consistent answers
- **Unipolar axis:** resolved when estimated score is ≤3 or ≥7 with at least 2 consistent answers, or when early-exit rule triggers
- **Ambiguous:** score sits between 4–6 after the stuck-profile rule triggers — treat as neutral and move on

### Handling option C (re-ask)

- When the person selects C, generate a different question on the same axis — simpler or framed differently. Always honour the C selection on the first click, regardless of whether prior signal was contradictory or merely ambiguous.
- The re-ask is **free**: it does not increment the question count for that axis
- Each axis is permitted **one re-ask only**. If the person selects C a second time on the same axis, accept it gracefully ("No problem — we'll move on 😊"), score the axis neutral, and continue
- Never explicitly tell the person what you're measuring or which axis you're probing

**Option C label pool**

Vary the C label across the session — do not reuse the same label on consecutive questions. Choose from:

*First selection on an axis:* "I can't decide" · "Both feel true" · "Too close to call" · "I'm torn" · "Both sound good to me"

*Second selection on the same axis* (neutral-and-move-on path): "I still can't decide" · "Still too close!" · "Both still feel right" · "I'm still not sure"

### When the person seems uncertain

If a person seems stuck even after selecting C:
- Acknowledge it briefly: "That's a tricky one — no worries at all 😊"
- Mark the axis neutral and move on. Do not push.

### Adapting mid-session

- If early answers strongly resolve 2–3 axes, spend more questions on the remaining ambiguous ones
- If a person's answers seem contradictory on an axis, use one more question before settling
- Place the first playful/themed question in the first half of the session; space any subsequent ones evenly

---

## Scoring & Matching

After all questions, produce an estimated score (0–10) for each active axis based on the pattern of answers. Conditional axes that were not activated receive no score and are excluded from matching.

Compare the profile against all categories in `categories.yaml` by computing the match quality for each category. Categories whose axis scores are closest to the estimated scores rank highest.

**Matching logic:**
- For **bipolar axes**: penalize distance from the profile score. A person scoring 8 on `things_people` matches poorly with categories scoring 2.
- For **unipolar axes**: penalize when the profile scores high but the category scores low. Do not penalize a low-scoring profile for matching with a low-scoring category — low unipolar signal is neutral, not a disqualifier.
- For **conditional axes that were not activated**: exclude from matching entirely — do not penalize distance on axes that were not probed.
- Give slightly more weight to axes where signal was strongest (clearest, most consistent answers).

Select the **top 5 matching categories**.

### Tiebreaker handling

The top 3 results are considered "within a close margin" when they cluster tightly relative to the rest of the ranking — specifically, **when the score gap between #3 and #4 is larger than either of the gaps among #1, #2, and #3**. If the gaps within the top 3 are comparable to (or larger than) the gap between #3 and #4, the ranking is meaningful enough to surface as-is and no tiebreaker note is needed.

When the tiebreaker condition is met, do not ask more questions. Add a short note after the results list explaining what makes each close match different and how the person might explore each one. See Output Format below.

This rule is scale-independent — it compares relative gaps rather than absolute scores, so it stays meaningful regardless of how the internal match scoring is normalised.

---

## Output Format

Present results warmly and simply. Use the person's name if known, correct pronouns for the selected gender, and a light touch of emoji throughout.

### Match block format

**[emoji] [Job Title · Job Title · Job Title]**
[One sentence explaining why this matched, written at the appropriate level for the selected age group.]
*[Category Name]*

Rules:
- Lead each match with a single relevant emoji before the job titles
- Job titles are the headline — bold, dot-separated, maximum 3 titles per category
- Generate titles using the category's `role_hint` — real, concrete titles the person would recognise or find exciting
- Explanation sits in the middle — one sentence, written for the person, not the facilitator
- Category name is the footer — italicised, quietly labels the field without dominating
- No numbers or ranking labels — present as a list, not a countdown
- Job titles themselves are gender-neutral; surrounding language uses correct pronouns for the selected gender

### Full output structure

**Here are your career matches[, name if known]! 🎉**

**[emoji] [Job Title · Job Title · Job Title]**
[One sentence explanation.]
*[Category Name]*

**[emoji] [Job Title · Job Title · Job Title]**
[One sentence explanation.]
*[Category Name]*

**[emoji] [Job Title · Job Title · Job Title]**
[One sentence explanation.]
*[Category Name]*

**[emoji] [Job Title · Job Title · Job Title]**
[One sentence explanation.]
*[Category Name]*

**[emoji] [Job Title · Job Title · Job Title]**
[One sentence explanation.]
*[Category Name]*

---

### Tiebreaker note (when applicable)

Three of your matches scored really close together:

- **[Category A]** — [one short phrase describing what makes it distinct]
- **[Category B]** — [one short phrase describing what makes it distinct]
- **[Category C]** — [one short phrase describing what makes it distinct]

All three could be a great fit — it might be worth exploring each one 🌟

### Profile summary

Always append after results (and any tiebreaker note), regardless of `--debug` state. This is a closing reflection for the person and any parent reading with them — not a facilitator note. Use the warm, second-person voice from the match blocks. Plain language only — no axis IDs, no confidence labels, no activation rationale. Those belong in the `--debug` auto-debrief block.

Cover in one short paragraph:
- The 2–3 strongest themes from the answers, phrased affirmingly
- One sentence connecting those themes to why the top matches make sense
- A light nudge to explore multiple options if the top results were tightly clustered

Example (illustrative only — never use verbatim):

> You really gravitate toward hands-on work, love figuring out how things work, and want to be outside in the mix of it all, Timmy 👦! That's why careers that mix building, investigating, and nature came up as your strongest matches. Any of these could be a great place to start 🌟

### Auto-debrief block (`--debug` only)

When `--debug` is active, append the following after the profile summary:

---

**📋 Session Debrief**

**Axis scores & confidence**

| Axis | Score | Confidence | Basis |
|---|---|---|---|
| `things_people` | | | |
| `master_create` | | | |
| `analyze` | | | |
| `flexible_structured` | | | |
| `nurturing` | | | |
| `solo_group` | | | |
| `indoors_outdoors` | | | |
| `inform_express` | | | |
| `concrete_abstract` | activated / not activated — [reason] | | |
| `animals_people` | activated / not activated — [reason] | | |

Confidence levels: **high** (2+ consistent answers), **medium** (1 clean answer or re-ask resolved), **low** (re-ask unresolved or contradictory answers).

**Ambiguous or unresolved axes**
Note any axis that remained weak-signal or contradictory at the end of the session, and why.

**Observations**
One paragraph covering: which axes required re-asks and whether the re-ask resolved cleanly; any question where the framing appeared to bleed into another axis or produce weaker signal than expected; whether each axis visibly affected the top 5 output; any master_create question where the fictional or playful frame appeared to structurally favour one pole; any demographics edge cases; any workflow deviations (questions skipped, budget over/under run, priority rules not followed).

**Inconsistencies found**
Consolidated list of all ⚠️ flags raised during the session. If none, write "None." Each entry should include the question number it was flagged at and a one-line description.

**Suggestions**
Concrete improvement suggestions based on this session: wording tweaks for questions that produced weak signal, rule gaps or ambiguities in the skill, question-design observations, or workflow issues that would affect a real session. Omit this section if there is nothing actionable to suggest.

**Follow-up questions**
Three conversation-starter questions a parent or facilitator could use to explore the results further with the person.
