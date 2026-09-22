#!/usr/bin/env python3
"""
Usage:
  python validate_yaml.py dimensions   — validate live/dimensions.yaml structure
  python validate_yaml.py categories   — validate live/categories.yaml against dimensions.yaml
  python validate_yaml.py archetypes   — validate analytics/archetypes.yaml against dimensions.yaml
"""

import sys
import yaml

DIMENSIONS_PATH = "live/dimensions.yaml"
CATEGORIES_PATH = "live/categories.yaml"
ARCHETYPES_PATH = "analytics/archetypes.yaml"

REQUIRED_AXIS_FIELDS = {"id", "type", "score_range", "priority", "min_questions", "low_pole", "high_pole"}
VALID_TYPES = {"bipolar", "unipolar"}


def load(path):
    with open(path) as f:
        return yaml.safe_load(f)


def validate_dimensions():
    errors = []

    try:
        data = load(DIMENSIONS_PATH)
    except Exception as e:
        print(f"ERROR: Could not parse {DIMENSIONS_PATH}: {e}")
        sys.exit(1)

    axes = data.get("axes", [])
    if not axes:
        errors.append("No axes found.")

    seen_ids = set()
    for axis in axes:
        axis_id = axis.get("id", "<missing id>")

        if axis_id in seen_ids:
            errors.append(f"  [{axis_id}] duplicate axis ID")
        seen_ids.add(axis_id)

        missing = REQUIRED_AXIS_FIELDS - axis.keys()
        if missing:
            errors.append(f"  [{axis_id}] missing fields: {', '.join(sorted(missing))}")

        if axis.get("type") not in VALID_TYPES:
            errors.append(f"  [{axis_id}] invalid type: {axis.get('type')!r} (must be bipolar or unipolar)")

        if axis.get("score_range") != [0, 10]:
            errors.append(f"  [{axis_id}] score_range must be [0, 10], got: {axis.get('score_range')!r}")

    if not data.get("scoring"):
        errors.append("Missing 'scoring' block.")

    if errors:
        print(f"dimensions.yaml validation failed — {len(errors)} error(s):\n")
        for e in errors:
            print(e)
        sys.exit(1)

    print(f"OK — dimensions.yaml: {len(axes)} axes, all well-formed.")


def validate_categories():
    errors = []

    try:
        dimensions = load(DIMENSIONS_PATH)
    except Exception as e:
        print(f"ERROR: Could not parse {DIMENSIONS_PATH}: {e}")
        sys.exit(1)

    try:
        data = load(CATEGORIES_PATH)
    except Exception as e:
        print(f"ERROR: Could not parse {CATEGORIES_PATH}: {e}")
        sys.exit(1)

    axis_ids = {axis["id"] for axis in dimensions["axes"]}
    categories = data.get("categories", [])

    if not categories:
        errors.append("No categories found.")

    for category in categories:
        name = category.get("name", "<unnamed>")
        scored = category.get("axes", {}) or {}

        for axis_id in axis_ids:
            if axis_id not in scored:
                errors.append(f"  [{name}] missing axis: {axis_id}")

        for axis_id, score in scored.items():
            if axis_id not in axis_ids:
                errors.append(f"  [{name}] unknown axis: {axis_id} (not in dimensions.yaml)")
            elif not isinstance(score, (int, float)) or not (0 <= score <= 10):
                errors.append(f"  [{name}] axis {axis_id}: score {score!r} out of range [0, 10]")

    if errors:
        print(f"categories.yaml validation failed — {len(errors)} error(s):\n")
        for e in errors:
            print(e)
        sys.exit(1)

    print(f"OK — categories.yaml: {len(categories)} categories, all consistent with dimensions.yaml.")


def validate_archetypes():
    errors = []

    try:
        dimensions = load(DIMENSIONS_PATH)
    except Exception as e:
        print(f"ERROR: Could not parse {DIMENSIONS_PATH}: {e}")
        sys.exit(1)

    try:
        data = load(ARCHETYPES_PATH)
    except Exception as e:
        print(f"ERROR: Could not parse {ARCHETYPES_PATH}: {e}")
        sys.exit(1)

    sigma = data.get("sigma", {}) or {}
    if not isinstance(sigma.get("primary"), (int, float)):
        errors.append("sigma.primary missing or not a number")
    if not isinstance(sigma.get("secondary"), (int, float)):
        errors.append("sigma.secondary missing or not a number")

    axis_ids = {ax["id"] for ax in dimensions["axes"]}
    archetypes = data.get("archetypes", [])

    if not archetypes:
        errors.append("No archetypes found.")

    seen_ids = set()
    for arch in archetypes:
        arch_id = arch.get("id", "<missing id>")

        if arch_id in seen_ids:
            errors.append(f"  [{arch_id}] duplicate archetype ID")
        seen_ids.add(arch_id)

        if not arch.get("description"):
            errors.append(f"  [{arch_id}] missing description")

        seeds = arch.get("seeds") or {}
        missing = axis_ids - set(seeds.keys())
        if missing:
            errors.append(f"  [{arch_id}] missing seeds for: {', '.join(sorted(missing))}")

        for ax_id, val in seeds.items():
            if ax_id not in axis_ids:
                errors.append(f"  [{arch_id}] unknown axis in seeds: {ax_id}")
            elif not isinstance(val, (int, float)) or not (0 <= val <= 10):
                errors.append(f"  [{arch_id}] seed {ax_id}={val!r} out of range [0, 10]")

    if errors:
        print(f"archetypes.yaml validation failed -- {len(errors)} error(s):\n")
        for e in errors:
            print(e)
        sys.exit(1)

    print(f"OK -- archetypes.yaml: {len(archetypes)} archetypes, all consistent with dimensions.yaml.")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("dimensions", "categories", "archetypes"):
        print("Usage: validate_yaml.py dimensions|categories|archetypes")
        sys.exit(1)

    if sys.argv[1] == "dimensions":
        validate_dimensions()
    elif sys.argv[1] == "categories":
        validate_categories()
    else:
        validate_archetypes()
