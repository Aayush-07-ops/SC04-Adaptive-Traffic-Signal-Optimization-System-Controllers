"""SC04 Step 6 - Automated unittest validation suite.

Run from the repository root:
    python -m unittest -v src/test_step6_validation.py
"""
from __future__ import annotations

import itertools
import sys
import unittest
from pathlib import Path

import pandas as pd

SRC_DIR = Path(__file__).resolve().parent
ROOT = SRC_DIR.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from product_v1_service import load_fuzzy_model, predict_single_state, validate_single_input
from step3_fuzzy_controller import MAX_GREEN_SEC, MIN_GREEN_SEC, predict_fuzzy


class Step6ValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        val_df = pd.read_csv(ROOT / "data" / "processed" / "validation.csv")
        self.normal_row = val_df.iloc[0].to_dict()

    def test_t01_normal_prediction(self) -> None:
        res = predict_single_state(self.normal_row)
        self.assertEqual(res["status"], "ok")
        self.assertIn(res["next_phase"], ("NS", "EW"))
        self.assertGreaterEqual(res["green_duration_sec"], MIN_GREEN_SEC)
        self.assertLessEqual(res["green_duration_sec"], MAX_GREEN_SEC)

    def test_t02_lower_boundary(self) -> None:
        payload = {
            **self.normal_row,
            "queue_ns": "0",
            "density_ns_pct": "0",
            "max_wait_ns_sec": "0",
        }
        df, errs = validate_single_input(payload)
        self.assertEqual(errs, [])
        self.assertIsNotNone(df)
        res = predict_single_state(payload)
        self.assertEqual(res["status"], "ok")
        self.assertGreaterEqual(res["green_duration_sec"], MIN_GREEN_SEC)
        self.assertLessEqual(res["green_duration_sec"], MAX_GREEN_SEC)

    def test_t03_upper_boundary(self) -> None:
        payload = {
            **self.normal_row,
            "queue_ns": "100",
            "density_ns_pct": "100",
            "max_wait_ns_sec": "300",
            "emergency_direction": "none",
        }
        res = predict_single_state(payload)
        self.assertEqual(res["status"], "ok")
        self.assertGreaterEqual(res["green_duration_sec"], MIN_GREEN_SEC)
        self.assertLessEqual(res["green_duration_sec"], MAX_GREEN_SEC)

    def test_t04_out_of_range_rejected(self) -> None:
        for field, bad_val in (
            ("density_ns_pct", "140"),
            ("max_wait_ns_sec", "450"),
            ("queue_ns", "-5"),
        ):
            payload = {**self.normal_row, field: bad_val}
            res = predict_single_state(payload)
            self.assertEqual(res["status"], "validation_error")
            self.assertTrue(any(field in e for e in res["errors"]))

    def test_t05_non_numeric_rejected(self) -> None:
        payload = {**self.normal_row, "queue_ew": "abc"}
        res = predict_single_state(payload)
        self.assertEqual(res["status"], "validation_error")
        self.assertTrue(any("not a valid number" in e for e in res["errors"]))

    def test_t06_missing_field_rejected(self) -> None:
        payload = {**self.normal_row, "queue_ns": ""}
        res = predict_single_state(payload)
        self.assertEqual(res["status"], "validation_error")
        self.assertTrue(any("missing" in e for e in res["errors"]))

    def test_invalid_emergency_category_rejected(self) -> None:
        payload = {**self.normal_row, "emergency_direction": "BOTH"}
        res = predict_single_state(payload)
        self.assertEqual(res["status"], "validation_error")
        self.assertTrue(any("emergency_direction" in e for e in res["errors"]))

    def test_t07_t08_missing_model_and_recovery(self) -> None:
        missing_pkl = ROOT / "models" / "missing_model_step6_test.pkl"
        res_missing = predict_single_state(self.normal_row, model_path=missing_pkl)
        self.assertEqual(res_missing["status"], "model_error")
        self.assertGreaterEqual(len(res_missing["errors"]), 1)

        res_ok = predict_single_state(self.normal_row)
        self.assertEqual(res_ok["status"], "ok")

    def test_fuzzy_rule_coverage_and_green_bounds(self) -> None:
        fuzzy_bundle, _, err = load_fuzzy_model()
        self.assertIsNone(err)
        self.assertIsNotNone(fuzzy_bundle)

        # Sample representative low / medium / high corners across all 27 rule combinations
        q_vals = [2.0, 25.0, 55.0]
        d_vals = [5.0, 50.0, 92.0]
        w_vals = [10.0, 120.0, 260.0]
        combos = list(itertools.product(q_vals, d_vals, w_vals))
        grid_df = pd.DataFrame(
            [
                {
                    "state_id": f"RULE-{idx:02d}",
                    "queue_ns": q,
                    "queue_ew": 10.0,
                    "density_ns_pct": d,
                    "density_ew_pct": 25.0,
                    "max_wait_ns_sec": w,
                    "max_wait_ew_sec": 45.0,
                    "emergency_direction": "none",
                }
                for idx, (q, d, w) in enumerate(combos, start=1)
            ]
        )
        out = predict_fuzzy(grid_df, fuzzy_bundle)
        self.assertEqual(len(out), 27)
        self.assertTrue(((out["fuzzy_green_duration_sec"] >= MIN_GREEN_SEC) & (out["fuzzy_green_duration_sec"] <= MAX_GREEN_SEC)).all())
        self.assertTrue(((out["urgency_ns"] >= 0.0) & (out["urgency_ns"] <= 100.0)).all())


if __name__ == "__main__":
    unittest.main(verbosity=2)
