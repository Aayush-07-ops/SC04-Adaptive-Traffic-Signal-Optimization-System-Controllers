# Fixed-Time Baseline Pseudocode

## Purpose

This baseline provides a simple fixed-time controller for comparison
with the M1 fuzzy controller and the M2 GA-tuned controller.

## Input Validation

For one traffic state:

1. Read the traffic state.
2. Reject the input if:
   - queue_ns < 0
   - queue_ew < 0
   - density_ns_pct < 0 or density_ns_pct > 100
   - density_ew_pct < 0 or density_ew_pct > 100
   - max_wait_ns_sec < 0 or max_wait_ns_sec > 300
   - max_wait_ew_sec < 0 or max_wait_ew_sec > 300
   - emergency_direction is not one of:
     - none
     - NS
     - EW
3. If the input is invalid, display an error and stop.

## Baseline Rules

1. Start with NS green for 30 seconds.
2. Then give EW green for 30 seconds.
3. Continue alternating NS and EW.
4. The baseline does not change its normal 30-second timing because
   one direction has a longer queue.
5. If emergency_direction is not `none`, apply the documented
   safety override in the test version.
6. Display the selected phase and green duration.
7. Save the result.

## Pseudocode

START

READ one traffic state

IF the input is invalid:
    DISPLAY an error
    STOP

IF emergency_direction == NS:
    APPLY NS emergency safety override
    DISPLAY NS phase and documented duration
ELSE IF emergency_direction == EW:
    APPLY EW emergency safety override
    DISPLAY EW phase and documented duration
ELSE:
    START with NS green for 30 seconds
    NEXT give EW green for 30 seconds
    CONTINUE alternating NS and EW

DISPLAY the baseline phase and duration
SAVE the result

END

## Mandatory Test Cases

### TRF-001 — Balanced low traffic
Expected baseline behavior:
- No emergency override.
- Follow the normal fixed-time sequence.
- NS = 30 seconds, then EW = 30 seconds.

### TRF-002 — Heavy NS queue
Expected baseline behavior:
- No emergency override.
- The baseline still follows the fixed 30-second sequence.
- It does not extend NS green based on the longer queue.

### TRF-003 — Heavy EW queue
Expected baseline behavior:
- No emergency override.
- The baseline still follows the fixed 30-second sequence.
- It does not extend EW green based on the longer queue.

### TRF-004 — Long waiting time
Expected baseline behavior:
- No emergency override.
- The baseline still follows the fixed 30-second sequence.
- Waiting time does not change the normal baseline timing.

### TRF-005 — EW emergency
Expected baseline behavior:
- emergency_direction = EW.
- Apply the explicit EW emergency safety override in the test version.
- Record the selected EW phase and documented safety behavior.

## Temporary Step 1 Assumptions

The 30-second fixed-time duration is a simple baseline assumption for
comparison.

The validation limits are:
- Queue: 0 or more vehicles.
- Density: 0–100 percent.
- Maximum waiting time: 0–300 seconds.

These are Step 1/test-version limits and are not claimed to be
optimal real-world signal-timing values.

## Comparison Purpose

The fixed-time baseline is used as the reference controller.

M1:
- Fuzzy controller.

M2:
- Genetic Algorithm used to tune the controller parameters.

The later experiments compare controller behavior using the same
traffic scenarios.
