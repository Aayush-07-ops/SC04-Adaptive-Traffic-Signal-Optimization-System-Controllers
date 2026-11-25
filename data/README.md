# Data README - Step 1 starter data

## Files
| File | Purpose |
|---|---|
| `sample_input.csv` | 20 valid starter traffic states (header row + 20 rows, comma-separated) |
| `invalid_input.csv` | One deliberately wrong row used to prove the validator rejects bad data. **Never mix into valid data.** |

## Data dictionary (inputs)
| Field | Simple meaning | Type / unit | Allowed values (Step 1) | If missing |
|---|---|---|---|---|
| `state_id` | Unique name of one traffic state | text identifier | `TRF-001`, `TRF-002`, ... (format `TRF-###`, unique) | Reject |
| `queue_ns` | Number of vehicles waiting on the north-south approach | integer, vehicles (input) | whole number 0 to 100 | Reject |
| `queue_ew` | Number of vehicles waiting on the east-west approach | integer, vehicles (input) | whole number 0 to 100 | Reject |
| `density_ns_pct` | How full the NS approach is with vehicles | number, percent (input) | 0 to 100 | Reject |
| `density_ew_pct` | How full the EW approach is with vehicles | number, percent (input) | 0 to 100 | Reject |
| `max_wait_ns_sec` | Waiting time of the vehicle that has waited longest on NS | number, seconds (input) | 0 to 300 | Reject |
| `max_wait_ew_sec` | Waiting time of the vehicle that has waited longest on EW | number, seconds (input) | 0 to 300 | Reject |
| `emergency_direction` | Approach on which an emergency vehicle is present | category (input) | exactly `none`, `NS`, or `EW` (case-sensitive) | Reject |

## Outputs (produced by the controller, not stored in the input file)
| Output | Meaning | Type / unit | Allowed values |
|---|---|---|---|
| `next_phase` | Which direction gets the next green | category | `NS` or `EW` |
| `green_duration_sec` | How long that green lasts | number, seconds | safe minimum **10 s** to safe maximum **60 s** (TEMPORARY) |

## Missing-value rule
Step 1 never guesses or fills a missing value. A row with any missing field is **rejected** with a clear error that
names the row and the field, and no phase is recommended for it.

## Assumptions (all TEMPORARY until confirmed in Step 2 / faculty review)
1. One isolated, simple **two-phase** junction: phase NS (north and south approaches go) and phase EW.
2. Density is the percentage of the approach's road space occupied by vehicles (0 = empty, 100 = completely full).
3. Maximum plausible queue is 100 vehicles per approach; maximum plausible wait is 300 s.
4. Safe green limits are 10 s (minimum) and 60 s (maximum); the fixed baseline uses 30 s.
5. Emergency vehicles appear on at most one approach at a time.
6. Turning movements, pedestrians, amber/all-red clearance and multiple junctions are **out of scope**.

## Source statement
- **Starter rows are hand-written by the team** to cover normal, boundary and difficult situations. They are **simulated/illustrative, not real measured data.**
- Rows `TRF-001` to `TRF-005` are the five mandatory cases from the project guide.
- Rows `TRF-006` to `TRF-010` are ordinary valid rows; `TRF-011` to `TRF-015` are boundary rows; `TRF-016` to `TRF-020` are difficult rows combining conditions.
- No external dataset or licence is used in Step 1.
- Planned for Step 2: a reproducible, seeded Python simulator (and optionally a reference tool such as SUMO, https://eclipse.dev/sumo/) to generate 10,000+ labelled-as-simulated states. Add exact URLs, licences and what each source contributed here when they are used.

## Row groups in `sample_input.csv`
| Rows | Group | Examples of what to point out |
|---|---|---|
| TRF-001 to 005 | Mandatory cases | balanced, heavy NS, heavy EW, long wait, emergency |
| TRF-006 to 010 | Ordinary | moderate, mixed values |
| TRF-011 to 015 | Boundary | all zeros (TRF-011); all maxima (TRF-012); one side empty, other nearly full (TRF-013, 014, 015) |
| TRF-016 to 020 | Difficult | near-tie heavy (016); emergency on a light side while the other side is heavy (017, 018); extreme wait with equal queues (019); heavy both with emergency (020) |

## The invalid case
`invalid_input.csv` -> `TRF-999` has `queue_ns = -4` (negative queue is impossible) and `density_ns_pct = 140`
(density over 100 percent). The validator must reject it with two clear messages.

## Plan for 10,000+ records (Step 2)
Use a reproducible simulator (fixed random seed) with documented arrival and departure assumptions and the safe
green-time limits above. Do not change field names, meanings or units silently: update this file and commit the change.

## Step 2 - Generated scenarios
- File: data/generated/traffic_scenarios_10000.csv (10,000 valid rows, seed 42)
- All rows are GENERATED scenarios, not real field observations.
- Extra column: scenario_type (normal, boundary, stress, difficult, emergency)
- Mix: normal 5000, boundary 1500, stress 1500, difficult 1500, emergency 500
- Assumptions (temporary): max queue 60 vehicles, max wait 300 s,
  density rises with queue length plus noise, wait rises with queue length plus offset
- Invalid test rows: data/generated/invalid_test_scenarios.csv (120 rows, each breaks one rule)
- Generator: src/generate_scenarios.py | Validator: src/validate_data.py
- Report: data/reports/scenario_quality_report.md
