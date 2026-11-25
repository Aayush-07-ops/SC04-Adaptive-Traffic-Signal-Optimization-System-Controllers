# SC04 — Step 5: Product V1 (Streamlit Interface + Saved Fuzzy Controller)

> **Data & Scope Disclaimer:** This application is an academic prototype
> evaluated on 10,000 synthetically generated traffic scenarios for an isolated
> two-phase (NS/EW) junction. It does not read live roadside sensors or control
> physical traffic signals, and no real-world safety or travel-time savings are
> claimed.

---

## 1. Overview & Architecture

Product V1 connects the interactive Streamlit interface (`app/app.py`) to the
saved Step 3 Mamdani Fuzzy Logic Controller (`models/fuzzy_traffic_controller.pkl`)
without re-training on prediction clicks.

| Layer | File | Responsibility |
|---|---|---|
| **UI** | `app/app.py` | 3-tab Streamlit interface: Single Signal Decision, Batch CSV Validation/Inference, and Time-Series Junction Simulation |
| **Service Layer** | `src/product_v1_service.py` | Loads saved `.pkl` + metadata, validates raw/CSV inputs, executes `predict_fuzzy()`, formats human-readable explanations & limitations |
| **Saved Model** | `models/fuzzy_traffic_controller.pkl` | Pickled Step 3 Mamdani FIS (`urgency_system` + `green_system`, 27 rules each) |
| **Validator** | `src/validate_data.py` | Shared Step 1/2/3 schema, type, range, and category checks |
| **Tests** | `src/test_step5_product_v1.py` | Automated verification across normal, boundary, invalid, missing-model, batch CSV, and UI-vs-code parity |

---

## 2. Reproducibility & How to Run Locally

- **Dependencies:** Listed in `requirements.txt` (includes `streamlit==1.67.0`, `scikit-fuzzy==0.5.0`, `scikit-learn==1.9.0`, `pandas==3.1.1`, `numpy==2.5.5`, `scipy==1.18.0`, `matplotlib==3.11.2`).
- **Entry-point file:** `app/app.py`
- **Start command (from repository root):**

```bash
streamlit run app/app.py
```

- **Local URL:** `http://localhost:8501`

To re-run the automated Step 5 verification suite:

```bash
python src/test_step5_product_v1.py
```

---

## 3. Input Validation & Output Readability

### Validated Input Ranges

| Field | Allowed Range / Values | Unit |
|---|---|---|
| `queue_ns`, `queue_ew` | `0` to `100` | vehicles |
| `density_ns_pct`, `density_ew_pct` | `0` to `100` | `%` |
| `max_wait_ns_sec`, `max_wait_ew_sec` | `0` to `300` | seconds |
| `emergency_direction` | `none`, `NS`, `EW` | category |

### Readable Output Provided in the UI

- **Next Green Phase** (`NS` or `EW`) plus plain-English action (`North-South (NS) gets GREEN; East-West (EW) holds RED`).
- **Green Duration** in **seconds**, bounded to `[10, 60] s`.
- **Fuzzy Urgency Scores** (`0–100`) for both NS and EW approaches.
- **Decision Mode** (`fuzzy_urgency` vs `emergency_override`).
- **Baseline Comparison** against the rigid `30 s` fixed-time baseline (`green_delta_vs_baseline_sec`).
- **Plain-English Explanation** and explicit **Limitations** notice.

---

## 4. Observed Test Evidence (`results/step5/step5_test_evidence.csv`)

All **17 / 17** automated checks passed (`failed_checks = 0`).

### 4.1 Normal Inputs

| Case ID | Scenario | Observed Output | Status |
|---|---|---|---|
| `NORM-01` | NS-heavy (`queue_ns=18, queue_ew=6, dens=45/20, wait=95/30, emerg=none`) | `phase=NS`, `green=32.84 s`, `mode=fuzzy_urgency` | PASS |
| `NORM-02` | EW-heavy (`queue_ns=5, queue_ew=28, dens=18/72, wait=25/160, emerg=none`) | `phase=EW`, `green=42.77 s`, `mode=fuzzy_urgency` | PASS |
| `NORM-03-EMERG` | EW congested but `emergency_direction=NS` | `phase=NS`, `green=15.33 s`, `mode=emergency_override` | PASS |

### 4.2 Boundary Inputs

| Case ID | Scenario | Observed Output | Status |
|---|---|---|---|
| `BND-01-ZERO` | All zeros (`0, 0, 0%, 0%, 0s, 0s`) | `phase=NS`, `green=15.33 s` (within `[10, 60] s`) | PASS |
| `BND-02-MAX-EW` | EW at max (`queue_ew=100, dens_ew=100%, wait_ew=300s`) | `phase=EW`, `green=54.67 s` (within `[10, 60] s`) | PASS |
| `BND-03-ALL-MAX` | Both directions at max (`100, 100%, 300s`) | `phase=NS`, `green=54.67 s` (symmetric tie-break) | PASS |

### 4.3 Invalid Inputs (Rejected Without Crashing)

| Case ID | Invalid Input | Observed Behaviour | Status |
|---|---|---|---|
| `INV-01-MISSING` | `queue_ns=""` (blank) | `status=validation_error`, explains missing value | PASS |
| `INV-02-NONNUM` | `queue_ew="abc"` | `status=validation_error`, explains non-numeric value | PASS |
| `INV-03-NEG-QUEUE` | `queue_ns=-5` | `status=validation_error`, explains out-of-range `[0, 100]` | PASS |
| `INV-04-HIGH-DENS` | `density_ns_pct=140` | `status=validation_error`, explains out-of-range `[0, 100] %` | PASS |
| `INV-05-HIGH-WAIT` | `max_wait_ns_sec=450` | `status=validation_error`, explains out-of-range `[0, 300] s` | PASS |
| `INV-06-BAD-EMERG` | `emergency_direction="BOTH"` | `status=validation_error`, explains allowed `{none, NS, EW}` | PASS |
| `INV-07-NAN` | `density_ew_pct="nan"` | `status=validation_error`, rejects non-finite value | PASS |

### 4.4 Missing-Model, UI-vs-Code Parity & Batch CSV Checks

| Case ID | Check | Observed Result | Status |
|---|---|---|---|
| `MOD-01-MISSING` | Non-existent `.pkl` model path | `status=model_error` with clear regeneration instructions; no crash | PASS |
| `PARITY-01` | UI service (`predict_single_state`) vs direct `predict_fuzzy()` on 5 rows | `0 mismatches` on phase, green duration, and urgency scores | PASS |
| `BATCH-01-SAMPLE` | Batch CSV on `data/sample_input.csv` | `20` valid predicted, `0` rejected | PASS |
| `BATCH-02-INVALID` | Batch CSV on `data/generated/invalid_test_scenarios.csv` | `0` valid, `120` invalid rows rejected with per-row reasons | PASS |

---

## 5. Addressed Earlier Feedback & Limitations

- **Earlier Step 3/4 alignment:** Kept `src/fuzzy_controller.py` (Step 2 simulator helper) intact while connecting the UI directly to the Step 3 Mamdani FIS (`models/fuzzy_traffic_controller.pkl`) and reusing `src/validate_data.py`.
- **Training separated from inference:** `app/app.py` only loads the saved `.pkl` model; no training or data generation runs inside UI prediction buttons.
- **Limitations:** Synthetic dataset only; isolated 2-phase junction without multi-intersection coordination, pedestrian phases, or hardware sensor integration.

---

## 6. Evidence Files

| File | Description |
|---|---|
| `app/app.py` | Streamlit Product V1 application |
| `src/product_v1_service.py` | Model loader, input validator, readable inference & batch CSV service |
| `src/test_step5_product_v1.py` | Automated Step 5 verification suite |
| `results/step5/step5_test_evidence.csv` | Row-by-row test evidence (17 checks) |
| `results/step5/step5_test_summary.json` | Aggregated pass/fail summary |
| `docs/STEP-5.md` | Step 5 report |
