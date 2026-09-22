---
title: Design Decisions
description: Non-obvious decisions about axis typing and scoring logic. Read before making structural changes to axes.
---

# Design Decisions

Non-obvious decisions that aren't visible in the files. Reference before making structural changes to axes or scoring logic.

---

**`master_create` is bipolar, not unipolar**
The genuine opposite of "drives to make new things" is "drives to master existing things" — a real and distinct personality profile. Unipolar `create` was losing signal on master-leaning profiles (clinical medicine, finance, skilled trades). Bipolar `master_create` captures both ends.

**`analyze` remains unipolar**
The opposite of analytical drive is not a meaningful signal — it's just low curiosity, not a different preference. Making it bipolar would incorrectly penalise non-analytical careers.

**`nurturing` remains unipolar**
Low nurturing drive is not a negative trait — it's just low signal. Making it bipolar would incorrectly penalise non-nurturing careers.

**`concrete_abstract` is conditional on `analyze >= 6 OR master_create >= 7`**
For pure care or people-facing profiles, this axis rarely separates the top matches. Probing it for those profiles costs question budget without improving output.

**`animals_people` is conditional on `nurturing >= 7 OR things_people >= 7`**
Only relevant when nurturing or people drive is high — otherwise neither people nor animals is a strong motivator and the axis produces noise.

**`nurturing` non-animal rule**
People with a strong animal preference can score >=8 on `nurturing` without that reflecting general nurturing drive. At least one non-animal nurturing scenario must be answered before the early-exit condition can trigger, to prevent inflated scores.

**C option: free, capped at once per axis, always honoured on first click**
The re-ask doesn't cost a question slot, but is capped to prevent loops — a second C on the same axis scores it neutral and moves on. C is honoured literally on the first click regardless of whether prior signal was contradictory or merely ambiguous. Distinguishing the two from a single prior answer isn't reliable, and silently ignoring a user's C selection is worse UX than re-asking — especially for children.

**Conditional budget caps for dominant axes**
When `nurturing >= 8` or `things_people <= 2`, remaining tiebreaker axes are capped at 1 question each. Strong signal on dominant axes already constrains the output — further probing other axes produces diminishing returns.

**Tiebreaker is explanatory, not more questions**
Near-identical top results can't be reliably separated with the current axes. Adding more questions to break ties would frustrate without improving accuracy. A brief explanatory note is more honest and more useful.
