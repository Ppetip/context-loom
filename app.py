# SPDX-License-Identifier: GPL-3.0-only
"""Pack mutually exclusive source variants into a caller-measured context budget."""
import argparse
import hashlib
import json
from io_utils import canonical, integer, load, shape, text


def validate(data):
    shape(data, {"budget", "chunks"})
    integer(data["budget"], 0, 10000)
    if not isinstance(data["chunks"], list) or len(data["chunks"]) > 100:
        raise ValueError("chunks must be a list of at most 100 items")
    ids, required_sources = set(), set()
    for row in data["chunks"]:
        shape(row, {"id", "source", "text", "units", "value"}, {"required"})
        for key in ("id", "source", "text"):
            text(row[key])
        integer(row["units"], 1, 10000)
        integer(row["value"], 0, 1000000)
        if type(row.get("required", False)) is not bool:
            raise ValueError("required must be boolean")
        if row["id"] in ids:
            raise ValueError("duplicate chunk id")
        ids.add(row["id"])
        if row.get("required", False):
            if row["source"] in required_sources:
                raise ValueError("two required variants of the same source")
            required_sources.add(row["source"])
    if sum(r["units"] for r in data["chunks"] if r.get("required", False)) > data["budget"]:
        raise ValueError("required context exceeds budget")


def selection(rows, budget):
    ordered = sorted(rows, key=lambda r: r["id"])
    # Structured blocks preserve provenance; their text is untrusted data.
    return {"selected": [{**r, "sha256": hashlib.sha256(r["text"].encode("utf-8")).hexdigest()} for r in ordered],
            "used_units": sum(r["units"] for r in rows), "budget_units": budget,
            "total_value": sum(r["value"] for r in rows)}


def pack(data):
    validate(data)
    data = json.loads(canonical(data))  # Own a JSON snapshot without mutating caller data.
    required = [r for r in data["chunks"] if r.get("required", False)]
    fixed_sources = {r["source"] for r in required}
    remaining = data["budget"] - sum(r["units"] for r in required)
    groups = {}
    for row in data["chunks"]:
        if row["source"] not in fixed_sources:
            groups.setdefault(row["source"], []).append(row)
    # Multiple-choice knapsack: skip a source or choose one of its variants.
    states = {0: (0, ())}
    for source in sorted(groups):
        next_states = dict(states)
        for cost, (value, ids) in states.items():
            for row in sorted(groups[source], key=lambda r: r["id"]):
                new_cost = cost + row["units"]
                if new_cost > remaining:
                    continue
                candidate = (value + row["value"], tuple(sorted((*ids, row["id"]))))
                old = next_states.get(new_cost)
                if old is None or candidate[0] > old[0] or (candidate[0] == old[0] and candidate[1] < old[1]):
                    next_states[new_cost] = candidate
        states = next_states
    best_cost = min(states, key=lambda cost: (-states[cost][0], cost, states[cost][1]))
    selected_ids = set(states[best_cost][1]) | {r["id"] for r in required}
    selected = [r for r in data["chunks"] if r["id"] in selected_ids]
    baseline = list(required)
    sources = set(fixed_sources)
    used = sum(r["units"] for r in baseline)
    for row in data["chunks"]:
        if row["source"] not in sources and used + row["units"] <= data["budget"]:
            baseline.append(row); sources.add(row["source"]); used += row["units"]
    return {"mode": "offline-context-packing", "optimized": selection(selected, data["budget"]),
            "first_fit": selection(baseline, data["budget"]),
            "omitted_ids": sorted(r["id"] for r in data["chunks"] if r["id"] not in selected_ids),
            "limitation": "Units and values are caller-supplied, not tokenizer measurements or model quality. Include framing overhead in your budget. Provenance is not truth or a prompt-injection defense."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Authorized JSON input; stdout may contain its text")
    args = parser.parse_args()
    try:
        result = pack(load(args.input))
        print(json.dumps(result, indent=2, allow_nan=False))
    except (ValueError, TypeError, OSError, RecursionError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
