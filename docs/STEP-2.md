# Step 2 - Scenario Data Pipeline

## Goal
Create a reproducible set of 10,000+ valid traffic-state scenarios for the two-phase junction,
plus a separate invalid-row file for validator testing. No fuzzy controller or GA is built in this step.

## Data type
All 10,000 rows are **generated scenarios**. They are not real field observations.

## Fields (unchanged from Step 1)
state_id, queue_ns, queue_ew, density_ns_pct, density_ew_pct, max_wait_ns_sec,
max_wait_ew_sec, emergency_direction (none / NS / EW).
Step 2 adds one label column: `scenario_type` (normal, boundary, stress, difficult, emergency).

## Scenario mix (10,000 total)
| scenario_type | rows | purpose |
|---|---:|---|
| normal | 5,000 | everyday traffic, queues 0-25 vehicles |
| boundary | 1,500 | values at or next to the limits (0, 1, 59, 60 vehicles; 0 / 100 % density; 0 / 300 s wait) |
| stress | 1,500 | heavy queues (40-60 vehicles), long waits |
| difficult | 1,500 | conflicting signals: short queue but very long wait, or near-ties |
| emergency | 500 | emergency vehicle on NS or EW |

## Assumptions (temporary - tell me if your Step 1 limits differ)
- Maximum queue per approach: 60 vehicles
- Maximum wait: 300 s
- Density grows with queue length plus small noise, clipped to 0-100 %
- Wait grows with queue length plus a random offset

## Reproducibility
- Seed: 42 (`src/generate_scenarios.py`)
- Run: `python src/generate_scenarios.py` then `python src/validate_data.py`

## Outputs
- data/generated/traffic_scenarios_10000.csv
- data/generated/invalid_test_scenarios.csv (120 rows, each breaks exactly one rule)
- data/reports/scenario_quality_report.md
- notebooks/02_scenario_inspection.ipynb (executed)
- results/step2/scenario_overview.png

## Usage rule
Generated scenarios are for developing and testing the controller. Never describe them as real data.
