# Baseline pseudocode - fixed-time signal

The baseline is deliberately simple. Later it lets us prove whether the Soft Computing method is better.
It is **not** fuzzy logic, ANN, or GA. Runnable version: `src/baseline.py`.

## Numbered rules (TEMPORARY values are marked)
1. Start with **NS green for 30 seconds** (30 s is TEMPORARY).
2. Then use **EW green for 30 seconds**.
3. Continue alternating NS, EW, NS, EW ... **even when one queue is longer**.
4. **Test-version safety override:** if `emergency_direction` is not `none`, give green to that direction for 30 s instead of the cycle phase.
5. **Reject** negative queues, density over 100, or wait above 300 s (300 s is the selected limit, TEMPORARY).

Assumption for Step 1 testing: the position of a row in the file stands for the position in the cycle
(1st row = NS, 2nd row = EW, 3rd = NS ...). The alternation continues even when an override is used.

## Pseudocode
```
READ one valid input row
IF the row is invalid:
    SHOW a clear error
ELSE:
    APPLY the simple rules in order
        IF emergency_direction != "none":
            next_phase = emergency_direction        (rule 4)
            rule_used  = "emergency override"
        ELSE:
            next_phase = NS if cycle position is odd (1st, 3rd, ...) else EW     (rules 1-3)
            rule_used  = "fixed alternation"
        green_duration_sec = 30
    CALCULATE the baseline output
    PRINT the output and the rule that was used
SAVE the result for later comparison
```

## Expected baseline behaviour for the five mandatory cases
| Case | Cycle position | Expected baseline output | Rule used | Weakness this exposes |
|---|---|---|---|---|
| TRF-001 Balanced low traffic | 1st -> NS | NS, 30 s | 1-3 | None - traffic is balanced, fixed signal is fine |
| TRF-002 Heavy NS queue (30 vs 6) | 2nd -> EW | EW, 30 s | 1-3 | Serves the nearly-empty EW side while NS has 30 vehicles |
| TRF-003 Heavy EW queue (28 vs 4) | 3rd -> NS | NS, 30 s | 1-3 | Serves the nearly-empty NS side while EW has 28 vehicles |
| TRF-004 Long wait despite shorter NS queue | 4th -> EW | EW, 30 s | 1-3 | NS vehicle has waited 190 s but EW (65 s wait) is served |
| TRF-005 Emergency on EW | 5th -> would be NS | EW, 30 s | 4 | Override is right, but a fixed 30 s ignores how large the queues are |

These results are verified by running `python src/baseline.py` (output saved in `results/step1/baseline_run.txt`).
