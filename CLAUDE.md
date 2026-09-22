# Career Assessment — Project Context

## Identity

- **GitHub repo:** https://github.com/BoniniTech/career-assessment
- **What it is:** A career matching assessment for children and young people. A facilitator runs sessions; Claude asks adaptive "Would You Rather" questions, builds a profile across 10 axes, and outputs ranked career categories.

---

## Source of Truth Files

| File | Purpose |
|---|---|
| `live/dimensions.yaml` | The 10 scoring axes — authoritative contract for all axis IDs, types, score ranges, priorities, and activation conditions |
| `live/categories.yaml` | Career categories, each scored against all 10 axes. Drives matching logic. |
| `analytics/archetypes.yaml` | Archetype seeds for the analytics script. Add a seed for every axis when adding a new axis. |
| `live/career-assessment.md` | The primary assessment skill. Synced to Claude.ai via GitHub connector. |

Always read `live/dimensions.yaml` and `live/categories.yaml` before making any changes to axis scores, categories, or skill logic.

---

## Skills

Each skill lives in `skills/<skill-name>/SKILL.md`. Triggers are exact — Claude does not run a skill unless the trigger matches precisely.

| Skill | Trigger | When to load |
|---|---|---|
| Career Assessment | `career-assessment` or `career-assessment --debug` | Running a live session — skill lives at `live/career-assessment.md`, synced to Claude.ai |
| Analytics | `career-assessment-analytics` | Batch validation and diagnostic reports |
| Find Fresh Axis | `career-assessment-find-fresh-axis` | Proposing a new axis |
| Find Fresh Category | `career-assessment-find-fresh-category` | Proposing a new career category |

## Pre-commit Hooks

Both hooks fire whenever `live/categories.yaml` or `live/dimensions.yaml` is staged. They are configured via `core.hooksPath = .githooks`. Run `git config core.hooksPath .githooks` after a fresh clone to activate them.

**YAML validation** — `scripts/validate_yaml.py` checks structural integrity of both YAML files before anything is committed. Run manually:
```
python scripts/validate_yaml.py dimensions
python scripts/validate_yaml.py categories
```

**Axis priority recompute** — `scripts/recalc.py` recomputes axis priorities and re-stages `live/dimensions.yaml` with updated `priority` fields. Run manually:
```
python scripts/recalc.py           # recompute and update dimensions.yaml
python scripts/recalc.py --report  # also print full discrimination table
```

## Analytics

`scripts/analytics.py` generates synthetic profiles from `analytics/archetypes.yaml`, scores them
against `live/categories.yaml`, and reports on axis weakness and category coverage. The log
is written to `analytics/log.json` (gitignored — local only). All axis, category, and
activation-condition data is read live from YAML; no changes to the script are needed when
adding axes or categories (only `analytics/archetypes.yaml` seeds need updating).

```
python scripts/analytics.py                          # status: record count + top weak axes
python scripts/analytics.py run <n>                  # generate and score N profiles
python scripts/analytics.py run <n> --verbose        # include per-profile detail
python scripts/analytics.py run <n> --archetype <id> # restrict to one archetype seed
python scripts/analytics.py review                   # aggregate stats across full log
```

**When adding a new axis:** add a seed value for it to every archetype in `analytics/archetypes.yaml`.
The script errors at startup if any archetype is missing a seed for a defined axis.

**When adding a new category:** no changes needed — the script picks it up automatically from `live/categories.yaml`.

---

## Dev Workflow

Open tasks are tracked in [GitHub Issues](https://github.com/BoniniTech/career-assessment/issues). Check there for current work items.

Read `docs/design-decisions.md` before making structural changes to axes or scoring logic — it captures non-obvious typing decisions that aren't visible in the files.

### Adding an axis or category
Follow the step-by-step workflow in `docs/axis-addition-workflow.md` exactly — it covers all files that need updating and the validation test sessions required. Do not skip steps.

### Committing changes
- Commit `dimensions.yaml` and `categories.yaml` together when both are modified
- Commit skill files separately from data files
- Axis priorities are updated automatically on commit — no manual recalc step needed

### Branch, commit, and PR conventions

**Branching**
- Always `git fetch origin main && git checkout -b <prefix/name> origin/main` before starting any task
- Never work on an auto-generated worktree branch (e.g. `claude/...`) — push to a correctly named remote branch if needed
- Prefixes: `feat/` (new functionality) · `fix/` (bug fixes) · `upkeep/` or `cleanup/` (maintenance, docs, housekeeping)

**Commit messages**
- Semantic format: `fix: …`, `feat: …`, `upkeep: …` — imperative, lowercase
- No `Co-Authored-By: Claude …` footer

**PRs**
- Every completed task: commit → push → `gh pr create` — all steps automatically, no need to ask
- PR body: `## Summary` bullets + `## Test plan` checklist + `Closes #NN` footer; no "Generated with Claude Code" line
- Auto-assignee is handled by a GitHub Action — no `--assignee` flag needed
- `main` is protected by a ruleset: no direct pushes, force-pushes, or deletion, and PRs need a code-owner approval. Only the org admin can bypass, and only through a PR (`gh pr merge --admin`). Merge only when Victor says to
- Use `--template <filename>` from `.github/ISSUE_TEMPLATE/` when filing issues (`bug.md`, `qa.md`, `feature.md`, `enhancement.md`)

---

## Conventions

- Axis IDs follow `low_pole_high_pole` naming convention (e.g. `things_people`, `master_create`)
- All axis IDs in `categories.yaml` must match `dimensions.yaml` exactly
- Conditional axes are scored in `categories.yaml` for all categories — the activation condition controls probing during sessions, not scoring
- Non-triggering categories should score `animals_people: 5` (neutral) — see [issue #2](https://github.com/BoniniTech/career-assessment/issues/2)
- `dominant: true` axes (`things_people`, `nurturing`) get guaranteed Tier 1 placement and firm `min_questions` minimums
- Do not add features or axes without running the analytics skill and validation sessions first
