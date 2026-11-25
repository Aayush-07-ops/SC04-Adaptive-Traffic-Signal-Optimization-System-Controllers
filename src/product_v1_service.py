"""SC04 Step 5 - Product V1 Service Layer.

Connects the Streamlit UI (app/app.py) to the saved Mamdani Fuzzy Logic
Controller (models/fuzzy_traffic_controller.pkl) and the Step 1/2/3 data
validator (src/validate_data.py).

Keeps inference completely separate from training, validates all user inputs
without crashing, handles missing/corrupted model files gracefully, and
returns human-readable results with units, explanations, and limitations.
"""
from __future__ import annotations

import json
import math
import pickle
import sys
from pathlib import Path
from typing import Any

import pandas as pd

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from step3_fuzzy_controller import (
    MAX_DENSITY_PCT,
    MAX_GREEN_SEC,
    MAX_WAIT_SEC,
    MIN_GREEN_SEC,
    predict_fuzzy,
)
from validate_data import CATEGORIES, check_dataframe

PROJECT_ROOT = SRC_DIR.parent
DEFAULT_MODEL_PATH = PROJECT_ROOT / "models" / "fuzzy_traffic_controller.pkl"
DEFAULT_META_PATH = PROJECT_ROOT / "models" / "fuzzy_controller_metadata.json"

MAX_QUEUE_UNIVERSE = 100.0
FIXED_BASELINE_GREEN_SEC = 30.0

LIMITATIONS_TEXT = (
    "Academic prototype trained/evaluated on 10,000 synthetically generated "
    "scenarios (isolated 2-phase NS/EW junction). It does not read live "
    "roadside sensors or hardware signal controllers and has not undergone "
    "field safety certification."
)

NUMERIC_LIMITS: dict[str, tuple[float, float, str]] = {
    "queue_ns": (0.0, MAX_QUEUE_UNIVERSE, "vehicles"),
    "queue_ew": (0.0, MAX_QUEUE_UNIVERSE, "vehicles"),
    "density_ns_pct": (0.0, MAX_DENSITY_PCT, "%"),
    "density_ew_pct": (0.0, MAX_DENSITY_PCT, "%"),
    "max_wait_ns_sec": (0.0, MAX_WAIT_SEC, "seconds"),
    "max_wait_ew_sec": (0.0, MAX_WAIT_SEC, "seconds"),
}


def load_fuzzy_model(
    model_path: Path = DEFAULT_MODEL_PATH,
    meta_path: Path = DEFAULT_META_PATH,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, str | None]:
    """Load the saved Step 3 fuzzy controller bundle without re-training.

    Returns (fuzzy_bundle, metadata, error_message).
    """
    path = Path(model_path)
    if not path.exists():
        return (
            None,
            None,
            (
                f"Saved fuzzy controller file not found at '{path}'. "
                "Run `python src/step3_fuzzy_controller.py` to generate and save the model."
            ),
        )

    try:
        with open(path, "rb") as fh:
            raw_bundle = pickle.load(fh)
    except Exception as exc:
        return (
            None,
            None,
            f"Could not load saved model from '{path}': {exc}",
        )

    fuzzy_bundle = (
        raw_bundle.get("fuzzy_bundle", raw_bundle)
        if isinstance(raw_bundle, dict)
        else None
    )
    if (
        not isinstance(fuzzy_bundle, dict)
        or "urgency_system" not in fuzzy_bundle
        or "green_system" not in fuzzy_bundle
    ):
        return (
            None,
            None,
            (
                f"Saved model file '{path}' is missing required FIS keys "
                "('urgency_system', 'green_system'). Re-run `python src/step3_fuzzy_controller.py`."
            ),
        )

    metadata: dict[str, Any] | None = None
    mpath = Path(meta_path)
    if mpath.exists():
        try:
            metadata = json.loads(mpath.read_text(encoding="utf-8"))
        except Exception:
            metadata = None

    return fuzzy_bundle, metadata, None


def validate_single_input(raw: dict[str, Any]) -> tuple[pd.DataFrame | None, list[str]]:
    """Validate a single traffic-state dictionary from the UI or tests.

    Returns (validated_1row_df, errors). If errors is non-empty, df is None.
    """
    errors: list[str] = []
    cleaned: dict[str, Any] = {}

    state_id = str(raw.get("state_id", "UI-001")).strip()
    if not state_id:
        errors.append("state_id cannot be blank.")
    cleaned["state_id"] = state_id or "UI-001"

    for field, (lo, hi, unit) in NUMERIC_LIMITS.items():
        val = raw.get(field)
        if val is None or (isinstance(val, str) and val.strip() == ""):
            errors.append(f"{field}: value is missing (expected {lo:.0f} to {hi:.0f} {unit}).")
            continue
        if isinstance(val, bool):
            errors.append(f"{field}: boolean is not a valid numeric value.")
            continue
        try:
            num = float(val)
        except (TypeError, ValueError):
            errors.append(f"{field}: '{val}' is not a valid number.")
            continue
        if not math.isfinite(num):
            errors.append(f"{field}: value must be finite (not NaN or Inf).")
            continue
        if num < lo or num > hi:
            errors.append(
                f"{field}: {num:g} {unit} is out of range (allowed: {lo:.0f} to {hi:.0f} {unit})."
            )
            continue
        cleaned[field] = num

    emerg_raw = raw.get("emergency_direction")
    emerg = "" if emerg_raw is None else str(emerg_raw).strip()
    if emerg not in CATEGORIES:
        errors.append(
            f"emergency_direction: '{emerg}' is invalid (allowed: none, NS, EW)."
        )
    else:
        cleaned["emergency_direction"] = emerg

    if errors:
        return None, errors

    df = pd.DataFrame([cleaned])
    df_errors = check_dataframe(df.copy())
    if df_errors:
        return None, df_errors

    return df, []


def _build_explanation(row: pd.Series, raw: dict[str, Any]) -> str:
    """Create a plain-English explanation of the controller decision."""
    phase = str(row["fuzzy_next_phase"])
    green = float(row["fuzzy_green_duration_sec"])
    u_ns = float(row["urgency_ns"])
    u_ew = float(row["urgency_ew"])
    mode = str(row["decision_mode"])

    if mode == "emergency_override":
        return (
            f"Emergency vehicle detected on {phase}. Safety override bypassed "
            f"normal urgency competition and assigned immediate GREEN to {phase} "
            f"for {green:.2f} seconds (fuzzy urgency scores: NS={u_ns:.1f}, EW={u_ew:.1f})."
        )

    winner_label = "North-South (NS)" if phase == "NS" else "East-West (EW)"
    loser_label = "East-West (EW)" if phase == "NS" else "North-South (NS)"
    win_u = u_ns if phase == "NS" else u_ew
    lose_u = u_ew if phase == "NS" else u_ns
    return (
        f"{winner_label} received higher fuzzy urgency ({win_u:.1f}/100 vs {lose_u:.1f}/100 "
        f"for {loser_label}) based on queue, density, and max wait time. "
        f"The green-duration FIS assigned {green:.2f} seconds (bounded to "
        f"{MIN_GREEN_SEC:.0f}-{MAX_GREEN_SEC:.0f} s), compared to a rigid "
        f"{FIXED_BASELINE_GREEN_SEC:.0f} s fixed-time baseline."
    )


def predict_single_state(
    raw: dict[str, Any],
    model_path: Path = DEFAULT_MODEL_PATH,
    meta_path: Path = DEFAULT_META_PATH,
) -> dict[str, Any]:
    """Validate inputs, load saved fuzzy model, and return readable decision."""
    df, errors = validate_single_input(raw)
    if errors or df is None:
        return {
            "status": "validation_error",
            "errors": errors,
            "limitations": LIMITATIONS_TEXT,
        }

    fuzzy_bundle, metadata, model_err = load_fuzzy_model(
        model_path=model_path,
        meta_path=meta_path,
    )
    if model_err or fuzzy_bundle is None:
        return {
            "status": "model_error",
            "errors": [model_err or "Failed to load saved fuzzy controller."],
            "limitations": LIMITATIONS_TEXT,
        }

    pred_df = predict_fuzzy(df, fuzzy_bundle)
    row = pred_df.iloc[0]
    phase = str(row["fuzzy_next_phase"])
    green_sec = float(row["fuzzy_green_duration_sec"])
    phase_meaning = (
        "North-South (NS) gets GREEN; East-West (EW) holds RED."
        if phase == "NS"
        else "East-West (EW) gets GREEN; North-South (NS) holds RED."
    )

    return {
        "status": "ok",
        "errors": [],
        "state_id": str(row["state_id"]),
        "next_phase": phase,
        "phase_meaning": phase_meaning,
        "green_duration_sec": green_sec,
        "green_bounds_sec": (MIN_GREEN_SEC, MAX_GREEN_SEC),
        "urgency_ns": float(row["urgency_ns"]),
        "urgency_ew": float(row["urgency_ew"]),
        "decision_mode": str(row["decision_mode"]),
        "baseline_green_sec": FIXED_BASELINE_GREEN_SEC,
        "green_delta_vs_baseline_sec": round(green_sec - FIXED_BASELINE_GREEN_SEC, 2),
        "explanation": _build_explanation(row, raw),
        "limitations": LIMITATIONS_TEXT,
        "model_metadata": metadata or {},
    }


def validate_and_predict_csv(
    df: pd.DataFrame,
    model_path: Path = DEFAULT_MODEL_PATH,
    meta_path: Path = DEFAULT_META_PATH,
) -> dict[str, Any]:
    """Validate an uploaded batch CSV row-by-row and run fuzzy inference on valid rows."""
    fuzzy_bundle, _, model_err = load_fuzzy_model(
        model_path=model_path,
        meta_path=meta_path,
    )
    if model_err or fuzzy_bundle is None:
        return {
            "status": "model_error",
            "errors": [model_err or "Saved fuzzy model unavailable."],
            "valid_predictions": pd.DataFrame(),
            "rejected_rows": pd.DataFrame(),
        }

    schema_errs = [
        c
        for c in [
            "state_id",
            "queue_ns",
            "queue_ew",
            "density_ns_pct",
            "density_ew_pct",
            "max_wait_ns_sec",
            "max_wait_ew_sec",
            "emergency_direction",
        ]
        if c not in df.columns
    ]
    if schema_errs:
        return {
            "status": "validation_error",
            "errors": [f"Missing required CSV columns: {schema_errs}"],
            "valid_predictions": pd.DataFrame(),
            "rejected_rows": pd.DataFrame(),
        }

    valid_indices: list[int] = []
    rejected_records: list[dict[str, Any]] = []

    seen_ids: set[str] = set()
    for idx in range(len(df)):
        row_df = df.iloc[[idx]].copy()
        row_errors = check_dataframe(row_df.copy())
        sid = str(row_df.iloc[0]["state_id"])
        if sid in seen_ids:
            row_errors.append(f"Duplicate state_id '{sid}'")
        else:
            seen_ids.add(sid)

        if not row_errors:
            # Also enforce fuzzy universe upper bound for queue (0..100)
            for qcol in ("queue_ns", "queue_ew"):
                qval = float(pd.to_numeric(row_df.iloc[0][qcol], errors="coerce"))
                if qval > MAX_QUEUE_UNIVERSE:
                    row_errors.append(f"{qcol}: {qval:g} exceeds universe max {MAX_QUEUE_UNIVERSE:.0f}")

        if row_errors:
            rejected_records.append(
                {
                    "row_index": idx,
                    "state_id": sid,
                    "reason": "; ".join(row_errors),
                }
            )
        else:
            valid_indices.append(idx)

    valid_preds = (
        predict_fuzzy(df.iloc[valid_indices].copy(), fuzzy_bundle)
        if valid_indices
        else pd.DataFrame()
    )
    rejected_df = pd.DataFrame(rejected_records)
    return {
        "status": "ok",
        "errors": [],
        "total_rows": len(df),
        "valid_count": len(valid_indices),
        "rejected_count": len(rejected_records),
        "valid_predictions": valid_preds,
        "rejected_rows": rejected_df,
    }
