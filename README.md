# Career Matching Assessment

A career matching assessment for children and young people. A facilitator runs a session with one person at a time. Claude asks an adaptive series of "Would You Rather" questions, builds a personality profile across multiple dimensions, then outputs a ranked list of career categories with example job titles and a short explanation of why each matched.

Sessions run on [claude.ai](https://claude.ai) (web, desktop, or mobile app). The skill shows answer choices as clickable buttons, which only claude.ai provides, so it won't work through the API or in Claude Code.

---

## Quick start: run a session on claude.ai

You need three files from `live/`:

| File | Where it goes in claude.ai |
|---|---|
| `live/dimensions.yaml` | Project file |
| `live/categories.yaml` | Project file |
| `live/career-assessment.md` | Custom skill (uploaded as a ZIP, see step 3) |

### 1. Get the files

On this repo's GitHub page, click the green **Code** button, then **Download ZIP**. All three files are in the `live` folder inside it:

| OS | Where the files are |
|---|---|
| Windows | Open the ZIP in File Explorer: `~\Downloads\career-assessment-main.zip\career-assessment-main\live\` |
| macOS | Double-click the ZIP to unzip it: `~/Downloads/career-assessment-main/live/` |

If you use git, you can clone the repo instead. The files are in `live/`, and in step 3 you run the command from the repo root.

Take all three files from the same download: the skill and the two YAML files are updated together, and mixing versions can give wrong matches.

### 2. Create a Project and add the two YAML files

1. In claude.ai, open **Projects** and create a new project (e.g. "Career Assessment").
2. In the project's files panel, upload `dimensions.yaml` and `categories.yaml`.
3. Optional: paste this into the project's instructions so an unrecognised first message gets a helpful reply:

   > If the opening message is exactly `career-assessment` or `career-assessment --debug`, run the career-assessment skill. Otherwise respond: "To start the career assessment, type: `career-assessment`"

### 3. Add the skill

claude.ai only accepts skills as a ZIP containing a folder named after the skill, with the instructions in a file called `SKILL.md`. To build it, open a terminal (PowerShell on Windows, Terminal on macOS) and go to the folder that contains `live`:

| OS | Folder to run the command in |
|---|---|
| Windows | Right-click the ZIP → **Extract All** (keep the default destination), then `cd ~\Downloads\career-assessment-main\career-assessment-main` |
| macOS | `cd ~/Downloads/career-assessment-main` |

The command leaves `career-assessment.zip` in that folder.

macOS / Linux:

```bash
mkdir career-assessment && cp live/career-assessment.md career-assessment/SKILL.md && zip -r career-assessment.zip career-assessment
```

Windows (PowerShell):

```powershell
New-Item -ItemType Directory career-assessment; Copy-Item live/career-assessment.md career-assessment/SKILL.md; tar -a -c -f career-assessment.zip career-assessment
```

Then in claude.ai:

1. Turn on code execution: **Settings → Capabilities**, enable **Code execution and file creation**. Skills don't run without it.
2. Go to **Customize → Skills**, click **+**, then **Create skill → Upload a skill**, and pick `career-assessment.zip`.
3. Make sure the skill's toggle is on.

Custom skills belong to your account, not to the project. Each facilitator uploads the skill on their own account. See Anthropic's [Use skills in Claude](https://support.claude.com/en/articles/12512180-use-skills-in-claude) if the menus have moved.

### 4. Start a session

Open a **new chat inside the project** and send exactly:

```
career-assessment
```

The whole message must be just that command. Claude does not start the assessment on natural-language requests like "let's do the career quiz".

| Command | Use it for |
|---|---|
| `career-assessment` | Real sessions with a young person |
| `career-assessment --debug` | Test runs by a facilitator or developer. Adds per-question notes, inconsistency flags, and a debrief after the results. Don't use it with a real participant. |

Use one chat per participant. Start a new chat for the next person.

### Updating

When `live/` changes on `main`, replace both project files and upload the new skill ZIP again, all from the same commit.

---

## Repository Structure

```
career-assessment/
├── live/                              # What runs on claude.ai
│   ├── dimensions.yaml                # Scoring axes: source of truth for axis IDs, score ranges, types, and activation conditions
│   ├── categories.yaml                # Career categories, each tagged with axis scores and a role_hint
│   └── career-assessment.md           # Main assessment skill
├── analytics/
│   └── archetypes.yaml                # Archetype seeds for synthetic profiles in scripts/analytics.py
├── docs/
│   ├── design-decisions.md            # Non-obvious axis typing decisions (read before structural changes)
│   ├── axis-addition-workflow.md      # Step-by-step process for adding a new axis
│   ├── category-addition-workflow.md  # Step-by-step process for adding a new category
│   ├── analytics-internals.md
│   ├── find-fresh-axis-internals.md
│   └── find-fresh-category-internals.md
├── scripts/
│   ├── analytics.py                   # Generates and scores synthetic profiles; reports weak axes and coverage gaps
│   ├── recalc.py                      # Recomputes axis priority order from live data; runs automatically on commit
│   └── validate_yaml.py               # Validates dimensions.yaml, categories.yaml, and archetypes.yaml structure
└── skills/                            # Maintainer skills, run from Claude Code in this repo
    ├── career-assessment-analytics/
    ├── career-assessment-find-fresh-axis/
    └── career-assessment-find-fresh-category/
```

---

## Skills

Each skill has an exact trigger. Claude does not run a skill unless its trigger is matched precisely.

| Skill | Trigger | Where | Description |
|---|---|---|---|
| Career Assessment | `career-assessment` or `career-assessment --debug` | claude.ai | Runs the full career matching assessment. Handles demographics, adaptive questioning, scoring, and output. `--debug` adds facilitator notes and auto-debrief. |
| Analytics & Validation | `career-assessment-analytics` | Claude Code | Generates synthetic profiles, runs batch scoring, and produces diagnostic reports to identify weak axes and category coverage gaps. |
| Find Fresh Axis | `career-assessment-find-fresh-axis` | Claude Code | Identifies the closest-scoring category pair, checks for dimension misalignments, and proposes a new axis that would differentiate the pair. Discussion-only, does not write to any file without approval. |
| Find Fresh Category | `career-assessment-find-fresh-category` | Claude Code | Analyses the axis space for underserved regions and proposes one new category per run. Discussion-only, does not write to any file without approval. |

### Adding a new skill
1. Add a row to the table above with the skill name, trigger, where it runs, and a one-line description.
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

## Development

Requires Python 3 and `pyyaml` (`pip install pyyaml`).

After cloning, turn on the pre-commit hooks. They validate the YAML files and recompute axis priorities whenever `live/dimensions.yaml` or `live/categories.yaml` is staged.

```bash
git config core.hooksPath .githooks
```

Script usage, conventions, and the branch/PR workflow are in [`CLAUDE.md`](CLAUDE.md). To add an axis or category, follow [`docs/axis-addition-workflow.md`](docs/axis-addition-workflow.md) or [`docs/category-addition-workflow.md`](docs/category-addition-workflow.md).

---

## License

[MIT](LICENSE)
