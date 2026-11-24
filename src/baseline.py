"""Tiny runnable version of the Step 1 fixed-time baseline.

Run from the repository root:
    python src/baseline.py

Rules (see docs/baseline-pseudocode.md):
  1-3. Fixed alternation NS, EW, NS, ... with 30 s green, ignoring queues.
  4.   TEST-VERSION safety override: if emergency_direction != none, that direction gets green.
  5.   Invalid rows are rejected before any decision is made.
The baseline is NOT fuzzy logic, ANN or GA.
"""
import os
import sys

import pandas as pd

from validate_data import DEFAULT_FILE, load, validate

FIXED_GREEN_SEC = 30      # TEMPORARY
MIN_GREEN_SEC = 10        # TEMPORARY safe minimum
MAX_GREEN_SEC = 60        # TEMPORARY safe maximum
OUT_FILE = "results/step1/baseline_expected.csv"


def baseline_decision(position, row):
    """position = 0-based place of the row in the file (stands for the signal cycle position)."""
    green = max(MIN_GREEN_SEC, min(MAX_GREEN_SEC, FIXED_GREEN_SEC))
    if row["emergency_direction"] != "none":
        return row["emergency_direction"], green, "Rule 4: emergency safety override"
    phase = "NS" if position % 2 == 0 else "EW"
    return phase, green, "Rules 1-3: fixed alternation (queues ignored)"


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_FILE
    df = load(path)
    errors = validate(df)
    if errors:
        print("Rule 5: input rejected, no baseline output produced.")
        for e in errors:
            print("  -", e)
        return 1

    results = []
    for pos, (_, row) in enumerate(df.iterrows()):
        phase, green, rule = baseline_decision(pos, row)
        results.append({"state_id": row["state_id"], "baseline_next_phase": phase,
                        "baseline_green_duration_sec": green, "rule_used": rule})
        print(f"{row['state_id']}: next_phase={phase} green={green}s  [{rule}]")

    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    pd.DataFrame(results).to_csv(OUT_FILE, index=False)
    print("saved:", OUT_FILE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
