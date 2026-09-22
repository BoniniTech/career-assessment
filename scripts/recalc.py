#!/usr/bin/env python3
"""Recomputes axis priority order from live/categories.yaml and live/dimensions.yaml.
Writes updated priority fields directly to live/dimensions.yaml in-place.

Usage:
    python scripts/recalc.py
    python scripts/recalc.py --report   # also prints full discrimination table
"""

import sys
import re
import math
from pathlib import Path

try:
    import yaml
except ImportError:
    print("pyyaml required. Run: pip install pyyaml")
    sys.exit(1)

REPO_ROOT = Path(__file__).parent.parent
DIMS_PATH = REPO_ROOT / "live" / "dimensions.yaml"
CATS_PATH = REPO_ROOT / "live" / "categories.yaml"

# Calibrated at 33 categories to flag only axes already marked dominant. Revisit if
# the flag gets noisy as categories grow — indoors_outdoors (2.16 stdev) is the nearest watch-out.
DOMINANT_STDEV_THRESHOLD = 2.2
DOMINANT_SEP_THRESHOLD = 25.0


def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate(axes, categories):
    axis_ids = {a["id"] for a in axes}
    errors = []
    for cat in categories:
        for ax_id in axis_ids:
            if ax_id not in cat["axes"]:
                errors.append(f"  {cat['id']}: missing axis '{ax_id}'")
            elif not (0 <= cat["axes"][ax_id] <= 10):
                errors.append(f"  {cat['id']}: axis '{ax_id}' score {cat['axes'][ax_id]} out of [0, 10]")
        for ax_id in cat["axes"]:
            if ax_id not in axis_ids:
                errors.append(f"  {cat['id']}: undefined axis '{ax_id}'")
    return errors


def compute_metrics(ax_id, categories):
    scores = [cat["axes"][ax_id] for cat in categories]
    n = len(scores)
    mean = sum(scores) / n
    stdev = math.sqrt(sum((s - mean) ** 2 for s in scores) / n)

    low_pole = sum(1 for s in scores if s <= 3)
    high_pole = sum(1 for s in scores if s >= 7)

    total_pairs = n * (n - 1) // 2
    sep_pairs = sum(
        1 for i in range(n) for j in range(i + 1, n)
        if abs(scores[i] - scores[j]) >= 4
    )
    pair_sep_rate = (sep_pairs / total_pairs * 100) if total_pairs else 0.0

    low_pct = low_pole / n
    high_pct = high_pole / n
    if low_pct >= 0.20 and high_pct >= 0.20:
        shape = "bimodal"
    elif low_pct >= 0.40 and high_pct <= 0.15:
        shape = "skewed-low"
    elif high_pct >= 0.40 and low_pct <= 0.15:
        shape = "skewed-high"
    else:
        shape = "flat"

    return {
        "stdev": stdev,
        "low_pole": low_pole,
        "high_pole": high_pole,
        "pair_sep_rate": pair_sep_rate,
        "shape": shape,
    }


def parse_upstream_ids(condition_str, known_ids):
    """Extract axis IDs referenced in an activation condition string."""
    return [ax_id for ax_id in known_ids if re.search(rf"\b{re.escape(ax_id)}\b", condition_str)]


def build_meta(axes, categories):
    axis_ids = [a["id"] for a in axes]
    meta = {}
    for ax in axes:
        ax_id = ax["id"]
        m = compute_metrics(ax_id, categories)
        m["dominant"] = ax.get("dominant", False)
        m["min_questions"] = ax.get("min_questions", 1)
        m["current_priority"] = ax.get("priority")
        activation = ax.get("activation")
        m["conditional"] = activation is not None
        m["upstream_ids"] = (
            parse_upstream_ids(activation["condition"], axis_ids) if activation else []
        )
        meta[ax_id] = m
    return meta


def compute_sequence(meta):
    def disc_key(ax_id):
        return (-meta[ax_id]["stdev"], -meta[ax_id]["pair_sep_rate"])

    all_upstream = set()
    for ax_id, m in meta.items():
        if m["conditional"]:
            all_upstream.update(m["upstream_ids"])

    dominant = sorted([ax_id for ax_id, m in meta.items() if m["dominant"]], key=disc_key)
    promoted = sorted([
        ax_id for ax_id in all_upstream
        if not meta[ax_id]["dominant"] and not meta[ax_id]["conditional"]
    ], key=disc_key)
    remaining = sorted([
        ax_id for ax_id, m in meta.items()
        if not m["dominant"] and not m["conditional"] and ax_id not in all_upstream
    ], key=disc_key)
    conditionals = sorted([ax_id for ax_id, m in meta.items() if m["conditional"]], key=disc_key)

    sequence = dominant + promoted + remaining + conditionals
    new_priorities = {ax_id: i + 1 for i, ax_id in enumerate(sequence)}

    tier1_ids = set(dominant) | set(promoted)
    tier2_ids = set(remaining)
    tier3_ids = set(conditionals)

    return sequence, new_priorities, tier1_ids, tier2_ids, tier3_ids


def update_yaml_priorities(yaml_text, new_priorities):
    """Update priority fields in-place, preserving all formatting and comments."""
    lines = yaml_text.split("\n")
    current_axis_id = None
    result = []
    for line in lines:
        id_match = re.match(r"\s+- id:\s+(\S+)", line)
        if id_match:
            current_axis_id = id_match.group(1)
        if current_axis_id in new_priorities:
            p_match = re.match(r"(\s+priority:\s+)\d+(.*)", line)
            if p_match:
                line = f"{p_match.group(1)}{new_priorities[current_axis_id]}{p_match.group(2)}"
        result.append(line)
    return "\n".join(result)


def main():
    report = "--report" in sys.argv

    dims_data = load_yaml(DIMS_PATH)
    cats_data = load_yaml(CATS_PATH)
    axes = dims_data["axes"]
    categories = cats_data["categories"]

    errors = validate(axes, categories)
    if errors:
        print("Validation errors — recalc aborted:")
        for e in errors:
            print(e)
        sys.exit(1)

    meta = build_meta(axes, categories)
    sequence, new_priorities, tier1_ids, tier2_ids, tier3_ids = compute_sequence(meta)

    changes = [
        f"  {ax_id}: {meta[ax_id]['current_priority']} -> {new_priorities[ax_id]}"
        for ax_id in sequence
        if meta[ax_id]["current_priority"] != new_priorities[ax_id]
    ]

    yaml_text = DIMS_PATH.read_text(encoding="utf-8")
    updated_text = update_yaml_priorities(yaml_text, new_priorities)
    DIMS_PATH.write_text(updated_text, encoding="utf-8")

    n_cats = len(categories)
    n_axes = len(axes)
    print(f"Recalc complete -- {n_cats} categories, {n_axes} axes")

    if report:
        print(f"\n{'Axis':<30} {'Stdev':>6} {'PairSep':>8} {'LoPole':>7} {'HiPole':>7} {'Shape':<14} {'Dom':>4} {'Cond':>5}")
        print("-" * 92)
        for ax_id, m in sorted(meta.items(), key=lambda x: (-x[1]["stdev"], -x[1]["pair_sep_rate"])):
            dom = "Y" if m["dominant"] else ""
            cond = "Y" if m["conditional"] else ""
            print(f"{ax_id:<30} {m['stdev']:>6.2f} {m['pair_sep_rate']:>7.1f}% {m['low_pole']:>7} {m['high_pole']:>7} {m['shape']:<14} {dom:>4} {cond:>5}")

    print("\nPriority sequence:")
    current_tier = None
    for ax_id in sequence:
        p = new_priorities[ax_id]
        m = meta[ax_id]
        tier = 1 if ax_id in tier1_ids else (2 if ax_id in tier2_ids else 3)
        if tier != current_tier:
            tier_label = {1: "Tier 1 (frontload)", 2: "Tier 2 (mid-session)", 3: "Tier 3 (conditionals)"}[tier]
            print(f"\n  -- {tier_label} --")
            current_tier = tier
        changed = " *" if m["current_priority"] != p else ""
        dom_note = " [dominant]" if m["dominant"] else ""
        cond_note = f" (if {', '.join(m['upstream_ids'])})" if m["conditional"] else ""
        print(f"  {p}. {ax_id}{dom_note}{cond_note}{changed}")

    if changes:
        print(f"\nChanged ({len(changes)}):")
        for c in changes:
            print(c)
    else:
        print("\nNo priority changes.")

    flags = [
        f"  {ax_id}: stdev {m['stdev']:.2f}, sep {m['pair_sep_rate']:.1f}% — crosses dominant thresholds, review recommended"
        for ax_id, m in meta.items()
        if not m["dominant"] and not m["conditional"]
        and m["stdev"] >= DOMINANT_STDEV_THRESHOLD
        and m["pair_sep_rate"] >= DOMINANT_SEP_THRESHOLD
    ]
    if flags:
        print("\nDominant threshold flags:")
        for f in flags:
            print(f)


if __name__ == "__main__":
    main()
