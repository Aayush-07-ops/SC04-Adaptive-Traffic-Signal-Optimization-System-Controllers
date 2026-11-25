# SC04 Step 3 - Adaptive Traffic Signal Fuzzy Logic Controller

## Goal
Build and evaluate the core Soft Computing controller for **SC04 - Adaptive Traffic Signal Optimization System**: a **Mamdani Fuzzy Logic Controller** (`scikit-fuzzy`) for one two-phase junction (`NS` and `EW`) that decides the next green phase and adaptive green duration (`10 s` to `60 s`), while enforcing emergency priority and strict input validation.

## Inputs and output
- **Inputs (7 traffic features from `docs/STEP-1.md` and `data/README.md`):**
  - `queue_ns`, `queue_ew`: approach queue lengths (vehicles, `0..100` allowed; `0..60` in Step 2 scenarios)
  - `density_ns_pct`, `density_ew_pct`: road space occupancy (`0..100` %)
  - `max_wait_ns_sec`, `max_wait_ew_sec`: longest waiting time (`0..300` s)
  - `emergency_direction`: `none`, `NS`, or `EW`
- **Outputs:**
  - `next_phase`: `NS` or `EW`
  - `green_duration_sec`: adaptive green duration clamped safely to `[10.0, 60.0]` seconds

## Fuzzy architecture
1. **Validation Gate:** Every input DataFrame is checked by `src/validate_data.py` (`check_dataframe`) before inference; missing or out-of-range rows are rejected immediately.
2. **Symmetric Mamdani Approach-Urgency FIS:**
   - Fuzzifies `queue` (`low`, `medium`, `high`), `density` (`low`, `medium`, `high`), and `wait` (`short`, `moderate`, `long`).
   - Evaluates 27 complete IF-THEN rules with centroid defuzzification to compute `urgency` (`0..100`) separately for `NS` and `EW`, giving strong starvation protection to long waiting times (e.g., `TRF-004`).
3. **Emergency Safety Override (Rule 4):** If `emergency_direction != "none"`, that direction immediately receives the next green phase.
4. **Mamdani Green-Duration FIS:** Uses the selected phase's `queue`, `density`, and `wait` across 27 complete rules (`very_short`, `short`, `medium`, `long`, `max_green`) to assign green time within `[10 s, 60 s]`.

## Data strategy and evaluation
- **Source data:** Uses only the validated 10,000 generated traffic scenarios from Step 2 (`data/generated/traffic_scenarios_10000.csv`), split reproducibly (`RANDOM_SEED = 42`, stratified by `scenario_type`) into:
  - `data/processed/train.csv` (`7,000` rows — 70%)
  - `data/processed/validation.csv` (`1,500` rows — 15%)
  - `data/processed/test.csv` (`1,500` rows — 15%, held out for final evaluation)
- **Results (against the transparent domain-priority reference `compute_reference_phase`):**
  - **Validation (`1,500` rows):** accuracy `0.8827`, NS precision `0.8687`, NS recall `0.9012`, NS F1 `0.8847`, macro F1 `0.8826`, emergency compliance `1.0`, green bounds compliance `1.0`, mean green `33.23 s`.
  - **Test (`1,500` rows):** accuracy `0.8827`, NS precision `0.8812`, NS recall `0.8947`, NS F1 `0.8879`, macro F1 `0.8824`, emergency compliance `1.0`, green bounds compliance `1.0`, mean green `33.26 s`.
  - **Test green duration by scenario type:** `normal` mean `27.49 s`, `difficult` mean `30.72 s`, `boundary` mean `35.99 s`, `emergency` mean `28.55 s`, `stress` mean `53.86 s` (adapting smoothly compared with the fixed `30 s` baseline).
  - **Mandatory & invalid checks:** All 5 mandatory cases (`TRF-001` to `TRF-005`) and all 20 starter cases (`data/sample_input.csv`) behave as expected; `data/invalid_input.csv` (`TRF-999`) and all `120/120` rows of `data/generated/invalid_test_scenarios.csv` are rejected.

## Evidence files
- Notebook (executed with outputs & plots): `notebooks/03_fuzzy_controller.ipynb`
- Repeatable script: `src/step3_fuzzy_controller.py`
- Dependencies: `requirements.txt`
- Processed splits: `data/processed/train.csv`, `data/processed/validation.csv`, `data/processed/test.csv`
- Reports & predictions: `data/reports/step3_fuzzy_metrics.csv`, `data/reports/step3_validation_predictions.csv`, `data/reports/step3_test_predictions.csv`, `data/reports/step3_sample_predictions.csv`
- Saved controller & metadata: `models/fuzzy_traffic_controller.pkl`, `models/fuzzy_controller_metadata.json`
- Figures:
  - `results/step3/step3_fuzzy_membership_functions.png`
  - `results/step3/step3_fuzzy_control_surface.png`
  - `results/step3/step3_validation_confusion_matrix.png`
  - `results/step3/step3_test_confusion_matrix.png`

## Limitations and safety rules
- **Simulated data only:** All 10,000 scenarios are synthetic states generated in Step 2; they are not real field traffic measurements.
- **No real-world ground-truth labels:** Because Step 2 generated input traffic states without observed optimal signal timings, classification metrics measure agreement with the formal multi-criteria priority specification rather than real-world traffic observations.
- **Scope limits:** Turning movements, pedestrians, amber/all-red clearance intervals, and multi-junction coordination are out of scope in M1.
- **Educational simulator only:** This controller is an educational Soft Computing model and must not be deployed to control real-world traffic hardware without physical calibration, safety certification, and field testing.
- **Next step (Step 4):** Compare this Mamdani Fuzzy Controller directly against the Step 1 fixed-time baseline (`src/baseline.py`) before moving to M2 Genetic Algorithm tuning.
