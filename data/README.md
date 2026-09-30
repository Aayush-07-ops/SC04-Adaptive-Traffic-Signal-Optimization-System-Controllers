# Traffic Data Documentation

## Purpose

This directory contains the starter traffic-state data used for Step 1
validation and testing.

The starter dataset represents traffic scenarios for a simple two-phase
junction:

- North-South (NS)
- East-West (EW)

The scenarios are project-created test data. They are not presented as
real-world traffic measurements.

## Input Field Dictionary

| Field | Meaning | Type / Unit | Allowed Values | Missing Value Behavior |
|---|---|---|---|---|
| `state_id` | Unique identifier for a traffic state | Text | Unique values such as `TRF-001` | Reject the row |
| `queue_ns` | Number of vehicles waiting in the North-South direction | Numeric / vehicles | 0 or greater | Reject the row |
| `queue_ew` | Number of vehicles waiting in the East-West direction | Numeric / vehicles | 0 or greater | Reject the row |
| `density_ns_pct` | Traffic density in the North-South direction | Numeric / percent | 0–100 | Reject the row |
| `density_ew_pct` | Traffic density in the East-West direction | Numeric / percent | 0–100 | Reject the row |
| `max_wait_ns_sec` | Maximum waiting time in the North-South direction | Numeric / seconds | 0–300 | Reject the row |
| `max_wait_ew_sec` | Maximum waiting time in the East-West direction | Numeric / seconds | 0–300 | Reject the row |
| `emergency_direction` | Direction containing an emergency condition | Text | `none`, `NS`, `EW` | Reject the row |

## Validation Rules

The Step 1 validation program checks:

1. All required columns are present.
2. The dataset contains at least one data row.
3. Required values are not missing.
4. Numeric traffic fields contain valid numeric values.
5. Queue values are not negative.
6. Density values are between 0 and 100 percent.
7. Maximum waiting times are between 0 and 300 seconds.
8. `emergency_direction` is one of `none`, `NS`, or `EW`.
9. `state_id` values are unique.

Run the validator with:

```text
python src/validate_data.py