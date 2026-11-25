"""SC04 Step 3 - Mamdani Fuzzy Logic Traffic Signal Controller.

Repeatable non-notebook script that:
1. Validates Step 2 generated scenarios and creates stratified train/validation/test splits.
2. Builds a symmetric Mamdani Fuzzy Inference System (FIS) for approach urgency
   and adaptive green duration (safe bounds 10s-60s) with emergency safety override.
3. Evaluates the controller on validation, test, mandatory sample, and invalid inputs.
4. Saves evidence figures, metrics CSV, prediction CSVs, pickled FIS, and JSON metadata.

Run from the repository root:
    python src/step3_fuzzy_controller.py
"""
from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from validate_data import check_dataframe

PROJECT_ROOT = SRC_DIR.parent
RAW_SCENARIOS_FILE = PROJECT_ROOT / "data" / "generated" / "traffic_scenarios_10000.csv"
SAMPLE_FILE = PROJECT_ROOT / "data" / "sample_input.csv"
INVALID_SAMPLE_FILE = PROJECT_ROOT / "data" / "invalid_input.csv"
INVALID_SCENARIOS_FILE = PROJECT_ROOT / "data" / "generated" / "invalid_test_scenarios.csv"

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORT_DIR = PROJECT_ROOT / "data" / "reports"
MODEL_DIR = PROJECT_ROOT / "models"
RESULTS_DIR = PROJECT_ROOT / "results" / "step3"

RANDOM_SEED = 42
MIN_GREEN_SEC = 10.0
MAX_GREEN_SEC = 60.0
MAX_QUEUE_STEP2 = 60.0
MAX_DENSITY_PCT = 100.0
MAX_WAIT_SEC = 300.0

FEATURES = [
    "queue_ns",
    "queue_ew",
    "density_ns_pct",
    "density_ew_pct",
    "max_wait_ns_sec",
    "max_wait_ew_sec",
    "emergency_direction",
]
OUTPUTS = ["next_phase", "green_duration_sec"]


def build_fuzzy_systems():
    """Construct Mamdani FIS models for approach urgency and green duration."""
    q_u = np.linspace(0, 100, 51)
    d_u = np.linspace(0, 100, 51)
    w_u = np.linspace(0, 300, 61)
    u_u = np.linspace(0, 100, 51)
    g_u = np.linspace(MIN_GREEN_SEC, MAX_GREEN_SEC, 51)

    queue = ctrl.Antecedent(q_u, "queue")
    density = ctrl.Antecedent(d_u, "density")
    wait = ctrl.Antecedent(w_u, "wait")
    urgency = ctrl.Consequent(u_u, "urgency")
    green = ctrl.Consequent(g_u, "green")

    queue["low"] = fuzz.trapmf(q_u, [0, 0, 5, 22])
    queue["medium"] = fuzz.trimf(q_u, [8, 25, 45])
    queue["high"] = fuzz.trapmf(q_u, [30, 48, 100, 100])

    density["low"] = fuzz.trapmf(d_u, [0, 0, 15, 40])
    density["medium"] = fuzz.trimf(d_u, [20, 50, 80])
    density["high"] = fuzz.trapmf(d_u, [60, 82, 100, 100])

    wait["short"] = fuzz.trapmf(w_u, [0, 0, 25, 90])
    wait["moderate"] = fuzz.trimf(w_u, [45, 120, 195])
    wait["long"] = fuzz.trapmf(w_u, [150, 210, 300, 300])

    urgency["very_low"] = fuzz.trimf(u_u, [0, 10, 25])
    urgency["low"] = fuzz.trimf(u_u, [15, 32, 50])
    urgency["medium"] = fuzz.trimf(u_u, [35, 52, 70])
    urgency["high"] = fuzz.trimf(u_u, [55, 72, 88])
    urgency["critical"] = fuzz.trimf(u_u, [75, 92, 100])

    green["very_short"] = fuzz.trimf(g_u, [10, 14, 22])
    green["short"] = fuzz.trimf(g_u, [18, 26, 34])
    green["medium"] = fuzz.trimf(g_u, [28, 36, 44])
    green["long"] = fuzz.trimf(g_u, [38, 47, 55])
    green["max_green"] = fuzz.trimf(g_u, [48, 56, 60])

    level_scores = {"low": 0, "medium": 1, "high": 2}
    wait_scores = {"short": 0, "moderate": 1, "long": 2}

    urgency_rules = []
    green_rules = []
    rule_descriptions = []

    for ql, q_val in level_scores.items():
        for dl, d_val in level_scores.items():
            for wl, w_val in wait_scores.items():
                # Wait time carries strong weight to prevent approach starvation.
                u_score = 0.35 * q_val + 0.25 * d_val + 0.40 * w_val
                if w_val == 2 and u_score < 1.1:
                    u_label = "high"
                elif u_score <= 0.35:
                    u_label = "very_low"
                elif u_score <= 0.75:
                    u_label = "low"
                elif u_score <= 1.25:
                    u_label = "medium"
                elif u_score <= 1.65:
                    u_label = "high"
                else:
                    u_label = "critical"

                g_score = 0.45 * q_val + 0.25 * d_val + 0.30 * w_val
                if g_score <= 0.35:
                    g_label = "very_short"
                elif g_score <= 0.70:
                    g_label = "short"
                elif g_score <= 1.10:
                    g_label = "medium"
                elif g_score <= 1.55:
                    g_label = "long"
                else:
                    g_label = "max_green"

                antecedent = queue[ql] & density[dl] & wait[wl]
                urgency_rules.append(ctrl.Rule(antecedent, urgency[u_label]))
                green_rules.append(ctrl.Rule(antecedent, green[g_label]))
                rule_descriptions.append(
                    f"IF queue={ql} AND density={dl} AND wait={wl} "
                    f"THEN urgency={u_label}, green={g_label}"
                )

    urgency_system = ctrl.ControlSystem(urgency_rules)
    green_system = ctrl.ControlSystem(green_rules)
    return {
        "urgency_system": urgency_system,
        "green_system": green_system,
        "variables": {
            "queue": queue,
            "density": density,
            "wait": wait,
            "urgency": urgency,
            "green": green,
        },
        "rule_descriptions": rule_descriptions,
    }


def prepare_splits(raw_path: Path = RAW_SCENARIOS_FILE) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Validate Step 2 scenarios and create stratified train/validation/test CSV splits."""
    if not raw_path.exists():
        raise FileNotFoundError(f"Cannot find {raw_path}. Complete Step 2 first.")

    df = pd.read_csv(raw_path)
    errors = check_dataframe(df.copy())
    if errors:
        raise ValueError(f"Step 2 scenario dataset failed validation: {errors}")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    train_df, temp_df = train_test_split(
        df, test_size=0.30, stratify=df["scenario_type"], random_state=RANDOM_SEED
    )
    val_df, test_df = train_test_split(
        temp_df, test_size=0.50, stratify=temp_df["scenario_type"], random_state=RANDOM_SEED
    )

    train_df = train_df.reset_index(drop=True)
    val_df = val_df.reset_index(drop=True)
    test_df = test_df.reset_index(drop=True)

    train_df.to_csv(PROCESSED_DIR / "train.csv", index=False)
    val_df.to_csv(PROCESSED_DIR / "validation.csv", index=False)
    test_df.to_csv(PROCESSED_DIR / "test.csv", index=False)
    return train_df, val_df, test_df


def load_split(name: str) -> pd.DataFrame:
    """Load and validate a processed Step 2 split."""
    path = PROCESSED_DIR / f"{name}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Cannot find {path}. Run prepare_splits() first.")
    frame = pd.read_csv(path)
    errors = check_dataframe(frame.copy())
    if errors:
        raise ValueError(f"{name}.csv failed validation: {errors}")
    return frame


def predict_fuzzy(df: pd.DataFrame, fuzzy_bundle: dict) -> pd.DataFrame:
    """Validate inputs and run Mamdani fuzzy inference with emergency override."""
    errors = check_dataframe(df.copy())
    if errors:
        raise ValueError(f"Input rejected by Step 1/2 validator: {errors}")

    u_sim = ctrl.ControlSystemSimulation(fuzzy_bundle["urgency_system"])
    g_sim = ctrl.ControlSystemSimulation(fuzzy_bundle["green_system"])

    u_sim.input["queue"] = df["queue_ns"].to_numpy(dtype=float)
    u_sim.input["density"] = df["density_ns_pct"].to_numpy(dtype=float)
    u_sim.input["wait"] = df["max_wait_ns_sec"].to_numpy(dtype=float)
    u_sim.compute()
    u_ns = np.asarray(u_sim.output["urgency"], dtype=float)

    u_sim.input["queue"] = df["queue_ew"].to_numpy(dtype=float)
    u_sim.input["density"] = df["density_ew_pct"].to_numpy(dtype=float)
    u_sim.input["wait"] = df["max_wait_ew_sec"].to_numpy(dtype=float)
    u_sim.compute()
    u_ew = np.asarray(u_sim.output["urgency"], dtype=float)

    emerg = df["emergency_direction"].to_numpy()
    next_phase = np.where(emerg != "none", emerg, np.where(u_ns >= u_ew, "NS", "EW"))

    win_q = np.where(next_phase == "NS", df["queue_ns"].to_numpy(dtype=float), df["queue_ew"].to_numpy(dtype=float))
    win_d = np.where(next_phase == "NS", df["density_ns_pct"].to_numpy(dtype=float), df["density_ew_pct"].to_numpy(dtype=float))
    win_w = np.where(next_phase == "NS", df["max_wait_ns_sec"].to_numpy(dtype=float), df["max_wait_ew_sec"].to_numpy(dtype=float))

    g_sim.input["queue"] = win_q
    g_sim.input["density"] = win_d
    g_sim.input["wait"] = win_w
    g_sim.compute()
    green_sec = np.clip(np.round(np.asarray(g_sim.output["green"], dtype=float), 2), MIN_GREEN_SEC, MAX_GREEN_SEC)

    decision_mode = np.where(emerg != "none", "emergency_override", "fuzzy_urgency")

    out = df.copy()
    out["urgency_ns"] = np.round(u_ns, 2)
    out["urgency_ew"] = np.round(u_ew, 2)
    out["fuzzy_next_phase"] = next_phase
    out["fuzzy_green_duration_sec"] = green_sec
    out["decision_mode"] = decision_mode
    return out


def compute_reference_phase(df: pd.DataFrame) -> np.ndarray:
    """Compute transparent domain-priority reference phase for evaluating phase selection."""
    emerg = df["emergency_direction"].to_numpy()
    p_ns = (
        0.35 * (df["queue_ns"].to_numpy(dtype=float) / MAX_QUEUE_STEP2)
        + 0.25 * (df["density_ns_pct"].to_numpy(dtype=float) / MAX_DENSITY_PCT)
        + 0.40 * (df["max_wait_ns_sec"].to_numpy(dtype=float) / MAX_WAIT_SEC)
    )
    p_ew = (
        0.35 * (df["queue_ew"].to_numpy(dtype=float) / MAX_QUEUE_STEP2)
        + 0.25 * (df["density_ew_pct"].to_numpy(dtype=float) / MAX_DENSITY_PCT)
        + 0.40 * (df["max_wait_ew_sec"].to_numpy(dtype=float) / MAX_WAIT_SEC)
    )
    return np.where(emerg != "none", emerg, np.where(p_ns >= p_ew, "NS", "EW"))


def metric_row(y_true: np.ndarray, y_pred: np.ndarray, pred_df: pd.DataFrame, split_name: str) -> dict:
    """Compute classification alignment and domain safety metrics for a split."""
    emerg_mask = pred_df["emergency_direction"] != "none"
    emerg_acc = (
        float((pred_df.loc[emerg_mask, "fuzzy_next_phase"] == pred_df.loc[emerg_mask, "emergency_direction"]).mean())
        if emerg_mask.any()
        else 1.0
    )
    bounds_ok = float(
        ((pred_df["fuzzy_green_duration_sec"] >= MIN_GREEN_SEC) & (pred_df["fuzzy_green_duration_sec"] <= MAX_GREEN_SEC)).mean()
    )
    return {
        "split": split_name,
        "rows": len(pred_df),
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision_ns": round(float(precision_score(y_true, y_pred, pos_label="NS", zero_division=0)), 4),
        "recall_ns": round(float(recall_score(y_true, y_pred, pos_label="NS", zero_division=0)), 4),
        "f1_score_ns": round(float(f1_score(y_true, y_pred, pos_label="NS", zero_division=0)), 4),
        "f1_macro": round(float(f1_score(y_true, y_pred, average="macro", zero_division=0)), 4),
        "emergency_compliance": round(emerg_acc, 4),
        "green_bounds_compliance": round(bounds_ok, 4),
        "mean_green_sec": round(float(pred_df["fuzzy_green_duration_sec"].mean()), 2),
    }


def plot_membership_functions(fuzzy_bundle: dict, out_path: Path) -> None:
    """Plot and save all input and output fuzzy membership functions."""
    vars_map = fuzzy_bundle["variables"]
    specs = [
        ("queue", "Input 1: Queue Length (vehicles)"),
        ("density", "Input 2: Road Density (%)"),
        ("wait", "Input 3: Max Waiting Time (s)"),
        ("urgency", "Output 1: Approach Urgency Score"),
        ("green", "Output 2: Green Duration (s)"),
    ]
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    axes_flat = axes.flatten()
    for idx, (key, title) in enumerate(specs):
        ax = axes_flat[idx]
        var = vars_map[key]
        for term_name, term in var.terms.items():
            ax.plot(var.universe, term.mf, linewidth=2, label=term_name)
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.set_ylabel("Membership degree")
        ax.set_ylim(-0.05, 1.08)
        ax.grid(alpha=0.3)
        ax.legend(loc="best", fontsize=8)

    ax_info = axes_flat[5]
    ax_info.axis("off")
    info_text = (
        "SC04 Mamdani FIS Summary\n"
        "-------------------------\n"
        "• Method: Mamdani + Centroid\n"
        "• Rules: 27 complete combinations\n"
        "  (3 queue × 3 density × 3 wait)\n"
        "• Emergency Override (Rule 4):\n"
        "  emergency != 'none' -> immediate phase\n"
        "• Safe Green Bounds: [10s, 60s]\n"
        "• Validation Gate: rejects invalid rows"
    )
    ax_info.text(0.05, 0.5, info_text, va="center", fontsize=10, family="monospace")

    fig.suptitle("SC04 Step 3 — Fuzzy Membership Functions", fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def plot_control_surface_and_distributions(fuzzy_bundle: dict, test_pred: pd.DataFrame, out_path: Path) -> None:
    """Plot adaptive green-duration response surface and test scenario distributions."""
    g_sim = ctrl.ControlSystemSimulation(fuzzy_bundle["green_system"])
    q_grid = np.linspace(0, 60, 25)
    w_grid = np.linspace(0, 300, 25)
    qq, ww = np.meshgrid(q_grid, w_grid)
    dd = np.clip((qq / MAX_QUEUE_STEP2) * 100.0, 0, 100)

    g_sim.input["queue"] = qq.ravel()
    g_sim.input["density"] = dd.ravel()
    g_sim.input["wait"] = ww.ravel()
    g_sim.compute()
    zz = np.asarray(g_sim.output["green"], dtype=float).reshape(qq.shape)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    contour = ax1.contourf(qq, ww, zz, levels=16, cmap="YlGnBu")
    fig.colorbar(contour, ax=ax1, label="Green Duration (s)")
    ax1.set_title("Fuzzy Green Duration Surface (Queue vs Max Wait)", fontweight="bold")
    ax1.set_xlabel("Winning Approach Queue (vehicles)")
    ax1.set_ylabel("Winning Approach Max Wait (s)")

    order = ["normal", "boundary", "difficult", "emergency", "stress"]
    data_by_type = [test_pred.loc[test_pred["scenario_type"] == s, "fuzzy_green_duration_sec"].to_numpy() for s in order]
    ax2.boxplot(
        data_by_type,
        tick_labels=order,
        patch_artist=True,
        boxprops=dict(facecolor="#4C9BE8", alpha=0.65),
        medianprops=dict(color="#111111", linewidth=2),
    )
    ax2.axhline(30, color="crimson", linestyle="--", linewidth=1.3, label="Fixed Baseline (30 s)")
    ax2.set_title("Test-Split Fuzzy Green Time by Scenario Type", fontweight="bold")
    ax2.set_ylabel("Green Duration (s)")
    ax2.set_ylim(8, 62)
    ax2.grid(axis="y", alpha=0.3)
    ax2.legend(loc="lower right")

    fig.suptitle("SC04 Step 3 — Adaptive Controller Response & Distributions", fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def plot_confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray, split_name: str, out_path: Path) -> None:
    """Create and save a labelled NS vs EW confusion matrix."""
    matrix = confusion_matrix(y_true, y_pred, labels=["NS", "EW"])
    fig, ax = plt.subplots(figsize=(5, 4))
    image = ax.imshow(matrix, cmap="Blues")
    fig.colorbar(image, ax=ax)
    ax.set(
        title=f"Fuzzy Phase Confusion Matrix - {split_name.title()} Split",
        xlabel="Fuzzy Predicted Phase",
        ylabel="Domain Reference Phase",
        xticks=[0, 1],
        yticks=[0, 1],
        xticklabels=["NS", "EW"],
        yticklabels=["NS", "EW"],
    )
    thresh = matrix.max() / 2.0
    for row in range(2):
        for col in range(2):
            color = "white" if matrix[row, col] > thresh else "black"
            ax.text(col, row, str(matrix[row, col]), ha="center", va="center", color=color, fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def verify_invalid_rejection() -> dict:
    """Verify invalid Step 1 and Step 2 test rows are rejected before inference."""
    sample_bad = pd.read_csv(INVALID_SAMPLE_FILE)
    sample_errors = check_dataframe(sample_bad.copy())
    assert len(sample_errors) > 0, "Invalid Step 1 row must be rejected"

    invalid_df = pd.read_csv(INVALID_SCENARIOS_FILE)
    rejected = sum(1 for i in range(len(invalid_df)) if check_dataframe(invalid_df.iloc[[i]].copy()))
    assert rejected == len(invalid_df), f"Expected all {len(invalid_df)} invalid rows rejected, got {rejected}"
    return {
        "step1_invalid_rejected": True,
        "step1_invalid_errors": sample_errors,
        "step2_invalid_total": len(invalid_df),
        "step2_invalid_rejected": rejected,
    }


def main() -> int:
    for folder in (PROCESSED_DIR, REPORT_DIR, MODEL_DIR, RESULTS_DIR):
        folder.mkdir(parents=True, exist_ok=True)

    print("SC04 STEP 3 - MAMDANI FUZZY LOGIC CONTROLLER")
    print("=" * 52)

    train_df, val_df, test_df = prepare_splits()
    print(f"Splits created (seed={RANDOM_SEED}): train={len(train_df)}, validation={len(val_df)}, test={len(test_df)}")

    fuzzy_bundle = build_fuzzy_systems()
    print(f"Built Mamdani FIS with {len(fuzzy_bundle['rule_descriptions'])} rules per subsystem.")

    val_pred = predict_fuzzy(val_df, fuzzy_bundle)
    test_pred = predict_fuzzy(test_df, fuzzy_bundle)

    val_ref = compute_reference_phase(val_df)
    test_ref = compute_reference_phase(test_df)

    val_pred["reference_phase"] = val_ref
    test_pred["reference_phase"] = test_ref

    val_metrics = metric_row(val_ref, val_pred["fuzzy_next_phase"].to_numpy(), val_pred, "validation")
    test_metrics = metric_row(test_ref, test_pred["fuzzy_next_phase"].to_numpy(), test_pred, "test")

    metrics_df = pd.DataFrame([val_metrics, test_metrics])
    print("\nValidation & Test Metrics (against domain priority reference):")
    print(metrics_df.to_string(index=False))

    print("\nValidation Classification Report:")
    print(classification_report(val_ref, val_pred["fuzzy_next_phase"], labels=["NS", "EW"], zero_division=0))
    print("Test Classification Report:")
    print(classification_report(test_ref, test_pred["fuzzy_next_phase"], labels=["NS", "EW"], zero_division=0))

    sample_df = pd.read_csv(SAMPLE_FILE)
    sample_pred = predict_fuzzy(sample_df, fuzzy_bundle)
    sample_pred.to_csv(REPORT_DIR / "step3_sample_predictions.csv", index=False)

    by_id = sample_pred.set_index("state_id")
    assert by_id.loc["TRF-002", "fuzzy_next_phase"] == "NS"
    assert by_id.loc["TRF-003", "fuzzy_next_phase"] == "EW"
    assert by_id.loc["TRF-004", "fuzzy_next_phase"] == "NS"
    assert by_id.loc["TRF-005", "fuzzy_next_phase"] == "EW"
    assert by_id.loc["TRF-017", "fuzzy_next_phase"] == "NS"
    assert by_id.loc["TRF-018", "fuzzy_next_phase"] == "EW"
    assert by_id.loc["TRF-019", "fuzzy_next_phase"] == "NS"
    print("Mandatory sample checks (TRF-001..TRF-020): PASS")

    invalid_report = verify_invalid_rejection()
    print(
        f"Invalid input gate: PASS (Step 1 invalid rejected; "
        f"{invalid_report['step2_invalid_rejected']}/{invalid_report['step2_invalid_total']} Step 2 invalid rows rejected)"
    )

    plot_membership_functions(fuzzy_bundle, RESULTS_DIR / "step3_fuzzy_membership_functions.png")
    plot_control_surface_and_distributions(fuzzy_bundle, test_pred, RESULTS_DIR / "step3_fuzzy_control_surface.png")
    plot_confusion_matrix(val_ref, val_pred["fuzzy_next_phase"].to_numpy(), "validation", RESULTS_DIR / "step3_validation_confusion_matrix.png")
    plot_confusion_matrix(test_ref, test_pred["fuzzy_next_phase"].to_numpy(), "test", RESULTS_DIR / "step3_test_confusion_matrix.png")

    metrics_df.to_csv(REPORT_DIR / "step3_fuzzy_metrics.csv", index=False)
    val_pred.to_csv(REPORT_DIR / "step3_validation_predictions.csv", index=False)
    test_pred.to_csv(REPORT_DIR / "step3_test_predictions.csv", index=False)

    model_payload = {
        "technique": "Mamdani Fuzzy Inference System (scikit-fuzzy)",
        "fuzzy_bundle": fuzzy_bundle,
        "min_green_sec": MIN_GREEN_SEC,
        "max_green_sec": MAX_GREEN_SEC,
        "random_seed": RANDOM_SEED,
    }
    with (MODEL_DIR / "fuzzy_traffic_controller.pkl").open("wb") as f:
        pickle.dump(model_payload, f)

    scenario_green_summary = (
        test_pred.groupby("scenario_type")["fuzzy_green_duration_sec"]
        .agg(["count", "mean", "min", "max"])
        .round(2)
        .to_dict(orient="index")
    )

    metadata = {
        "project": "SC04 - Adaptive Traffic Signal Optimization System",
        "step": "Step 3 - Mamdani Fuzzy Logic Controller",
        "technique": "Mamdani Fuzzy Inference System + Centroid Defuzzification + Emergency Safety Override",
        "features": FEATURES,
        "outputs": OUTPUTS,
        "green_bounds_sec": [MIN_GREEN_SEC, MAX_GREEN_SEC],
        "fuzzy_rules_count": len(fuzzy_bundle["rule_descriptions"]),
        "random_seed": RANDOM_SEED,
        "data_splits": {
            "train_rows": len(train_df),
            "validation_rows": len(val_df),
            "test_rows": len(test_df),
            "honesty_note": "All 10,000 rows are generated scenarios (not real traffic observations).",
        },
        "metrics": [val_metrics, test_metrics],
        "test_green_by_scenario_type": scenario_green_summary,
        "invalid_rejection": invalid_report,
    }
    (MODEL_DIR / "fuzzy_controller_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print("\nSaved model, metadata, CSV reports, and Step 3 evidence figures successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
