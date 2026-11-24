"""SC04 validation - checks the Step 1 sample and the Step 2 generated scenarios.

Run from the repository root:
    python src/validate_data.py
"""
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_FILE = PROJECT_ROOT / "data" / "sample_input.csv"
VALID_FILE = PROJECT_ROOT / "data" / "generated" / "traffic_scenarios_10000.csv"
INVALID_FILE = PROJECT_ROOT / "data" / "generated" / "invalid_test_scenarios.csv"

REQUIRED = ["state_id", "queue_ns", "queue_ew", "density_ns_pct", "density_ew_pct",
            "max_wait_ns_sec", "max_wait_ew_sec", "emergency_direction"]
NUMERIC = ["queue_ns", "queue_ew", "density_ns_pct", "density_ew_pct",
           "max_wait_ns_sec", "max_wait_ew_sec"]
DENSITY = ["density_ns_pct", "density_ew_pct"]
WAIT = ["max_wait_ns_sec", "max_wait_ew_sec"]
QUEUE = ["queue_ns", "queue_ew"]
CATEGORIES = {"none", "NS", "EW"}
MAX_WAIT_SEC = 300


def check_dataframe(df):
    """Return a list of error messages. An empty list means the data is valid."""
    errors = []

    missing_cols = [c for c in REQUIRED if c not in df.columns]
    if missing_cols:
        return [f"Missing columns: {missing_cols}"]

    n_missing = int(df[REQUIRED].isna().sum().sum())
    if n_missing:
        errors.append(f"Missing values found: {n_missing}")

    for column in NUMERIC:
        numeric = pd.to_numeric(df[column], errors="coerce")
        bad = int(numeric.isna().sum() - df[column].isna().sum())
        if bad:
            errors.append(f"{column}: {bad} non-numeric value(s)")
        df[column] = numeric  # work with numbers from here on

    if int((df[QUEUE] < 0).sum().sum()):
        errors.append("Negative queue length found")
    if int(((df[DENSITY] < 0) | (df[DENSITY] > 100)).sum().sum()):
        errors.append("Density outside 0-100 % found")
    if int(((df[WAIT] < 0) | (df[WAIT] > MAX_WAIT_SEC)).sum().sum()):
        errors.append(f"Wait outside 0-{MAX_WAIT_SEC} sec found")

    bad_cat = set(df["emergency_direction"].dropna().unique()) - CATEGORIES
    if bad_cat:
        errors.append(f"Invalid emergency_direction values: {sorted(bad_cat)}")

    if df["state_id"].duplicated().any():
        errors.append("Duplicate state_id found")

    return errors


def validate_file(path, label, expect_pass=True):
    print(f"\n{label}: {path.relative_to(PROJECT_ROOT)}")
    if not path.exists():
        print("  FILE NOT FOUND")
        return False
    df = pd.read_csv(path)
    print(f"  shape: {df.shape}")

    if expect_pass:
        errors = check_dataframe(df)
        if errors:
            for e in errors:
                print("  ERROR:", e)
            return False
        print("  PASS")
        return True

    # Invalid file: every row must be rejected when checked on its own.
    caught = 0
    for i in range(len(df)):
        if check_dataframe(df.iloc[[i]].copy()):
            caught += 1
    first = check_dataframe(df.copy())
    print("  sample of reported errors:", first[:3])
    if caught == len(df):
        print(f"  EXPECTED FAIL: all {caught} invalid rows were rejected")
        return True
    print(f"  PROBLEM: only {caught} of {len(df)} invalid rows were rejected")
    return False


def main():
    results = [
        validate_file(SAMPLE_FILE, "Step 1 sample"),
        validate_file(VALID_FILE, "Step 2 generated scenarios"),
        validate_file(INVALID_FILE, "Deliberately invalid rows", expect_pass=False),
    ]
    if all(results):
        print("\nSTEP 2 DATA CHECK PASSED")
    else:
        print("\nSTEP 2 DATA CHECK FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
