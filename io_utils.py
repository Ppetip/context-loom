# SPDX-License-Identifier: GPL-3.0-only
"""Bounded strict JSON input for the offline command line."""
import json
from pathlib import Path


def reject_constant(value):
    raise ValueError("nonfinite JSON number")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def load(path):
    with Path(path).open("rb") as handle:
        raw = handle.read(1_048_577)
    if len(raw) > 1_048_576:
        raise ValueError("input exceeds 1 MiB")
    return json.loads(raw.decode("utf-8-sig"), parse_constant=reject_constant, object_pairs_hook=unique_object)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False)


def shape(value, required, optional=()):
    if not isinstance(value, dict) or not set(required) <= value.keys() or value.keys() - set(required) - set(optional):
        raise ValueError("object has missing or unsupported fields")


def text(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("expected nonempty text")


def integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError("integer outside supported range")
