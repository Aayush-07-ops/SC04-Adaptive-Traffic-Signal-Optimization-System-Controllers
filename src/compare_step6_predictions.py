"""SC04 Step 6 - Compare direct Step 3 reference prediction with Product V1 UI service.

Generates (if missing or when --generate is passed) and compares:
    data/reports/step5_ui_reference_prediction.csv
    data/reports/step6_ui_prediction.csv

Run from the repository root:
    python src/compare_step6_predictions.py
"""
from __future__ import annotations

import argparse
import csv
import sys
from math import isclose
from pathlib import Path

import pandas as pd

SRC_DIR = Path(__file__).resolve().parent
ROOT = SRC_DIR.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from product_v1_service import load_fuzzy_model, predict_single_state
from step3_fuzzy_controller import FEATURES, predict_fuzzy

NUMERIC_FEATURES = [
    "queue_ns",
    "queue_ew",
    "density_ns_pct",
    "density_ew_pct",
    "max_wait_ns_sec",
    "max_wait_ew_sec",
]
REPORT_DIR = ROOT / "data" / "reports"
VAL_CSV = ROOT / "data" / "processed" / "validation.csv"


def generate_csvs() -> tuple[Path, Path]:
    """Generate reference prediction CSV (Step 3 code) and UI service CSV (Step 5/6)."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    val_df = pd.read_csv(VAL_CSV)
    row_df = val_df.iloc[[0]].copy()

    fuzzy_bundle, _, err = load_fuzzy_model()
    if err or fuzzy_bundle is None:
        raise RuntimeError(f"Could not load saved fuzzy model: {err}")

    ref_df = predict_fuzzy(row_df.copy(), fuzzy_bundle)
    ref_path = REPORT_DIR / "step5_ui_reference_prediction.csv"
    ref_df.to_csv(ref_path, index=False)

    ui_res = predict_single_state(row_df.iloc[0].to_dict())
    if ui_res["status"] != "ok":
        raise RuntimeError(f"UI service prediction failed: {ui_res['errors']}")

    ui_row = row_df.iloc[0].to_dict()
    ui_row["urgency_ns"] = ui_res["urgency_ns"]
    ui_row["urgency_ew"] = ui_res["urgency_ew"]
    ui_row["fuzzy_next_phase"] = ui_res["next_phase"]
    ui_row["fuzzy_green_duration_sec"] = ui_res["green_duration_sec"]
    ui_row["decision_mode"] = ui_res["decision_mode"]
    ui_path = REPORT_DIR / "step6_ui_prediction.csv"
    pd.DataFrame([ui_row]).to_csv(ui_path, index=False)
    return ref_path, ui_path


def read_prediction(path: Path) -> dict[str, str]:
    with path.open(encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    if len(rows) != 1:
        raise ValueError(f"{path.name}: expected exactly one prediction row.")
    row = rows[0]
    required = [
        *FEATURES,
        "urgency_ns",
        "urgency_ew",
        "fuzzy_next_phase",
        "fuzzy_green_duration_sec",
        "decision_mode",
    ]
    for field in required:
        if row.get(field) in (None, ""):
            raise ValueError(f"{path.name}: missing value for {field}.")
    return row


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "reference",
        type=Path,
        nargs="?",
        default=REPORT_DIR / "step5_ui_reference_prediction.csv",
    )
    parser.add_argument(
        "app_output",
        type=Path,
        nargs="?",
        default=REPORT_DIR / "step6_ui_prediction.csv",
    )
    args = parser.parse_args()

    if not args.reference.exists() or not args.app_output.exists():
        generate_csvs()

    try:
        reference = read_prediction(args.reference)
        app = read_prediction(args.app_output)
        differences = [
            name
            for name in [*NUMERIC_FEATURES, "urgency_ns", "urgency_ew", "fuzzy_green_duration_sec"]
            if not isclose(float(reference[name]), float(app[name]), rel_tol=1e-9, abs_tol=1e-9)
        ]
        differences.extend(
            name
            for name in ("emergency_direction", "fuzzy_next_phase", "decision_mode")
            if reference[name].strip() != app[name].strip()
        )
    except (OSError, ValueError, csv.Error) as error:
        parser.exit(1, f"FAIL: {error}\n")

    if differences:
        parser.exit(1, f"FAIL: Different values in {', '.join(differences)}.\n")

    print(
        "PASS: All seven inputs, next phase, green duration, and urgency scores match."
    )
    print(
        f"state_id={app['state_id']} | phase={app['fuzzy_next_phase']} | "
        f"green={app['fuzzy_green_duration_sec']} s | "
        f"urgency=({app['urgency_ns']}, {app['urgency_ew']})"
    )


if __name__ == "__main__":
    main()
