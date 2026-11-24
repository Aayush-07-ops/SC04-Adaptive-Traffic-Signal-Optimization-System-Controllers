# SC04 Generated Scenario Report

## Purpose
These are GENERATED traffic states for building and testing the fuzzy controller and later the GA tuner. They are not real field observations and must not be described as real data.

## Reproducibility
- Generator: `src/generate_scenarios.py` (fixed seed `42`)
- Valid scenarios: 10,000 in `data/generated/traffic_scenarios_10000.csv`
- Invalid test rows: 120 in `data/generated/invalid_test_scenarios.csv` (validator must reject all of them)

## Assumptions (temporary)
- Maximum queue per approach: 60 vehicles
- Maximum waiting time: 300 seconds
- Density rises with queue length plus small noise, clipped to 0-100 %
- Wait time rises with queue length plus a random offset
- Emergency direction is `none`, `NS` or `EW`

## Scenario mix

| scenario_type | rows |
|---|---:|
| normal | 5,000 |
| boundary | 1,500 |
| stress | 1,500 |
| difficult | 1,500 |
| emergency | 500 |
| **total** | **10,000** |

## Value ranges

| statistic | queue_ns | queue_ew | density_ns_pct | density_ew_pct | max_wait_ns_sec | max_wait_ew_sec |
|---|---:|---:|---:|---:|---:|---:|
| min | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| mean | 19.7 | 19.3 | 34.2 | 34.0 | 117.3 | 116.4 |
| max | 60.0 | 60.0 | 100.0 | 100.0 | 300.0 | 300.0 |

## Emergency balance

| emergency_direction | rows |
|---|---:|
| none | 8,725 |
| NS | 662 |
| EW | 613 |

## Usage rule
Use these scenarios to develop and test the controller. Do not present them as real traffic measurements in the report.
