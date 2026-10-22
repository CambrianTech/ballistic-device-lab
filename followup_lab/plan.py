"""Content-addressed leader promotion; never changes search scores."""

import hashlib
import json

from ballistic_lab.reporting.dc_search import promoted


def identity(candidate):
    return hashlib.sha256(json.dumps(candidate["obstacles"], sort_keys=True).encode()).hexdigest()[
        :20
    ]


def leader(snapshot):
    rows = promoted([r for history in snapshot["histories"].values() for r in history])
    return rows[0]["candidate"] if rows else None


def passes(values):
    return len(values) >= 3 and all(
        abs(b - a) <= 1e-9 + 0.01 * abs(b) for a, b in zip(values[-3:-1], values[-2:], strict=True)
    )
