"""
SC04 – Adaptive Traffic Signal Optimization
Step 4: Baseline vs Fuzzy Controller Comparison
================================================
Compares the fixed-time baseline (Step 1) against the Mamdani Fuzzy Logic
Controller (Step 3) on the held-out test split (1 500 rows, seed=42).

Outputs
-------
results/step4/step4_baseline_predictions.csv
results/step4/step4_comparison_metrics.csv
results/step4/step4_sample_comparison.csv
results/step4/step4_comparison_bar.png
results/step4/step4_green_duration_comparison.png
results/step4/step4_phase_accuracy_by_scenario.png
data/reports/step4_comparison_metrics.csv

NOTE: All 10 000 scenarios in this project are synthetically generated for
academic purposes and do not represent real-world traffic measurements.
"""

from __future__ import annotations

import os
import sys
import warnings
import pathlib
import pickle
import textwrap
from typing import Dict, Any

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, ConfusionMatrixDisplay,
)

# ── project root ──────────────────────────────────────────────────────────────
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

warnings.filterwarnings("ignore")

# ── constants ─────────────────────────────────────────────────────────────────
FIXED_GREEN_SEC   = 30.0
GREEN_MIN         = 10.0
GREEN_MAX         = 60.0
RESULTS_DIR       = ROOT / "results" / "step4"
REPORTS_DIR       = ROOT / "data" / "reports"
DATA_DIR          = ROOT / "data" / "processed"
SAMPLE_INPUT_PATH = ROOT / "data" / "sample_input.csv"
MODEL_PATH        = ROOT / "models" / "fuzzy_traffic_controller.pkl"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ══════════════════════════════════════════════════════════════════════════════
# 1. IMPORT STEP-3 HELPERS
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 65)
print("SC04 Step 4 — Baseline vs Fuzzy Controller Comparison")
print("=" * 65)

# Import the functions we need from step3_fuzzy_controller
import importlib.util
_spec = importlib.util.spec_from_file_location(
    "step3_fuzzy_controller",
    ROOT / "src" / "step3_fuzzy_controller.py",
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

load_split              = _mod.load_split
compute_reference_phase = _mod.compute_reference_phase
predict_fuzzy           = _mod.predict_fuzzy
FEATURES                = _mod.FEATURES

print("\n[1] Loading test split …")
test_df = load_split("test")
print(f"    Rows: {len(test_df)}")
print(f"    Scenario types: {test_df['scenario_type'].value_counts().to_dict()}")


# ══════════════════════════════════════════════════════════════════════════════
# 2. LOAD FUZZY BUNDLE
# ══════════════════════════════════════════════════════════════════════════════
print("\n[2] Loading fuzzy controller bundle …")
with open(MODEL_PATH, "rb") as fh:
    _raw_bundle: Dict[str, Any] = pickle.load(fh)
# The pkl stores {'fuzzy_bundle': {...}, 'technique': ..., ...}
fuzzy_bundle: Dict[str, Any] = _raw_bundle.get("fuzzy_bundle", _raw_bundle)
print("    Bundle loaded OK")


# ══════════════════════════════════════════════════════════════════════════════
# 3. DOMAIN REFERENCE (ground truth)
# ══════════════════════════════════════════════════════════════════════════════
print("\n[3] Computing domain reference phases …")
ref_phase = compute_reference_phase(test_df)
print(f"    NS: {(ref_phase == 'NS').sum()}  EW: {(ref_phase == 'EW').sum()}")


# ══════════════════════════════════════════════════════════════════════════════
# 4. FIXED-TIME BASELINE PREDICTIONS
# ══════════════════════════════════════════════════════════════════════════════
print("\n[4] Computing fixed-time baseline predictions …")

def predict_baseline(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fixed-time baseline (Step 1 logic):
      • Phase alternates by row index: even → NS, odd → EW
      • Emergency override: if emergency_direction != 'none' → that direction
      • Green duration: always FIXED_GREEN_SEC (30 s) regardless of load
    """
    n = len(df)
    idx_array = np.arange(n)

    # Default alternating phase
    phase = np.where(idx_array % 2 == 0, "NS", "EW")

    # Emergency override
    emerg = df["emergency_direction"].values
    has_emerg = emerg != "none"
    phase = np.where(has_emerg, emerg, phase)

    # Green duration always fixed
    green = np.full(n, FIXED_GREEN_SEC)

    _keep = [c for c in ["state_id", "scenario_type", "emergency_direction"]
              if c in df.columns]
    out = df[_keep].copy()
    out["baseline_phase"]      = phase
    out["baseline_green_sec"]  = green
    return out

baseline_preds = predict_baseline(test_df)
baseline_preds["reference_phase"] = ref_phase if isinstance(ref_phase, np.ndarray) else ref_phase.values

# Emergency compliance for baseline
emerg_mask = test_df["emergency_direction"].values != "none"
emerg_correct = (
    baseline_preds.loc[emerg_mask, "baseline_phase"].values
    == test_df.loc[emerg_mask, "emergency_direction"].values
)
baseline_emerg_compliance = emerg_correct.mean() if emerg_mask.sum() > 0 else 1.0
baseline_phase_acc = accuracy_score(ref_phase, baseline_preds["baseline_phase"])

print(f"    Baseline phase accuracy : {baseline_phase_acc:.4f}")
print(f"    Baseline emerg compliance: {baseline_emerg_compliance:.4f}")


# ══════════════════════════════════════════════════════════════════════════════
# 5. FUZZY CONTROLLER PREDICTIONS
# ══════════════════════════════════════════════════════════════════════════════
print("\n[5] Running fuzzy controller on test split (this may take ~30 s) …")
fuzzy_preds_df = predict_fuzzy(test_df, fuzzy_bundle)
fuzzy_phase    = fuzzy_preds_df["fuzzy_next_phase"].values
fuzzy_green    = fuzzy_preds_df["fuzzy_green_duration_sec"].values

fuzzy_phase_acc = accuracy_score(ref_phase, fuzzy_phase)
fuzzy_emerg_preds = fuzzy_preds_df.loc[emerg_mask, "fuzzy_next_phase"].values
fuzzy_emerg_true  = test_df.loc[emerg_mask, "emergency_direction"].values
fuzzy_emerg_compliance = (
    (fuzzy_emerg_preds == fuzzy_emerg_true).mean()
    if emerg_mask.sum() > 0 else 1.0
)
fuzzy_green_bounds = (
    ((fuzzy_green >= GREEN_MIN - 0.01) & (fuzzy_green <= GREEN_MAX + 0.01)).mean()
)

print(f"    Fuzzy phase accuracy    : {fuzzy_phase_acc:.4f}")
print(f"    Fuzzy emerg compliance  : {fuzzy_emerg_compliance:.4f}")
print(f"    Fuzzy green bounds OK   : {fuzzy_green_bounds:.4f}")


# ══════════════════════════════════════════════════════════════════════════════
# 6. METRIC HELPER
# ══════════════════════════════════════════════════════════════════════════════
def compute_metrics(name: str, pred_phase, true_phase,
                    green_arr, emerg_compliance: float) -> dict:
    acc  = accuracy_score(true_phase, pred_phase)
    prec = precision_score(true_phase, pred_phase, pos_label="NS",
                           zero_division=0)
    rec  = recall_score(true_phase, pred_phase, pos_label="NS",
                        zero_division=0)
    f1_ns  = f1_score(true_phase, pred_phase, pos_label="NS", zero_division=0)
    f1_mac = f1_score(true_phase, pred_phase, average="macro", zero_division=0)
    gbc    = ((green_arr >= GREEN_MIN - 0.01) & (green_arr <= GREEN_MAX + 0.01)).mean()
    return {
        "model":                 name,
        "accuracy":              round(acc, 4),
        "precision_NS":          round(prec, 4),
        "recall_NS":             round(rec, 4),
        "f1_NS":                 round(f1_ns, 4),
        "f1_macro":              round(f1_mac, 4),
        "emergency_compliance":  round(emerg_compliance, 4),
        "green_bounds_compliance": round(gbc, 4),
        "mean_green_sec":        round(float(green_arr.mean()), 4),
        "std_green_sec":         round(float(green_arr.std()), 4),
        "min_green_sec":         round(float(green_arr.min()), 4),
        "max_green_sec":         round(float(green_arr.max()), 4),
    }

ref_phase_arr = np.asarray(ref_phase)

baseline_metrics = compute_metrics(
    "Fixed-Time Baseline",
    baseline_preds["baseline_phase"].values,
    ref_phase_arr,
    baseline_preds["baseline_green_sec"].values,
    baseline_emerg_compliance,
)
fuzzy_metrics = compute_metrics(
    "Mamdani Fuzzy Controller",
    fuzzy_phase,
    ref_phase_arr,
    fuzzy_green,
    fuzzy_emerg_compliance,
)

metrics_df = pd.DataFrame([baseline_metrics, fuzzy_metrics])
print("\n" + "=" * 65)
print("COMPARISON METRICS")
print("=" * 65)
print(metrics_df.to_string(index=False))


# ══════════════════════════════════════════════════════════════════════════════
# 7. PER-SCENARIO ACCURACY
# ══════════════════════════════════════════════════════════════════════════════
print("\n[6] Per-scenario accuracy …")
scenario_types = test_df["scenario_type"].unique()
scenario_acc = {}
for sc in sorted(scenario_types):
    mask = test_df["scenario_type"] == sc
    b_acc = accuracy_score(ref_phase[mask], baseline_preds["baseline_phase"][mask])
    f_acc = accuracy_score(ref_phase[mask], fuzzy_phase[mask])
    scenario_acc[sc] = {"baseline": round(b_acc, 4), "fuzzy": round(f_acc, 4)}
    print(f"    {sc:12s}  baseline={b_acc:.3f}  fuzzy={f_acc:.3f}")


# ══════════════════════════════════════════════════════════════════════════════
# 8. SAMPLE CASE-BY-CASE COMPARISON (20 mandatory cases)
# ══════════════════════════════════════════════════════════════════════════════
print("\n[7] Sample comparison on 20 mandatory cases …")
if SAMPLE_INPUT_PATH.exists():
    sample_df = pd.read_csv(SAMPLE_INPUT_PATH)
else:
    # Fall back to first 20 rows of test split
    print("    sample_input.csv not found — using first 20 rows of test split")
    sample_df = test_df.head(20).reset_index(drop=True)

# Ensure state_id exists
if "state_id" not in sample_df.columns:
    sample_df["state_id"] = [f"S{i+1:03d}" for i in range(len(sample_df))]

sample_ref   = compute_reference_phase(sample_df)
sample_base  = predict_baseline(sample_df)
sample_fuzzy = predict_fuzzy(sample_df, fuzzy_bundle)

sample_cmp = pd.DataFrame({
    "state_id":          sample_df["state_id"].values,
    "scenario_type":     sample_df["scenario_type"].values if "scenario_type" in sample_df.columns else ["unknown"] * len(sample_df),
    "emergency_dir":     sample_df["emergency_direction"].values,
    "correct_phase":     np.asarray(sample_ref),
    "baseline_phase":    sample_base["baseline_phase"].values,
    "fuzzy_phase":       sample_fuzzy["fuzzy_next_phase"].values,
    "baseline_green":    sample_base["baseline_green_sec"].values,
    "fuzzy_green":       sample_fuzzy["fuzzy_green_duration_sec"].values,
    "baseline_correct":  (sample_base["baseline_phase"].values == np.asarray(sample_ref)),
    "fuzzy_correct":     (sample_fuzzy["fuzzy_next_phase"].values == np.asarray(sample_ref)),
})

b_sample_acc = sample_cmp["baseline_correct"].mean()
f_sample_acc = sample_cmp["fuzzy_correct"].mean()
print(f"    Sample baseline accuracy : {b_sample_acc:.3f}")
print(f"    Sample fuzzy accuracy    : {f_sample_acc:.3f}")
print(sample_cmp[["state_id", "correct_phase", "baseline_phase",
                   "fuzzy_phase", "baseline_correct", "fuzzy_correct"]].to_string(index=False))


# ══════════════════════════════════════════════════════════════════════════════
# 9. SAVE CSVs
# ══════════════════════════════════════════════════════════════════════════════
print("\n[8] Saving CSVs …")

# Full test split with both baseline and fuzzy predictions
full_pred = test_df[["state_id", "scenario_type", "emergency_direction"]].copy()
full_pred["reference_phase"]   = ref_phase_arr
full_pred["baseline_phase"]    = baseline_preds["baseline_phase"].values
full_pred["baseline_green"]    = baseline_preds["baseline_green_sec"].values
full_pred["fuzzy_phase"]       = fuzzy_phase
full_pred["fuzzy_green"]       = fuzzy_green
full_pred["baseline_correct"]  = full_pred["baseline_phase"] == full_pred["reference_phase"]
full_pred["fuzzy_correct"]     = full_pred["fuzzy_phase"] == full_pred["reference_phase"]

full_pred.to_csv(RESULTS_DIR / "step4_baseline_predictions.csv", index=False)
print(f"    Saved {RESULTS_DIR / 'step4_baseline_predictions.csv'}")

metrics_df.to_csv(RESULTS_DIR / "step4_comparison_metrics.csv", index=False)
print(f"    Saved {RESULTS_DIR / 'step4_comparison_metrics.csv'}")

metrics_df.to_csv(REPORTS_DIR / "step4_comparison_metrics.csv", index=False)
print(f"    Saved {REPORTS_DIR / 'step4_comparison_metrics.csv'}")

sample_cmp.to_csv(RESULTS_DIR / "step4_sample_comparison.csv", index=False)
print(f"    Saved {RESULTS_DIR / 'step4_sample_comparison.csv'}")


# ══════════════════════════════════════════════════════════════════════════════
# 10. FIGURES
# ══════════════════════════════════════════════════════════════════════════════
print("\n[9] Generating figures …")

# ── Figure 1: Grouped bar chart – key metrics ─────────────────────────────────
metrics_to_plot = ["accuracy", "f1_macro", "emergency_compliance", "green_bounds_compliance"]
labels          = ["Accuracy", "F1-Macro", "Emergency\nCompliance", "Green Bounds\nCompliance"]
bvals = [baseline_metrics[m] for m in metrics_to_plot]
fvals = [fuzzy_metrics[m]    for m in metrics_to_plot]

x     = np.arange(len(labels))
width = 0.35

fig, ax = plt.subplots(figsize=(10, 6))
bars_b = ax.bar(x - width/2, bvals, width, label="Fixed-Time Baseline",
                color="#e74c3c", alpha=0.85, edgecolor="black", linewidth=0.8)
bars_f = ax.bar(x + width/2, fvals, width, label="Mamdani Fuzzy Controller",
                color="#2ecc71", alpha=0.85, edgecolor="black", linewidth=0.8)

ax.bar_label(bars_b, fmt="%.3f", padding=3, fontsize=10, fontweight="bold")
ax.bar_label(bars_f, fmt="%.3f", padding=3, fontsize=10, fontweight="bold")

ax.set_xlabel("Metric", fontsize=12)
ax.set_ylabel("Score (0–1)", fontsize=12)
ax.set_title("SC04 Step 4: Baseline vs Fuzzy Controller\n(Held-Out Test Split, 1 500 Scenarios)",
             fontsize=13, fontweight="bold")
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=11)
ax.set_ylim(0, 1.15)
ax.legend(fontsize=11)
ax.grid(axis="y", linestyle="--", alpha=0.5)
plt.tight_layout()
fig.savefig(RESULTS_DIR / "step4_comparison_bar.png", dpi=150)
plt.close(fig)
print(f"    Saved {RESULTS_DIR / 'step4_comparison_bar.png'}")

# ── Figure 2: Green duration comparison ──────────────────────────────────────
scenario_order = sorted(test_df["scenario_type"].unique())
fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharey=False)

# Left: boxplot per scenario (fuzzy) + flat line (baseline)
fuzzy_by_sc = [fuzzy_green[test_df["scenario_type"].values == sc]
               for sc in scenario_order]
bp = axes[0].boxplot(fuzzy_by_sc, tick_labels=scenario_order, patch_artist=True,
                     medianprops={"color": "black", "linewidth": 2})
for patch in bp["boxes"]:
    patch.set_facecolor("#2ecc71")
    patch.set_alpha(0.75)
axes[0].axhline(FIXED_GREEN_SEC, color="#e74c3c", linewidth=2.5,
                linestyle="--", label=f"Baseline (fixed {FIXED_GREEN_SEC:.0f} s)")
axes[0].set_title("Green Duration by Scenario Type", fontsize=12, fontweight="bold")
axes[0].set_xlabel("Scenario Type", fontsize=11)
axes[0].set_ylabel("Green Duration (seconds)", fontsize=11)
axes[0].legend(fontsize=10)
axes[0].tick_params(axis="x", rotation=20)
axes[0].grid(axis="y", linestyle="--", alpha=0.5)

# Right: overall distribution overlay
axes[1].hist(fuzzy_green, bins=30, alpha=0.7, color="#2ecc71", label="Fuzzy Controller",
             edgecolor="black", linewidth=0.6)
axes[1].axvline(FIXED_GREEN_SEC, color="#e74c3c", linewidth=2.5,
                linestyle="--", label=f"Baseline = {FIXED_GREEN_SEC:.0f} s (all)")
axes[1].set_title("Distribution of Green Duration (Test Split)", fontsize=12, fontweight="bold")
axes[1].set_xlabel("Green Duration (seconds)", fontsize=11)
axes[1].set_ylabel("Count", fontsize=11)
axes[1].legend(fontsize=10)
axes[1].grid(axis="y", linestyle="--", alpha=0.5)

plt.suptitle("SC04 Step 4: Green Duration — Fixed-Time Baseline vs Fuzzy Controller",
             fontsize=12, fontweight="bold", y=1.01)
plt.tight_layout()
fig.savefig(RESULTS_DIR / "step4_green_duration_comparison.png", dpi=150,
            bbox_inches="tight")
plt.close(fig)
print(f"    Saved {RESULTS_DIR / 'step4_green_duration_comparison.png'}")

# ── Figure 3: Phase accuracy per scenario ────────────────────────────────────
sc_names = sorted(scenario_acc.keys())
b_accs   = [scenario_acc[s]["baseline"] for s in sc_names]
f_accs   = [scenario_acc[s]["fuzzy"]    for s in sc_names]

x     = np.arange(len(sc_names))
width = 0.35

fig, ax = plt.subplots(figsize=(11, 6))
bb = ax.bar(x - width/2, b_accs, width, label="Fixed-Time Baseline",
            color="#e74c3c", alpha=0.85, edgecolor="black", linewidth=0.8)
fb = ax.bar(x + width/2, f_accs, width, label="Mamdani Fuzzy Controller",
            color="#2ecc71", alpha=0.85, edgecolor="black", linewidth=0.8)

ax.bar_label(bb, fmt="%.3f", padding=3, fontsize=9, fontweight="bold")
ax.bar_label(fb, fmt="%.3f", padding=3, fontsize=9, fontweight="bold")

ax.set_xlabel("Scenario Type", fontsize=12)
ax.set_ylabel("Phase Accuracy", fontsize=12)
ax.set_title("SC04 Step 4: Phase Accuracy per Scenario Type\n(Fixed-Time Baseline vs Fuzzy Controller)",
             fontsize=13, fontweight="bold")
ax.set_xticks(x)
ax.set_xticklabels([s.capitalize() for s in sc_names], fontsize=11)
ax.set_ylim(0, 1.18)
ax.legend(fontsize=11)
ax.grid(axis="y", linestyle="--", alpha=0.5)
plt.tight_layout()
fig.savefig(RESULTS_DIR / "step4_phase_accuracy_by_scenario.png", dpi=150)
plt.close(fig)
print(f"    Saved {RESULTS_DIR / 'step4_phase_accuracy_by_scenario.png'}")


# ══════════════════════════════════════════════════════════════════════════════
# 11. PRINT SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 65)
print("STEP 4 SUMMARY")
print("=" * 65)
improvement_acc  = fuzzy_metrics["accuracy"]  - baseline_metrics["accuracy"]
improvement_f1   = fuzzy_metrics["f1_macro"]  - baseline_metrics["f1_macro"]
print(f"\n  Phase accuracy  : Baseline={baseline_metrics['accuracy']:.4f}  "
      f"Fuzzy={fuzzy_metrics['accuracy']:.4f}  Δ=+{improvement_acc:.4f}")
print(f"  F1-Macro        : Baseline={baseline_metrics['f1_macro']:.4f}  "
      f"Fuzzy={fuzzy_metrics['f1_macro']:.4f}  Δ=+{improvement_f1:.4f}")
print(f"  Emerg. Compl.   : Baseline={baseline_metrics['emergency_compliance']:.4f}  "
      f"Fuzzy={fuzzy_metrics['emergency_compliance']:.4f}")
print(f"  Mean Green (s)  : Baseline={baseline_metrics['mean_green_sec']:.2f}  "
      f"Fuzzy={fuzzy_metrics['mean_green_sec']:.2f}")
print(f"  Green Std  (s)  : Baseline={baseline_metrics['std_green_sec']:.2f}  "
      f"Fuzzy={fuzzy_metrics['std_green_sec']:.2f}")
print(f"\n  Fuzzy improves phase accuracy by "
      f"{improvement_acc*100:.1f} percentage points over the fixed-time baseline.")
print(f"\n  All output files saved to: {RESULTS_DIR}")
print("\n[DONE] Step 4 comparison complete.")
