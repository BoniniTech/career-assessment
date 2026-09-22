#!/usr/bin/env python3
"""Career assessment analytics -- generates synthetic profiles, scores them against
live/categories.yaml, and reports on axis weakness and category coverage.

All axis definitions, scoring thresholds, and category data are read from live/*.yaml.
Archetype seeds live in analytics/archetypes.yaml. sigma (noise level) is derived automatically
from each seed value: seeds <=2 or >=8 use sigma=primary (strong signal), all others sigma=secondary.

Usage:
    python scripts/analytics.py                          # status: record count + top weak axes
    python scripts/analytics.py run <n>                  # generate and score N profiles
    python scripts/analytics.py run <n> --verbose        # include per-profile detail
    python scripts/analytics.py run <n> --archetype <id> # restrict to one archetype
    python scripts/analytics.py review                   # aggregate stats across full log
"""

import argparse
import json
import random
import re
import sys
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    print("pyyaml required. Run: pip install pyyaml")
    sys.exit(1)

REPO_ROOT = Path(__file__).resolve().parent.parent
DIMENSIONS_FILE = REPO_ROOT / "live" / "dimensions.yaml"
CATEGORIES_FILE = REPO_ROOT / "live" / "categories.yaml"
ARCHETYPES_FILE = REPO_ROOT / "analytics" / "archetypes.yaml"
LOG_FILE = REPO_ROOT / "analytics" / "log.json"

# Diagnostic thresholds -- policy decisions, adjust as the dataset grows
WEAK_RANGE_THRESHOLD = 2          # top-5 category score range <= this -> axis didn't discriminate
CHOPPING_BLOCK_CUTOFF = 0.40      # structurally weak in > 40% of active profiles -> flag
COVERAGE_GAP_CUTOFF = 0.03        # appears in < 3% of top-5 results -> coverage gap
DOMINANT_CATEGORY_CUTOFF = 0.25   # appears in > 25% of top-5 results -> potentially over-broad
TIGHT_CLUSTER_MARGIN = 0.05       # top1->top2 gap < this -> tightly clustered
TIGHT_CLUSTER_TOP5_MARGIN = 0.08  # top5->top6 gap < this (used with above for tightly_clustered)
WELL_SPREAD_MARGIN = 0.15         # top5->top6 gap > this -> well spread


# -- Data loading --------------------------------------------------------------

def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_log():
    if not LOG_FILE.exists():
        return []
    with open(LOG_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_log(records):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    existing = load_log()
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(existing + records, f, indent=2)


# -- Conditional axis evaluation -----------------------------------------------

def eval_condition(condition_str, axis_scores):
    """Evaluate an activation condition like 'analyze >= 6 OR master_create >= 7'.

    Reads condition strings directly from dimensions.yaml activation fields so
    adding new conditional axes requires no changes here.
    """
    def eval_clause(clause):
        clause = clause.strip()
        m = re.match(r"(\w+)\s*(>=|<=|>|<|==|!=)\s*(\d+)", clause)
        if not m:
            raise ValueError(f"Cannot parse condition clause: {clause!r}")
        axis_id, op, val = m.group(1), m.group(2), int(m.group(3))
        score = axis_scores.get(axis_id)
        if score is None:
            return False
        return {">=": score >= val, "<=": score <= val, ">": score > val,
                "<": score < val, "==": score == val, "!=": score != val}[op]

    # OR has lower precedence than AND
    or_parts = re.split(r"\bOR\b", condition_str, flags=re.IGNORECASE)
    return any(
        all(eval_clause(c) for c in re.split(r"\bAND\b", part, flags=re.IGNORECASE))
        for part in or_parts
    )


# -- Profile generation --------------------------------------------------------

def sigma_for_seed(seed, sigma_primary, sigma_secondary):
    """Strong-signal seeds (<=2 or >=8) get tighter noise; mid-range seeds get wider."""
    return sigma_primary if (seed <= 2 or seed >= 8) else sigma_secondary


def generate_profile(archetype, axes, sigma_primary, sigma_secondary):
    """Generate a synthetic axis score profile from an archetype seed with gaussian noise.

    Conditional axes are evaluated after non-conditional axes are scored so their
    activation conditions reflect the actual generated profile.
    """
    seeds = archetype["seeds"]
    conditional_ids = {ax["id"] for ax in axes if "activation" in ax}

    # First pass: all non-conditional axes
    scores = {}
    for ax in axes:
        if ax["id"] in conditional_ids:
            continue
        seed = seeds[ax["id"]]
        sigma = sigma_for_seed(seed, sigma_primary, sigma_secondary)
        raw = seed + random.gauss(0, sigma)
        scores[ax["id"]] = int(round(max(0, min(10, raw))))

    # Second pass: conditional axes -- evaluate activation against generated scores
    conditional_info = {}
    for ax in axes:
        ax_id = ax["id"]
        if ax_id not in conditional_ids:
            continue
        condition = ax["activation"]["condition"]
        activated = eval_condition(condition, scores)
        if activated:
            seed = seeds[ax_id]
            sigma = sigma_for_seed(seed, sigma_primary, sigma_secondary)
            raw = seed + random.gauss(0, sigma)
            scores[ax_id] = int(round(max(0, min(10, raw))))
            conditional_info[ax_id] = {"activated": True, "reason": condition}
        else:
            scores[ax_id] = None
            conditional_info[ax_id] = {"activated": False, "reason": f"condition not met: {condition}"}

    return scores, conditional_info


# -- Scoring & matching --------------------------------------------------------

def axis_weight(profile_score, neutral_band):
    """Higher weight for strong-signal (extreme) profile scores, lower for neutral."""
    lo, hi = neutral_band
    if profile_score <= 2 or profile_score >= 8:
        return 1.3
    elif lo <= profile_score <= hi:
        return 0.7
    else:
        return 1.0


def bipolar_contribution(profile_score, category_score):
    return 1.0 - abs(profile_score - category_score) / 10.0


def unipolar_contribution(profile_score, category_score, low_thresh, high_thresh):
    """Unipolar axes (analyze, nurturing): low profile = no penalty; high profile +
    low category = penalty scaled by signal strength and category gap.
    """
    if profile_score <= low_thresh:
        return 1.0  # weak signal -- no penalty regardless of category
    # Profile has meaningful signal; penalise if category is below low_thresh
    profile_signal = (profile_score - low_thresh) / (10.0 - low_thresh)
    category_gap = max(0, (low_thresh + 1) - category_score) / (low_thresh + 1)
    return max(0.0, 1.0 - profile_signal * category_gap)


def score_match(profile_scores, category_axes, axes_meta, scoring):
    """Compute normalised match score (0-1) for one category."""
    neutral_band = scoring["bipolar_neutral_band"]
    low_thresh = scoring["unipolar_threshold_low"]
    high_thresh = scoring["unipolar_threshold_high"]

    total_weight = 0.0
    total_contribution = 0.0

    for ax in axes_meta:
        ax_id = ax["id"]
        profile_score = profile_scores.get(ax_id)
        if profile_score is None:
            continue  # conditional axis not activated -- excluded from scoring

        category_score = category_axes.get(ax_id, 5)
        weight = axis_weight(profile_score, neutral_band)

        if ax["type"] == "unipolar":
            contrib = unipolar_contribution(profile_score, category_score, low_thresh, high_thresh)
        else:
            contrib = bipolar_contribution(profile_score, category_score)

        total_weight += weight
        total_contribution += weight * contrib

    return (total_contribution / total_weight) if total_weight > 0 else 0.0


def classify_axes(profile_scores, category_axes, axes_meta, neutral_band):
    """Classify each active axis as driving, opposing, or neutral for one category match."""
    lo, hi = neutral_band
    driving, opposing, neutral = [], [], []

    for ax in axes_meta:
        ax_id = ax["id"]
        profile_score = profile_scores.get(ax_id)
        if profile_score is None:
            continue
        category_score = category_axes.get(ax_id, 5)
        diff = abs(profile_score - category_score)
        both_neutral = (lo <= profile_score <= hi) and (lo <= category_score <= hi)

        if diff >= 4:
            opposing.append(ax_id)
        elif diff <= 2 and not both_neutral:
            driving.append(ax_id)
        else:
            neutral.append(ax_id)

    return driving, neutral, opposing


def identify_weak_axes(profile_scores, top5_cat_ids, category_map, axes_meta, neutral_band):
    """Find axes that failed to discriminate across the top-5 matched categories."""
    lo, hi = neutral_band
    weak = []

    for ax in axes_meta:
        ax_id = ax["id"]
        if profile_scores.get(ax_id) is None:
            continue  # inactive conditional axis

        cat_scores = [category_map[cat_id]["axes"].get(ax_id, 5) for cat_id in top5_cat_ids]
        score_range = max(cat_scores) - min(cat_scores)

        if score_range <= WEAK_RANGE_THRESHOLD:
            neutral_profile = lo <= profile_scores[ax_id] <= hi
            weak.append({"axis": ax_id, "neutral_profile": neutral_profile, "range": score_range})

    return weak


# -- Single profile run --------------------------------------------------------

def run_profile(archetype, axes_meta, category_map, scoring, sigma_primary, sigma_secondary):
    """Generate one synthetic profile and score it against all categories."""
    profile_scores, conditional_info = generate_profile(
        archetype, axes_meta, sigma_primary, sigma_secondary
    )
    neutral_band = scoring["bipolar_neutral_band"]

    ranked = sorted(
        ((cat_id, score_match(profile_scores, cat["axes"], axes_meta, scoring))
         for cat_id, cat in category_map.items()),
        key=lambda x: -x[1],
    )

    top5 = ranked[:5]
    top6_score = ranked[5][1] if len(ranked) > 5 else 0.0
    top5_ids = [c[0] for c in top5]

    top5_records = []
    for rank, (cat_id, ms) in enumerate(top5, 1):
        driving, neut, opposing = classify_axes(
            profile_scores, category_map[cat_id]["axes"], axes_meta, neutral_band
        )
        top5_records.append({
            "rank": rank,
            "category_id": cat_id,
            "match_score": round(ms, 4),
            "driving_axes": driving,
            "neutral_axes": neut,
            "opposing_axes": opposing,
        })

    top1_score = top5[0][1] if top5 else 0.0
    top2_score = top5[1][1] if len(top5) > 1 else 0.0
    top5_score = top5[4][1] if len(top5) >= 5 else 0.0
    top1_to_top2 = round(top1_score - top2_score, 4)
    top5_to_top6 = round(top5_score - top6_score, 4)

    weak = identify_weak_axes(profile_scores, top5_ids, category_map, axes_meta, neutral_band)

    return {
        "run_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "archetype": archetype["id"],
        "axis_scores": profile_scores,
        "conditional_axes": conditional_info,
        "top_5": top5_records,
        "match_margin": {"top1_to_top2": top1_to_top2, "top5_to_top6": top5_to_top6},
        "weak_axes": weak,
        "tightly_clustered": (
            top1_to_top2 < TIGHT_CLUSTER_MARGIN and top5_to_top6 < TIGHT_CLUSTER_TOP5_MARGIN
        ),
    }


# -- Aggregate stats -----------------------------------------------------------

def compute_stats(records, axes_meta):
    """Compute aggregate weak-axis and category-coverage stats across a set of records."""
    axis_active = defaultdict(int)
    axis_weak = defaultdict(int)
    axis_struct_weak = defaultdict(int)
    cat_appearances = defaultdict(int)
    tight_count = 0
    well_spread_count = 0
    sum_top1_top2 = 0.0
    sum_top5_top6 = 0.0

    for r in records:
        for ax_id, score in r["axis_scores"].items():
            if score is not None:
                axis_active[ax_id] += 1
        for w in r["weak_axes"]:
            axis_weak[w["axis"]] += 1
            if not w["neutral_profile"]:
                axis_struct_weak[w["axis"]] += 1
        for t in r["top_5"]:
            cat_appearances[t["category_id"]] += 1
        if r["tightly_clustered"]:
            tight_count += 1
        if r["match_margin"]["top5_to_top6"] > WELL_SPREAD_MARGIN:
            well_spread_count += 1
        sum_top1_top2 += r["match_margin"]["top1_to_top2"]
        sum_top5_top6 += r["match_margin"]["top5_to_top6"]

    n = len(records)
    return {
        "n": n,
        "axis_active": axis_active,
        "axis_weak": axis_weak,
        "axis_struct_weak": axis_struct_weak,
        "cat_appearances": cat_appearances,
        "tight_count": tight_count,
        "well_spread_count": well_spread_count,
        "avg_top1_top2": sum_top1_top2 / n if n else 0,
        "avg_top5_top6": sum_top5_top6 / n if n else 0,
    }


# -- Report output -------------------------------------------------------------

def print_weak_axis_table(stats, axes_meta):
    n = stats["n"]
    ax_ids = [ax["id"] for ax in axes_meta]
    rows = []
    for ax_id in ax_ids:
        active = stats["axis_active"].get(ax_id, 0)
        if active == 0:
            continue
        weak_pct = stats["axis_weak"].get(ax_id, 0) / active * 100
        struct_pct = stats["axis_struct_weak"].get(ax_id, 0) / active * 100
        rows.append((ax_id, active, stats["axis_weak"].get(ax_id, 0), weak_pct, struct_pct))

    rows.sort(key=lambda x: -x[4])
    print(f"\n{'Axis':<30} {'Active':>8} {'Weak':>6} {'Weak%':>7} {'Struct%':>8}")
    print("-" * 66)
    for ax_id, active, weak, weak_pct, struct_pct in rows:
        flag = "  ! CHOPPING BLOCK" if struct_pct > CHOPPING_BLOCK_CUTOFF * 100 else ""
        print(f"{ax_id:<30} {active:>8} {weak:>6} {weak_pct:>6.1f}% {struct_pct:>7.1f}%{flag}")


def print_category_table(stats, category_map):
    n = stats["n"]
    print(f"\n{'Category':<45} {'Top-5':>6} {'%':>6}")
    print("-" * 62)
    for cat_id in sorted(category_map, key=lambda c: -stats["cat_appearances"].get(c, 0)):
        count = stats["cat_appearances"].get(cat_id, 0)
        pct = count / n * 100
        flag = ""
        if pct < COVERAGE_GAP_CUTOFF * 100:
            flag = "  ! COVERAGE GAP"
        elif pct > DOMINANT_CATEGORY_CUTOFF * 100:
            flag = "  ! DOMINANT"
        print(f"{cat_id:<45} {count:>6} {pct:>5.1f}%{flag}")


def print_tightness(stats):
    n = stats["n"]
    print(f"\nTightly clustered (top1->top2 < {TIGHT_CLUSTER_MARGIN}): "
          f"{stats['tight_count']} / {stats['tight_count'] / n * 100:.1f}%")
    print(f"Well spread (top5->top6 > {WELL_SPREAD_MARGIN}): "
          f"{stats['well_spread_count']} / {stats['well_spread_count'] / n * 100:.1f}%")
    print(f"Avg top1->top2 margin: {stats['avg_top1_top2']:.4f}")
    print(f"Avg top5->top6 margin: {stats['avg_top5_top6']:.4f}")


def batch_summary(records, axes_meta, category_map, archetypes, verbose=False):
    n = len(records)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    arch_dist = defaultdict(int)
    for r in records:
        arch_dist[r["archetype"]] += 1

    print(f"\n-- Batch Summary -- {n} profiles -- {ts} ------------------------------")
    print(f"Archetypes: {', '.join(f'{k} ({v})' for k, v in sorted(arch_dist.items()))}")

    stats = compute_stats(records, axes_meta)

    print("\n-- Weak Axis Ranking ----------------------------------------------------")
    print_weak_axis_table(stats, axes_meta)
    print("  Struct% excludes profiles where the axis was in the profile's neutral band.")

    print("\n-- Category Coverage ----------------------------------------------------")
    print_category_table(stats, category_map)

    print("\n-- Match Tightness ------------------------------------------------------")
    print_tightness(stats)

    print("\n-- Per-Archetype Top Categories -----------------------------------------")
    archetype_ids = sorted({r["archetype"] for r in records})
    for arch_id in archetype_ids:
        arch_records = [r for r in records if r["archetype"] == arch_id]
        counts = defaultdict(int)
        for r in arch_records:
            for t in r["top_5"]:
                counts[t["category_id"]] += 1
        top3 = sorted(counts.items(), key=lambda x: -x[1])[:3]
        top3_str = ", ".join(f"{c} ({n})" for c, n in top3)
        print(f"  {arch_id}: {top3_str}")

    if verbose:
        print("\n-- Per-Profile Detail ---------------------------------------------------")
        for r in records:
            print(f"\n  [{r['archetype']}] run {r['run_id'][:8]}")
            active = {k: v for k, v in r["axis_scores"].items() if v is not None}
            print(f"  Scores: {active}")
            print(f"  Top-5: {[t['category_id'] for t in r['top_5']]}")
            if r["weak_axes"]:
                print(f"  Weak axes: {[w['axis'] for w in r['weak_axes']]}")
            if r["tightly_clustered"]:
                print("  ! Tightly clustered")


def review_report(records, axes_meta, category_map, archetypes):
    if not records:
        print("Log is empty -- run `python scripts/analytics.py run <n>` first.")
        return

    timestamps = [r["timestamp"] for r in records]
    first_date = min(timestamps)[:10]
    last_date = max(timestamps)[:10]

    print(f"\n-- Session Log Review -- {len(records)} profiles "
          f"-- started {first_date} -- last run {last_date} --")

    stats = compute_stats(records, axes_meta)

    print("\n-- Weak Axis Ranking (full log) -----------------------------------------")
    print_weak_axis_table(stats, axes_meta)
    print("  Struct% excludes profiles where the axis was in the profile's neutral band.")

    print("\n-- Category Coverage (full log) -----------------------------------------")
    print_category_table(stats, category_map)

    print("\n-- Match Tightness (full log) -------------------------------------------")
    print_tightness(stats)

    # Trend: group by date, show weak axis leaders per day
    by_date = defaultdict(list)
    for r in records:
        by_date[r["timestamp"][:10]].append(r)

    if len(by_date) > 1:
        print("\n-- Trend Over Time ------------------------------------------------------")
        for date in sorted(by_date):
            day_stats = compute_stats(by_date[date], axes_meta)
            leaders = sorted(
                (ax_id for ax_id in day_stats["axis_struct_weak"]),
                key=lambda a: -(day_stats["axis_struct_weak"][a] /
                                max(1, day_stats["axis_active"].get(a, 1)))
            )[:3]
            print(f"  {date} ({len(by_date[date])} profiles): "
                  f"struct-weak leaders = {leaders or 'none'}")


# -- Startup validation --------------------------------------------------------

def validate_archetypes(archetypes, axes_meta):
    ax_ids = {ax["id"] for ax in axes_meta}
    errors = []
    for arch in archetypes:
        missing = ax_ids - set(arch["seeds"])
        if missing:
            errors.append(f"  '{arch['id']}' missing seeds for: {sorted(missing)}")
        for ax_id, val in arch["seeds"].items():
            if ax_id not in ax_ids:
                errors.append(f"  '{arch['id']}' references unknown axis: {ax_id}")
            elif not isinstance(val, (int, float)) or not (0 <= val <= 10):
                errors.append(f"  '{arch['id']}' seed {ax_id}={val} out of [0, 10]")
    return errors


# -- CLI -----------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Career assessment analytics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="cmd")

    run_p = sub.add_parser("run", help="Generate and score N synthetic profiles")
    run_p.add_argument("n", type=int, help="Number of profiles to generate")
    run_p.add_argument("--verbose", action="store_true", help="Print per-profile detail")
    run_p.add_argument("--archetype", metavar="ID", help="Restrict to a single archetype")

    sub.add_parser("review", help="Aggregate stats across the full session log")

    args = parser.parse_args()

    # Load live data
    dims = load_yaml(DIMENSIONS_FILE)
    cats = load_yaml(CATEGORIES_FILE)
    archs = load_yaml(ARCHETYPES_FILE)

    axes_meta = dims["axes"]
    scoring = dims["scoring"]
    category_map = {cat["id"]: cat for cat in cats["categories"]}
    archetypes = archs["archetypes"]
    sigma_primary = archs.get("sigma", {}).get("primary", 1.5)
    sigma_secondary = archs.get("sigma", {}).get("secondary", 2.5)

    errors = validate_archetypes(archetypes, axes_meta)
    if errors:
        print("Archetype validation failed -- add missing seeds to analytics/archetypes.yaml:")
        for e in errors:
            print(e)
        sys.exit(1)

    if args.cmd is None:
        # Bare invocation: status summary
        log = load_log()
        if not log:
            print("No records in log. Run: python scripts/analytics.py run <n>")
            return
        last_run = max(r["timestamp"] for r in log)[:10]
        recent = log[-min(len(log), 200):]
        stats = compute_stats(recent, axes_meta)
        top_weak = sorted(
            (ax for ax in stats["axis_struct_weak"]),
            key=lambda a: -(stats["axis_struct_weak"][a] /
                            max(1, stats["axis_active"].get(a, 1)))
        )[:3]
        print(f"Log: {len(log)} records, last run {last_run}")
        print(f"Top structurally weak axes (last {len(recent)} records): "
              f"{top_weak or 'none'}")
        return

    if args.cmd == "review":
        review_report(load_log(), axes_meta, category_map, archetypes)
        return

    if args.cmd == "run":
        pool = archetypes
        if args.archetype:
            pool = [a for a in archetypes if a["id"] == args.archetype]
            if not pool:
                valid = [a["id"] for a in archetypes]
                print(f"Unknown archetype '{args.archetype}'. Valid: {valid}")
                sys.exit(1)

        batch_id = str(uuid.uuid4())
        records = []
        print(f"Running {args.n} profiles...", end="", flush=True)
        for i in range(args.n):
            arch = random.choice(pool)
            record = run_profile(arch, axes_meta, category_map, scoring, sigma_primary, sigma_secondary)
            record["batch_id"] = batch_id
            records.append(record)
            if (i + 1) % 10 == 0:
                print(".", end="", flush=True)
        print()

        save_log(records)
        batch_summary(records, axes_meta, category_map, archetypes, verbose=args.verbose)


if __name__ == "__main__":
    main()
