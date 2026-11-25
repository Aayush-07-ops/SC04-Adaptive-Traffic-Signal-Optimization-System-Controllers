# SC04 — Step 4: Baseline vs Fuzzy Controller Comparison

> **Data disclaimer:** All 10 000 traffic scenarios in this project are
> synthetically generated for academic purposes. Results reflect performance
> on simulated data and do not represent real-world traffic measurements.

---

## 1. Goal

Compare the fixed-time **baseline controller** (Step 1) against the **Mamdani
Fuzzy Logic Controller** (Step 3) on the same held-out test split (1 500
scenarios) to quantify the improvement delivered by soft computing.

---

## 2. Controllers

### 2.1 Fixed-Time Baseline

| Property | Value |
|---|---|
| Phase selection | Alternates NS/EW by row index (even → NS, odd → EW) |
| Emergency override | Emergency direction always gets green |
| Green duration | Fixed **30 s** for every scenario |
| Adaptability | **None** — ignores queue length, density, wait time |

The baseline serves as the simplest possible rule-based controller and
represents the "do-nothing" state that smart controllers must beat.

### 2.2 Mamdani Fuzzy Logic Controller (Step 3)

| Property | Value |
|---|---|
| Architecture | Two-stage Mamdani FIS (urgency → phase; load → green) |
| Input variables | queue (NS/EW), density (NS/EW), max-wait (NS/EW), emergency_direction |
| Output variables | urgency score, green duration |
| Rules | 27 urgency rules + 27 green-duration rules per direction |
| Emergency override | Fuzzy inference bypassed; emergency direction always wins |
| Green duration range | [10, 60] s adaptive |

---

## 3. Evaluation Setup

| Item | Detail |
|---|---|
| Test split | 1 500 rows (15 % of 10 000, stratified, seed = 42) |
| Ground truth | `compute_reference_phase()`: priority score = 0.35×(queue/60) + 0.25×(density/100) + 0.40×(wait/300); higher-priority direction gets green |
| Metrics | Accuracy, Precision-NS, Recall-NS, F1-NS, F1-Macro, Emergency Compliance, Green Bounds Compliance, Mean/Std Green |
| Mandatory sample | `data/sample_input.csv` — 20 cases (TRF-001 … TRF-020) |

---

## 4. Results

### 4.1 Key Metrics (Test Split — 1 500 Scenarios)

| Metric | Fixed-Time Baseline | Mamdani Fuzzy | Improvement |
|---|---|---|---|
| **Phase Accuracy** | 0.5733 | **0.8827** | +31.0 pp |
| **F1-Macro** | 0.5732 | **0.8824** | +30.9 pp |
| Precision-NS | 0.5935 | 0.8812 | +28.8 pp |
| Recall-NS | 0.5661 | 0.8947 | +32.9 pp |
| F1-NS | 0.5795 | 0.8879 | +30.8 pp |
| Emergency Compliance | **1.0000** | **1.0000** | — (tied) |
| Green Bounds Compliance | 1.0000 | 1.0000 | — (tied) |
| Mean Green Duration (s) | 30.00 | 33.26 | Fuzzy adapts higher when needed |
| Std Green Duration (s) | **0.00** | **12.00** | Fuzzy adapts; baseline is rigid |
| Min Green (s) | 30.00 | 15.33 | Fuzzy reduces for low-load |
| Max Green (s) | 30.00 | 54.67 | Fuzzy extends for high-load |

### 4.2 Per-Scenario Accuracy

| Scenario Type | Baseline | Fuzzy | Improvement |
|---|---|---|---|
| normal | 0.521 | **0.932** | +41.1 pp |
| difficult | 0.502 | **0.582** | +8.0 pp |
| boundary | 0.760 | **0.916** | +15.6 pp |
| stress | 0.489 | **0.947** | +45.8 pp |
| emergency | **1.000** | **1.000** | — (tied) |

> **Key insight:** Baseline achieves 100 % on emergency only because emergency
> direction is a direct override in both methods. For non-emergency load-
> sensitive scenarios (normal, stress), the fuzzy controller shows the largest
> gains (+41 pp and +46 pp respectively).

### 4.3 Mandatory Sample — 20 Cases (TRF-001 … TRF-020)

| Metric | Fixed-Time Baseline | Mamdani Fuzzy |
|---|---|---|
| Sample Accuracy | 0.600 (12/20) | **1.000 (20/20)** |

The fuzzy controller correctly classifies all 20 mandatory test cases;
the baseline misclassifies 8 due to its rigid alternating rule.

---

## 5. Discussion

### Where the Baseline Fails

1. **Phase selection ignores traffic state.** A road with 50 vehicles waiting
   gets the same 30 s as one with 2 vehicles — alternating by row index is
   purely arbitrary.
2. **Green duration cannot respond to load.** Under heavy stress (60+ vehicles,
   density > 90 %, wait > 240 s), 30 s is insufficient. The fuzzy controller
   extends to ~55 s in such cases.
3. **Difficult scenarios are hardest for both.** When NS and EW loads are
   nearly equal, even the reference formula is uncertain, explaining why both
   controllers have lower accuracy on that scenario type.

### Why the Fuzzy Controller Wins

1. **Urgency-aware phase selection.** The 27-rule Mamdani FIS computes urgency
   from queue, density, and wait for each direction and always gives green to
   the more urgent direction.
2. **Adaptive green duration.** A second FIS maps input load to [10, 60] s
   green, reducing waste when queues are small and extending service when
   congestion is severe.
3. **Emergency safety is preserved.** The override gate ensures 100 %
   emergency compliance — no trade-off is needed.

### Limitations

- All data is **synthetic**; a real-world deployment would require sensor data,
  hardware integration, and safety certification beyond the scope of this
  capstone.
- The baseline alternates by **row index** (not clock time), which may differ
  from a real fixed-time controller cycling by wall-clock intervals.
- The "difficult" scenario gap (+8 pp) is small; future work could add more
  rules or increase antecedent granularity to improve edge-case decisions.

---

## 6. Evidence Files

| File | Description |
|---|---|
| `results/step4/step4_comparison_bar.png` | Grouped bar chart — key metrics baseline vs fuzzy |
| `results/step4/step4_green_duration_comparison.png` | Green duration boxplot by scenario + distribution |
| `results/step4/step4_phase_accuracy_by_scenario.png` | Per-scenario accuracy grouped bars |
| `results/step4/step4_comparison_metrics.csv` | Full metric table (2 rows × 12 metrics) |
| `results/step4/step4_baseline_predictions.csv` | Test split with both controllers' predictions |
| `results/step4/step4_sample_comparison.csv` | 20-case mandatory sample comparison |
| `data/reports/step4_comparison_metrics.csv` | Copy of metrics for reporting |
| `notebooks/04_baseline_comparison.ipynb` | Executed notebook with embedded figures |
| `src/compare_baseline.py` | Reproducible comparison script |

---

## 7. How to Reproduce

```bash
# From the repository root
python src/compare_baseline.py
```

Expected output: exits 0, prints comparison table, saves all 7 output files.
Requires: `scikit-fuzzy==0.5.0`, `scikit-learn==1.9.0`, `pandas`, `numpy`,
`matplotlib`, `scipy` (all in `requirements.txt`).

---

*SC04 — Adaptive Traffic Signal Optimization | Soft Computing Capstone*  
*Step 4 completed on branch `step-4-baseline`*
