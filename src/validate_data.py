"""Step 1 data validator for SC04 - Adaptive Traffic Signal Optimization System.

Usage (run from the repository root):
    python src/validate_data.py                                  # validate data/sample_input.csv -> PASS
    python src/validate_data.py --file data/invalid_input.csv --expect-fail
                                                                 # the bad row must be REJECTED

Exit code 0 = the outcome matched what was expected, 1 = it did not.
"""
import argparse
import re
import sys

import pandas as pd

DEFAULT_FILE = "data/sample_input.csv"

REQUIRED = [
    "state_id", "queue_ns", "queue_ew",
    "density_ns_pct", "density_ew_pct",
    "max_wait_ns_sec", "max_wait_ew_sec",
    "emergency_direction",
]
NUMERIC = [
    "queue_ns", "queue_ew",
    "density_ns_pct", "density_ew_pct",
    "max_wait_ns_sec", "max_wait_ew_sec",
]
QUEUE_COLS = ["queue_ns", "queue_ew"]
DENSITY_COLS = ["density_ns_pct", "density_ew_pct"]
WAIT_COLS = ["max_wait_ns_sec", "max_wait_ew_sec"]
CATEGORIES = {"none", "NS", "EW"}          # exact spelling only
ID_PATTERN = re.compile(r"^TRF-\d{3}$")
MANDATORY_IDS = ["TRF-001", "TRF-002", "TRF-003", "TRF-004", "TRF-005"]

# TEMPORARY limits (documented in data/README.md). Change here AND in the docs.
MAX_QUEUE_VEHICLES = 100
MAX_DENSITY_PCT = 100
MAX_WAIT_SEC = 300


def load(path):
    """Read a CSV. Empty cells become NaN; the text 'none' stays text."""
    return pd.read_csv(path, keep_default_na=False, na_values=[""])


def validate(df, check_mandatory=False):
    """Return a list of human-readable error messages (empty list = valid)."""
    errors = []

    for col in df.columns:
        if col != col.strip():
            errors.append(f"Header '{col}' contains accidental spaces")

    missing_cols = [c for c in REQUIRED if c not in df.columns]
    if missing_cols:
        errors.append(f"Missing columns: {missing_cols}")
        return errors
    extra = [c for c in df.columns if c not in REQUIRED]
    if extra:
        errors.append(f"Unexpected columns (not in data dictionary): {extra}")
    if df.empty:
        errors.append("File has a header but no data rows")
        return errors

    def where(i):
        return f"row {i + 2} ({df.at[i, 'state_id']})"   # +2 = header line + 1-based

    # 1. missing values
    for col in REQUIRED:
        for i in df.index[df[col].isna()]:
            errors.append(f"{where(i)}: '{col}' is missing")

    # 2. numeric type
    numeric_ok = []
    for col in NUMERIC:
        if pd.api.types.is_numeric_dtype(df[col]):
            numeric_ok.append(col)
        else:
            errors.append(f"Column '{col}' must be numeric but contains text")

    # 3. ranges
    for col in QUEUE_COLS:
        if col in numeric_ok:
            for i, v in df[col].dropna().items():
                if v < 0:
                    errors.append(f"{where(i)}: {col} = {v} is negative (queue must be >= 0 vehicles)")
                elif v > MAX_QUEUE_VEHICLES:
                    errors.append(f"{where(i)}: {col} = {v} is above the limit of {MAX_QUEUE_VEHICLES} vehicles")
                elif v != int(v):
                    errors.append(f"{where(i)}: {col} = {v} must be a whole number of vehicles")
    for col in DENSITY_COLS:
        if col in numeric_ok:
            for i, v in df[col].dropna().items():
                if v < 0 or v > MAX_DENSITY_PCT:
                    errors.append(f"{where(i)}: {col} = {v} is outside 0 to {MAX_DENSITY_PCT} percent")
    for col in WAIT_COLS:
        if col in numeric_ok:
            for i, v in df[col].dropna().items():
                if v < 0 or v > MAX_WAIT_SEC:
                    errors.append(f"{where(i)}: {col} = {v} is outside 0 to {MAX_WAIT_SEC} seconds")

    # 4. categories (exact spelling: none / NS / EW)
    for i, v in df["emergency_direction"].dropna().items():
        if v not in CATEGORIES:
            errors.append(f"{where(i)}: emergency_direction = '{v}' is not one of {sorted(CATEGORIES)}")

    # 5. identifiers
    ids = df["state_id"].dropna().astype(str)
    for i, v in ids.items():
        if not ID_PATTERN.match(v):
            errors.append(f"{where(i)}: state_id '{v}' does not match TRF-### format")
    for v in sorted(ids[ids.duplicated(keep=False)].unique()):
        errors.append(f"state_id '{v}' is duplicated (identifiers must be unique)")

    # 6. mandatory cases present
    if check_mandatory:
        absent = [m for m in MANDATORY_IDS if m not in set(ids)]
        if absent:
            errors.append(f"Mandatory test cases missing from file: {absent}")

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate a traffic-state CSV file.")
    parser.add_argument("--file", default=DEFAULT_FILE, help=f"CSV to check (default: {DEFAULT_FILE})")
    parser.add_argument("--expect-fail", action="store_true",
                        help="Use for the deliberately invalid file: success means it is rejected.")
    args = parser.parse_args()

    try:
        df = load(args.file)
    except FileNotFoundError:
        print(f"ERROR: file not found: {args.file}")
        return 1

    print("file:", args.file)
    print("shape:", df.shape)
    print("columns:", list(df.columns))
    print("missing values:", df.isna().sum().to_dict())

    errors = validate(df, check_mandatory=not args.expect_fail)

    if args.expect_fail:
        if errors:
            print("\nEXPECTED FAIL - the invalid data was correctly rejected:")
            for e in errors:
                print("  -", e)
            return 0
        print("\nUNEXPECTED PASS - the invalid file should have been rejected!")
        return 1

    if errors:
        print("\nFAIL - data is not valid:")
        for e in errors:
            print("  -", e)
        return 1
    print("\nPASS: STEP 1 DATA CHECK PASSED (%d valid rows)" % len(df))
    return 0


if __name__ == "__main__":
    sys.exit(main())
