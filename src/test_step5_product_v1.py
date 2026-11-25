"""SC04 Step 5 - Product V1 Automated Verification & Evidence Generator.

Verifies:
1. Normal inputs (NS-heavy, EW-heavy, Emergency override)
2. Boundary inputs (all-zero min, all-max, equal tie)
3. Invalid inputs (missing, non-numeric, negative, >100% density, >300s wait, bad category)
4. Missing-model graceful handling (non-crashing error message)
5. UI-service vs direct Step 3 code parity (exact output match)
6. Batch CSV validation on sample_input.csv and invalid_test_scenarios.csv

Saves:
    results/step5/step5_test_evidence.csv
    results/step5/step5_test_summary.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from product_v1_service import (
    load_fuzzy_model,
    predict_single_state,
    validate_and_predict_csv,
)
from step3_fuzzy_controller import predict_fuzzy

RESULTS_DIR = PROJECT_ROOT / "results" / "step5"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def run_all_tests() -> int:
    rows: list[dict] = []

    def record(category: str, case_id: str, expected: str, actual: str, passed: bool, detail: str) -> None:
        rows.append(
            {
                "category": category,
                "case_id": case_id,
                "expected": expected,
                "actual": actual,
                "passed": bool(passed),
                "detail": detail,
            }
        )

    # 1. Normal cases
    normal_cases = [
        (
            "NORM-01",
            {
                "state_id": "NORM-01",
                "queue_ns": "18",
                "queue_ew": "6",
                "density_ns_pct": "45",
                "density_ew_pct": "20",
                "max_wait_ns_sec": "95",
                "max_wait_ew_sec": "30",
                "emergency_direction": "none",
            },
            "NS",
        ),
        (
            "NORM-02",
            {
                "state_id": "NORM-02",
                "queue_ns": "5",
                "queue_ew": "28",
                "density_ns_pct": "18",
                "density_ew_pct": "72",
                "max_wait_ns_sec": "25",
                "max_wait_ew_sec": "160",
                "emergency_direction": "none",
            },
            "EW",
        ),
        (
            "NORM-03-EMERG",
            {
                "state_id": "NORM-03-EMERG",
                "queue_ns": "4",
                "queue_ew": "35",
                "density_ns_pct": "15",
                "density_ew_pct": "85",
                "max_wait_ns_sec": "20",
                "max_wait_ew_sec": "210",
                "emergency_direction": "NS",
            },
            "NS",
        ),
    ]
    for cid, payload, exp_phase in normal_cases:
        res = predict_single_state(payload)
        ok = (
            res["status"] == "ok"
            and res["next_phase"] == exp_phase
            and 10.0 <= res["green_duration_sec"] <= 60.0
        )
        record(
            "normal",
            cid,
            f"status=ok, phase={exp_phase}, green in [10,60]",
            f"status={res['status']}, phase={res.get('next_phase')}, green={res.get('green_duration_sec')}",
            ok,
            res.get("explanation", ""),
        )

    # 2. Boundary cases
    boundary_cases = [
        (
            "BND-01-ZERO",
            {
                "state_id": "BND-01-ZERO",
                "queue_ns": "0",
                "queue_ew": "0",
                "density_ns_pct": "0",
                "density_ew_pct": "0",
                "max_wait_ns_sec": "0",
                "max_wait_ew_sec": "0",
                "emergency_direction": "none",
            },
            "NS",
        ),
        (
            "BND-02-MAX-EW",
            {
                "state_id": "BND-02-MAX-EW",
                "queue_ns": "0",
                "queue_ew": "100",
                "density_ns_pct": "0",
                "density_ew_pct": "100",
                "max_wait_ns_sec": "0",
                "max_wait_ew_sec": "300",
                "emergency_direction": "none",
            },
            "EW",
        ),
        (
            "BND-03-ALL-MAX",
            {
                "state_id": "BND-03-ALL-MAX",
                "queue_ns": "100",
                "queue_ew": "100",
                "density_ns_pct": "100",
                "density_ew_pct": "100",
                "max_wait_ns_sec": "300",
                "max_wait_ew_sec": "300",
                "emergency_direction": "none",
            },
            "NS",
        ),
    ]
    for cid, payload, exp_phase in boundary_cases:
        res = predict_single_state(payload)
        ok = (
            res["status"] == "ok"
            and res["next_phase"] == exp_phase
            and 10.0 <= res["green_duration_sec"] <= 60.0
        )
        record(
            "boundary",
            cid,
            f"status=ok, phase={exp_phase}, green in [10,60]",
            f"status={res['status']}, phase={res.get('next_phase')}, green={res.get('green_duration_sec')}",
            ok,
            f"urgency_ns={res.get('urgency_ns')}, urgency_ew={res.get('urgency_ew')}",
        )

    # 3. Invalid inputs
    base_valid = dict(normal_cases[0][1])
    invalid_cases = [
        ("INV-01-MISSING", {**base_valid, "state_id": "INV-01", "queue_ns": ""}),
        ("INV-02-NONNUM", {**base_valid, "state_id": "INV-02", "queue_ew": "abc"}),
        ("INV-03-NEG-QUEUE", {**base_valid, "state_id": "INV-03", "queue_ns": "-5"}),
        ("INV-04-HIGH-DENS", {**base_valid, "state_id": "INV-04", "density_ns_pct": "140"}),
        ("INV-05-HIGH-WAIT", {**base_valid, "state_id": "INV-05", "max_wait_ns_sec": "450"}),
        ("INV-06-BAD-EMERG", {**base_valid, "state_id": "INV-06", "emergency_direction": "BOTH"}),
        ("INV-07-NAN", {**base_valid, "state_id": "INV-07", "density_ew_pct": "nan"}),
    ]
    for cid, payload in invalid_cases:
        res = predict_single_state(payload)
        ok = res["status"] == "validation_error" and len(res["errors"]) >= 1
        record(
            "invalid_input",
            cid,
            "status=validation_error with >=1 error",
            f"status={res['status']}, errors={len(res['errors'])}",
            ok,
            "; ".join(res["errors"]),
        )

    # 4. Missing-model check
    missing_path = PROJECT_ROOT / "models" / "does_not_exist_step5.pkl"
    res_missing = predict_single_state(base_valid, model_path=missing_path)
    ok_missing = res_missing["status"] == "model_error" and len(res_missing["errors"]) >= 1
    record(
        "missing_model",
        "MOD-01-MISSING",
        "status=model_error without crash",
        f"status={res_missing['status']}",
        ok_missing,
        "; ".join(res_missing["errors"]),
    )

    # 5. UI-vs-code parity check on 5 sample rows
    fuzzy_bundle, _, err = load_fuzzy_model()
    assert fuzzy_bundle is not None and err is None, f"Model load failed: {err}"
    sample_df = pd.read_csv(PROJECT_ROOT / "data" / "sample_input.csv").head(5)
    direct_df = predict_fuzzy(sample_df.copy(), fuzzy_bundle)

    parity_mismatches = 0
    for i in range(len(sample_df)):
        row_dict = sample_df.iloc[i].to_dict()
        ui_res = predict_single_state(row_dict)
        d_row = direct_df.iloc[i]
        match = (
            ui_res["status"] == "ok"
            and ui_res["next_phase"] == str(d_row["fuzzy_next_phase"])
            and abs(ui_res["green_duration_sec"] - float(d_row["fuzzy_green_duration_sec"])) < 1e-6
            and abs(ui_res["urgency_ns"] - float(d_row["urgency_ns"])) < 1e-6
            and abs(ui_res["urgency_ew"] - float(d_row["urgency_ew"])) < 1e-6
        )
        if not match:
            parity_mismatches += 1
    record(
        "ui_vs_code",
        "PARITY-01",
        "0 mismatches across 5 sample rows",
        f"{parity_mismatches} mismatches",
        parity_mismatches == 0,
        "Exact match on next_phase, green_duration_sec, urgency_ns, urgency_ew",
    )

    # 6. Batch CSV checks
    sample_full = pd.read_csv(PROJECT_ROOT / "data" / "sample_input.csv")
    b_valid = validate_and_predict_csv(sample_full)
    ok_b_valid = (
        b_valid["status"] == "ok"
        and b_valid["valid_count"] == len(sample_full)
        and b_valid["rejected_count"] == 0
    )
    record(
        "batch_csv",
        "BATCH-01-SAMPLE",
        f"valid={len(sample_full)}, rejected=0",
        f"valid={b_valid.get('valid_count')}, rejected={b_valid.get('rejected_count')}",
        ok_b_valid,
        "All 20 mandatory sample rows validated and predicted",
    )

    inv_full = pd.read_csv(PROJECT_ROOT / "data" / "generated" / "invalid_test_scenarios.csv")
    b_inv = validate_and_predict_csv(inv_full)
    ok_b_inv = (
        b_inv["status"] == "ok"
        and b_inv["valid_count"] == 0
        and b_inv["rejected_count"] == len(inv_full)
    )
    record(
        "batch_csv",
        "BATCH-02-INVALID",
        f"valid=0, rejected={len(inv_full)}",
        f"valid={b_inv.get('valid_count')}, rejected={b_inv.get('rejected_count')}",
        ok_b_inv,
        "All invalid test rows rejected with per-row reasons",
    )

    ev_df = pd.DataFrame(rows)
    ev_df.to_csv(RESULTS_DIR / "step5_test_evidence.csv", index=False)

    summary = {
        "total_checks": int(len(ev_df)),
        "passed_checks": int(ev_df["passed"].sum()),
        "failed_checks": int((~ev_df["passed"]).sum()),
        "by_category": {
            cat: {
                "total": int(len(grp)),
                "passed": int(grp["passed"].sum()),
            }
            for cat, grp in ev_df.groupby("category")
        },
    }
    (RESULTS_DIR / "step5_test_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    print(ev_df[["category", "case_id", "passed", "actual"]].to_string(index=False))
    print("\nSummary:", json.dumps(summary, indent=2))
    return 0 if summary["failed_checks"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
