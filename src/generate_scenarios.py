"""SC04 Step 2 - reproducible traffic-state scenario generator.

Creates 10,000 valid GENERATED traffic states (not real observations) plus a
small separate file of deliberately INVALID rows for testing the validator.

Run from the repository root:
    python src/generate_scenarios.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GENERATED_DIR = PROJECT_ROOT / "data" / "generated"
REPORT_DIR = PROJECT_ROOT / "data" / "reports"
VALID_FILE = GENERATED_DIR / "traffic_scenarios_10000.csv"
INVALID_FILE = GENERATED_DIR / "invalid_test_scenarios.csv"
REPORT_FILE = REPORT_DIR / "scenario_quality_report.md"

SEED = 42

# ---- Documented assumptions (temporary, editable in docs/STEP-1.md) -------
MAX_QUEUE = 60        # vehicles that fit on one approach in the model
MAX_WAIT_SEC = 300    # upper wait limit from the data dictionary
COUNTS = {            # 10,000 valid scenarios in total
    "normal": 5000,
    "boundary": 1500,
    "stress": 1500,
    "difficult": 1500,
    "emergency": 500,
}
N_INVALID = 120

COLUMNS = [
    "state_id", "queue_ns", "queue_ew", "density_ns_pct", "density_ew_pct",
    "max_wait_ns_sec", "max_wait_ew_sec", "emergency_direction", "scenario_type",
]


def density_from_queue(rng, queue):
    """Density rises with queue length, plus small measurement noise."""
    value = queue / MAX_QUEUE * 100 + rng.normal(0, 4)
    return round(float(np.clip(value, 0, 100)), 1)


def wait_from_queue(rng, queue):
    """Longer queues tend to wait longer; always inside 0..MAX_WAIT_SEC."""
    if queue == 0:
        return 0
    value = queue * rng.uniform(2.0, 5.0) + rng.uniform(0, 40)
    return int(np.clip(round(value), 0, MAX_WAIT_SEC))


def make_row(rng, q_ns, q_ew, w_ns=None, w_ew=None, d_ns=None, d_ew=None,
             emergency="none"):
    return {
        "queue_ns": int(q_ns),
        "queue_ew": int(q_ew),
        "density_ns_pct": density_from_queue(rng, q_ns) if d_ns is None else d_ns,
        "density_ew_pct": density_from_queue(rng, q_ew) if d_ew is None else d_ew,
        "max_wait_ns_sec": wait_from_queue(rng, q_ns) if w_ns is None else int(w_ns),
        "max_wait_ew_sec": wait_from_queue(rng, q_ew) if w_ew is None else int(w_ew),
        "emergency_direction": emergency,
    }


def normal_case(rng):
    return make_row(rng, rng.integers(0, 26), rng.integers(0, 26))


def boundary_case(rng):
    queues = [0, 1, 2, MAX_QUEUE - 1, MAX_QUEUE]
    densities = [0.0, 0.5, 1.0, 99.0, 99.5, 100.0]
    waits = [0, 1, MAX_WAIT_SEC - 1, MAX_WAIT_SEC]
    return make_row(
        rng,
        rng.choice(queues), rng.choice(queues),
        w_ns=rng.choice(waits), w_ew=rng.choice(waits),
        d_ns=float(rng.choice(densities)), d_ew=float(rng.choice(densities)),
        emergency=str(rng.choice(["none", "none", "NS", "EW"])),
    )


def stress_case(rng):
    heavy = lambda: int(rng.integers(40, MAX_QUEUE + 1))
    mode = rng.integers(0, 3)
    if mode == 0:       # both approaches jammed
        q_ns, q_ew = heavy(), heavy()
    elif mode == 1:     # NS jammed
        q_ns, q_ew = heavy(), int(rng.integers(0, 15))
    else:               # EW jammed
        q_ns, q_ew = int(rng.integers(0, 15)), heavy()
    row = make_row(rng, q_ns, q_ew)
    for key in ("max_wait_ns_sec", "max_wait_ew_sec"):
        if row[key] > 0:
            row[key] = int(min(MAX_WAIT_SEC, max(row[key], rng.integers(150, MAX_WAIT_SEC + 1))))
    return row


def difficult_case(rng):
    """Conflicting signals: short queue but very long wait, or near-ties."""
    mode = rng.integers(0, 3)
    if mode == 0:   # NS queue longer, EW has been waiting far longer
        row = make_row(rng, rng.integers(20, 40), rng.integers(3, 12),
                       w_ew=rng.integers(200, MAX_WAIT_SEC + 1))
    elif mode == 1:  # EW queue longer, NS has been waiting far longer
        row = make_row(rng, rng.integers(3, 12), rng.integers(20, 40),
                       w_ns=rng.integers(200, MAX_WAIT_SEC + 1))
    else:            # near-equal pressure on both sides
        base = int(rng.integers(10, 45))
        row = make_row(rng, base, base + int(rng.integers(-2, 3)))
    return row


def emergency_case(rng):
    direction = str(rng.choice(["NS", "EW"]))
    return make_row(rng, rng.integers(0, 40), rng.integers(0, 40), emergency=direction)


BUILDERS = {
    "normal": normal_case,
    "boundary": boundary_case,
    "stress": stress_case,
    "difficult": difficult_case,
    "emergency": emergency_case,
}


def generate_valid(rng):
    rows, seen = [], set()
    for scenario_type, count in COUNTS.items():
        made, attempts = 0, 0
        while made < count:
            attempts += 1
            if attempts > count * 200:
                raise RuntimeError(f"Could not create {count} unique {scenario_type} rows")
            row = BUILDERS[scenario_type](rng)
            key = tuple(row.values())
            if key in seen:
                continue
            seen.add(key)
            row["scenario_type"] = scenario_type
            rows.append(row)
            made += 1
    df = pd.DataFrame(rows)
    df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)
    df.insert(0, "state_id", [f"SCN-{i:05d}" for i in range(1, len(df) + 1)])
    return df[COLUMNS]


def generate_invalid(valid_df):
    """Copy some valid rows and break exactly one rule in each."""
    base = valid_df.sample(n=N_INVALID, random_state=SEED).reset_index(drop=True).astype(object)
    problems = [
        ("negative_queue", "queue_ns", -5),
        ("density_over_100", "density_ew_pct", 120.0),
        ("negative_density", "density_ns_pct", -3.0),
        ("wait_over_limit", "max_wait_ns_sec", 350),
        ("negative_wait", "max_wait_ew_sec", -10),
        ("bad_emergency_category", "emergency_direction", "North"),
        ("missing_value", "queue_ew", np.nan),
        ("non_numeric_queue", "queue_ns", "many"),
    ]
    reasons = []
    for i in range(len(base)):
        reason, column, value = problems[i % len(problems)]
        base.at[i, column] = value
        reasons.append(reason)
    base["scenario_type"] = "invalid"
    base["expected_error"] = reasons
    base["state_id"] = [f"BAD-{i:03d}" for i in range(1, len(base) + 1)]
    return base


def write_report(df, invalid_df):
    summary = df.groupby("scenario_type").size().reindex(list(COUNTS)).rename("rows")
    stats = df[["queue_ns", "queue_ew", "density_ns_pct", "density_ew_pct",
                "max_wait_ns_sec", "max_wait_ew_sec"]].agg(["min", "mean", "max"]).round(1)
    lines = [
        "# SC04 Generated Scenario Report", "",
        "## Purpose",
        "These are GENERATED traffic states for building and testing the fuzzy controller "
        "and later the GA tuner. They are not real field observations and must not be "
        "described as real data.", "",
        "## Reproducibility",
        f"- Generator: `src/generate_scenarios.py` (fixed seed `{SEED}`)",
        f"- Valid scenarios: {len(df):,} in `data/generated/traffic_scenarios_10000.csv`",
        f"- Invalid test rows: {len(invalid_df)} in `data/generated/invalid_test_scenarios.csv` "
        "(validator must reject all of them)", "",
        "## Assumptions (temporary)",
        f"- Maximum queue per approach: {MAX_QUEUE} vehicles",
        f"- Maximum waiting time: {MAX_WAIT_SEC} seconds",
        "- Density rises with queue length plus small noise, clipped to 0-100 %",
        "- Wait time rises with queue length plus a random offset",
        "- Emergency direction is `none`, `NS` or `EW`", "",
        "## Scenario mix", "",
        "| scenario_type | rows |", "|---|---:|",
    ]
    lines += [f"| {name} | {count:,} |" for name, count in summary.items()]
    lines += [f"| **total** | **{len(df):,}** |", "", "## Value ranges", "",
              "| statistic | " + " | ".join(stats.columns) + " |",
              "|---|" + "---:|" * len(stats.columns)]
    for stat, row in stats.iterrows():
        lines.append(f"| {stat} | " + " | ".join(f"{v}" for v in row) + " |")
    lines += ["", "## Emergency balance", "",
              "| emergency_direction | rows |", "|---|---:|"]
    lines += [f"| {k} | {v:,} |" for k, v in df["emergency_direction"].value_counts().items()]
    lines += ["",
              "## Usage rule",
              "Use these scenarios to develop and test the controller. Do not present them "
              "as real traffic measurements in the report."]
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_generator():
    rng = np.random.default_rng(SEED)
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    valid_df = generate_valid(rng)
    invalid_df = generate_invalid(valid_df)
    valid_df.to_csv(VALID_FILE, index=False)
    invalid_df.to_csv(INVALID_FILE, index=False)
    write_report(valid_df, invalid_df)
    return valid_df, invalid_df


if __name__ == "__main__":
    valid, invalid = run_generator()
    print("SC04 STEP 2 SCENARIO GENERATOR COMPLETED")
    print("-" * 45)
    print(f"Seed: {SEED}")
    print(f"Valid scenarios:   {len(valid):,}")
    print(f"Invalid test rows: {len(invalid)}")
    print(valid["scenario_type"].value_counts().to_string())
    print(f"Saved: {VALID_FILE.relative_to(PROJECT_ROOT)}")
    print(f"Saved: {INVALID_FILE.relative_to(PROJECT_ROOT)}")
    print(f"Saved: {REPORT_FILE.relative_to(PROJECT_ROOT)}")
