# Step 6 - Testing and validation

## Project and environment

- Project: SC04 - Adaptive Traffic Signal Optimization System.
- Branch: `step-6-testing`.
- Commit tested: `a6d6d42` (starting point from `step-5-product-v1`).
- Python and dependencies: `Python 3.14.3` with `streamlit==1.67.0`, `scikit-fuzzy==0.5.0`, `scikit-learn==1.9.0`, `pandas==3.1.1`, `numpy==2.5.5`, `scipy==1.18.0` (see `requirements.txt`).
- Launch from the repository root: `python -m streamlit run app/app.py`.
- Reference input: first data row in `data/processed/validation.csv` (`SCN-00773`: `queue_ns=9`, `queue_ew=39`, `density_ns_pct=9.7`, `density_ew_pct=61.1`, `max_wait_ns_sec=297`, `max_wait_ew_sec=128`, `emergency_direction=none`).

## Planned tests and results

Keep the other six input fields fixed when testing a single input. `PASS` means the app or script behaved as expected (including rejecting invalid inputs with a clear message and withholding the prediction).

| ID | Input or action | Expected behaviour | Actual result | Status |
| --- | --- | --- | --- | --- |
| T01 | Run normal reference input (`SCN-00773`) through saved fuzzy model | Display phase (`NS`/`EW`), green duration in `[10, 60] s`, urgency scores, and limitations notice. | Returned `phase=NS`, `green=26.93 s`, `urgency=(69.76, 63.71)`, `mode=fuzzy_urgency`, and limitations notice. | PASS |
| T02 | Set NS lower limits (`queue_ns=0`, `density_ns_pct=0`, `max_wait_ns_sec=0`) | Accept lower limits and display a valid signal plan. | Accepted all zero limits; returned `phase=EW`, `green=43.03 s` (within `[10, 60] s`). | PASS |
| T03 | Set NS upper limits (`queue_ns=100`, `density_ns_pct=100`, `max_wait_ns_sec=300`) | Accept upper limits and display a valid signal plan. | Accepted all upper limits; returned `phase=NS`, `green=54.67 s` (within `[10, 60] s`). | PASS |
| T04 | Set `density_ns_pct=140` (above 100%), `max_wait_ns_sec=450`, or `queue_ns=-5` | Show allowed range message and withhold prediction. | Displayed `'density_ns_pct: 140 % is out of range (allowed: 0 to 100 %).'`, withheld prediction (`status=validation_error`). | PASS |
| T05 | Enter text `abc` in `queue_ew` | Ask for a valid number and withhold prediction. | Displayed `"queue_ew: 'abc' is not a valid number."`, withheld prediction (`status=validation_error`). | PASS |
| T06 | Leave required field `queue_ns` blank (`""`) | Ask for the missing value and withhold prediction. | Displayed `'queue_ns: value is missing (expected 0 to 100 vehicles).'`, withheld prediction (`status=validation_error`). | PASS |
| T07 | Call prediction with missing model path (`models/missing_model_step6_test.pkl`) | Explain that the saved model file is missing and stop before prediction without crashing. | Returned `status=model_error` with `"Saved fuzzy controller file not found ... Run python src/step3_fuzzy_controller.py"`. | PASS |
| T08 | Restore valid saved model path (`models/fuzzy_traffic_controller.pkl`) and retry `T01` | Normal reference input predicts again with identical output. | Returned `status=ok`, `phase=NS`, `green=26.93 s`. | PASS |
| T09 | Run `python src/compare_step6_predictions.py` on `step5_ui_reference_prediction.csv` vs `step6_ui_prediction.csv` | All 7 inputs, `fuzzy_next_phase`, `fuzzy_green_duration_sec`, `urgency_ns`, `urgency_ew`, and `decision_mode` match. | Printed `PASS: All seven inputs, next phase, green duration, and urgency scores match.` (`SCN-00773`). | PASS |
| T10 | Run `python -m unittest -v src/test_step6_validation.py` (includes 27-rule corner coverage + bounds) | All 9 automated unit tests run and finish with `OK`. | Ran 9 tests in `1.231s`, all passed (`OK`), including all 27 rule-grid corners within `[10, 60] s`. | PASS |

## Evidence

| Test ID | File path or exact observed output |
| --- | --- |
| T01 | `data/reports/step6_ui_prediction.csv` (`SCN-00773`, `phase=NS`, `green=26.93 s`, `urgency=(69.76, 63.71)`) |
| T02–T03 | `src/test_step6_validation.py` (`test_t02_lower_boundary` -> `EW 43.03 s`; `test_t03_upper_boundary` -> `NS 54.67 s`) |
| T04–T06 | `results/step5/step5_ui_invalid.png` and `src/test_step6_validation.py` (`validation_error` returned and prediction withheld) |
| T07–T08 | `src/test_step6_validation.py` (`test_t07_t08_missing_model_and_recovery` -> `model_error` then recovered `ok`) |
| T09 | `python src/compare_step6_predictions.py` comparing `data/reports/step5_ui_reference_prediction.csv` and `data/reports/step6_ui_prediction.csv` -> `PASS` |
| T10 | `python -m unittest -v src/test_step6_validation.py` -> `Ran 9 tests in 1.231s` / `OK` |

## Failures, fixes and retests

| Test ID | What failed | What changed and where | Result of repeating the case and a normal case |
| --- | --- | --- | --- |
| None (app code) | No functional defects occurred in `app/app.py` or `src/product_v1_service.py` during Step 6 testing. | Added dedicated Step 6 scripts (`src/compare_step6_predictions.py`, `src/test_step6_validation.py`) to verify CSV parity and 27-rule corner coverage in `unittest`. | Re-ran `compare_step6_predictions.py` (`PASS`) and `unittest` (`Ran 9 tests in 1.231s`, `OK`). |

*(Note: `scikit-fuzzy` emits a NumPy `DeprecationWarning` inside `controlsystem.py` for multi-argument `np.maximum`; predictions and bounds `[10, 60] s` are unaffected.)*

## Known limits

- This app demonstrates a saved Mamdani fuzzy controller trained/evaluated on 10,000 synthetically generated scenarios for an isolated two-phase (NS/EW) junction.
- It does not connect to live roadside sensors, inductive loops, or physical signal hardware, and has not undergone field safety certification.
- Automated `unittest` and CSV parity checks (`T01`–`T10`) test `src/product_v1_service.py` and `src/step3_fuzzy_controller.py` directly; interactive browser rendering was verified in Step 5 (`results/step5/step5_ui_*.png`).

## Contributions

- **Aayush Jha (`Aayush-07-ops`)**: Created `step-6-testing` branch from `step-5-product-v1`, implemented `src/compare_step6_predictions.py` and `src/test_step6_validation.py`, ran all 10 planned checks (`T01`–`T10`), generated `data/reports/step5_ui_reference_prediction.csv` and `data/reports/step6_ui_prediction.csv`, and wrote `docs/STEP-6.md`.
