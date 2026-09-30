
import pandas as pd
import sys

FILE = sys.argv[1] if len(sys.argv) > 1 else "data/sample_input.csv"

REQUIRED = [
    "state_id",
    "queue_ns",
    "queue_ew",
    "density_ns_pct",
    "density_ew_pct",
    "max_wait_ns_sec",
    "max_wait_ew_sec",
    "emergency_direction"
]

NUMERIC = [
    "queue_ns",
    "queue_ew",
    "density_ns_pct",
    "density_ew_pct",
    "max_wait_ns_sec",
    "max_wait_ew_sec"
]

def validate_data(file):
    try:
        df = pd.read_csv(file)

        # Check required columns
        missing = [c for c in REQUIRED if c not in df.columns]
        if missing:
            raise ValueError(f"Missing columns: {missing}")

        # NEW: Reject empty datasets
        if df.empty:
            raise ValueError("Dataset contains no data rows")

        # Check missing values
        if df[REQUIRED].isna().any().any():
            raise ValueError("Missing values found")

        # Check numeric values
        for col in NUMERIC:
            df[col] = pd.to_numeric(df[col], errors="raise")

        # State IDs must be unique
        if not df["state_id"].is_unique:
            raise ValueError("Duplicate state IDs")

        # Queues cannot be negative
        if (df[["queue_ns", "queue_ew"]] < 0).any().any():
            raise ValueError("Queue cannot be negative")

        # Density must be between 0 and 100
        if not df[["density_ns_pct", "density_ew_pct"]].isin(
            range(101)
        ).all().all():
            raise ValueError("Density must be between 0 and 100")

        # Maximum wait must be between 0 and 300 seconds
        for col in ["max_wait_ns_sec", "max_wait_ew_sec"]:
            if not df[col].between(0, 300).all():
                raise ValueError(f"{col} must be between 0 and 300")

        # Validate emergency direction
        if not df["emergency_direction"].isin(
            ["none", "NS", "EW"]
        ).all():
            raise ValueError("Invalid emergency direction")

        print("Dataset shape:", df.shape)
        print("STEP 1 DATA CHECK PASSED")
        return True

    except Exception as e:
        print("STEP 1 DATA CHECK FAILED:", e)
        return False


if __name__ == "__main__":
    success = validate_data(FILE)
    sys.exit(0 if success else 1)