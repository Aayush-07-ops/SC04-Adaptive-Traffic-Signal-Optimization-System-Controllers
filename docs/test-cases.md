# Test cases

Five mandatory valid cases (all present in `data/sample_input.csv`) plus one invalid/impossible case
(in `data/invalid_input.csv`, kept separate).

| ID | Name | Input (queue_ns, queue_ew, dens_ns, dens_ew, wait_ns, wait_ew, emergency) | What to check | Expected baseline behaviour | Sensible target for later Soft Computing (not binding) |
|---|---|---|---|---|---|
| TRF-001 | Balanced low traffic | 5, 5, 20, 20, 25, 22, none | Validator accepts; nothing is urgent | NS 30 s (cycle) | Either phase, short-to-medium green |
| TRF-002 | Heavy NS queue | 30, 6, 85, 25, 120, 30, none | Large NS queue and density | EW 30 s (cycle, wrong side) | NS, long green |
| TRF-003 | Heavy EW queue | 4, 28, 15, 80, 20, 115, none | Large EW queue and density | NS 30 s (cycle, wrong side) | EW, long green |
| TRF-004 | Long waiting time despite shorter NS queue | 8, 12, 30, 40, 190, 65, none | Wait time must matter, not only queue | EW 30 s (cycle, ignores 190 s wait) | NS, to relieve the 190 s wait |
| TRF-005 | Emergency must get priority | 20, 20, 60, 60, 90, 90, EW | Equal traffic; emergency decides | EW 30 s (rule 4 override) | EW, with safe green length |
| INV-001 (TRF-999) | Invalid / impossible row | -4, 10, 140, 30, 50, 40, none | Validator must REJECT | No output; error message | Rejected before any controller runs |

## Expected validator result for INV-001
```
EXPECTED FAIL - the invalid data was correctly rejected:
  - row 2 (TRF-999): queue_ns = -4 is negative (queue must be >= 0 vehicles)
  - row 2 (TRF-999): density_ns_pct = 140 is outside 0 to 100 percent
```

## Test log
| Test | Command | Result | Evidence |
|---|---|---|---|
| Valid data accepted | `python src/validate_data.py` | PASS (20 rows) | `results/step1/validation_pass.txt` |
| Invalid data rejected | `python src/validate_data.py --file data/invalid_input.csv --expect-fail` | EXPECTED FAIL | `results/step1/validation_expected_fail.txt` |
| Baseline output | `python src/baseline.py` | 20 decisions | `results/step1/baseline_run.txt`, `baseline_expected.csv` |
