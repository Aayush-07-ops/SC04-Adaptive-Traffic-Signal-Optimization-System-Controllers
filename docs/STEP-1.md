# Step 1 Project Contract

## Team and Responsibilities

- Member 1 — Team lead and integration
- Member 2 — Data preparation
- Member 3 — Baseline and testing
- Member 4 — Validation and UI

All members are expected to understand the complete Step 1 implementation and be able to explain the project during the faculty demonstration.

---

## One-Sentence Problem

Given queues, traffic density, maximum waiting time, and emergency direction at a simple two-phase junction, choose the next signal phase and an appropriate green duration.

---

## Problem Boundary

The Step 1 system models one simple two-phase traffic junction:

- NS = North-South movement
- EW = East-West movement
- The system uses queue length, traffic density, waiting time, and emergency direction.
- The baseline uses fixed-time signal control.
- The M1 Soft Computing method uses fuzzy logic.
- The M2 method uses Genetic Algorithm optimization of controller parameters.

The project is a simulation and decision-support prototype. It is not a live traffic-control system.

---

## User of the Product

A traffic operator or student/researcher studying the behavior of one simple two-phase traffic junction.

---

# Inputs and Units

| Field | Meaning | Type | Unit | Allowed values |
|---|---|---|---|---|
| `state_id` | Unique identifier for a traffic state | Text identifier | None | `TRF-001`, `TRF-002`, ... |
| `queue_ns` | Number of vehicles waiting in the North-South direction | Numeric | vehicles | 0 or greater |
| `queue_ew` | Number of vehicles waiting in the East-West direction | Numeric | vehicles | 0 or greater |
| `density_ns_pct` | Traffic density in the North-South direction | Numeric | percentage | 0 to 100 |
| `density_ew_pct` | Traffic density in the East-West direction | Numeric | percentage | 0 to 100 |
| `max_wait_ns_sec` | Longest current waiting time in the North-South direction | Numeric | seconds | 0 to 300 |
| `max_wait_ew_sec` | Longest current waiting time in the East-West direction | Numeric | seconds | 0 to 300 |
| `emergency_direction` | Direction containing an emergency-priority vehicle | Category | None | `none`, `NS`, `EW` |

### Missing-value rule

All required input fields must be present.

Missing values cause validation to fail rather than being silently replaced.

### Validation rules

- Queue values cannot be negative.
- Density values must be between 0 and 100 percent.
- Maximum waiting time must be between 0 and 300 seconds.
- `emergency_direction` must be `none`, `NS`, or `EW`.
- `state_id` must be unique.
- The input file must contain at least one data row.

---

# Outputs and Units

| Output | Meaning | Unit | Rule |
|---|---|---|---|
| `next_phase` | Signal phase selected for the next green period | NS/EW | Must be either `NS` or `EW` |
| `green_duration_sec` | Green time assigned to the selected phase | seconds | Must remain within the controller's configured safe minimum and maximum |

The exact green-time limits are controller parameters and are treated as simulation assumptions rather than real-world signal-control limits.

---

# Baseline Method

The baseline is a simple fixed-time signal used for comparison.

### Baseline rules

1. Start with NS green for 30 seconds.
2. Then use EW green for 30 seconds.
3. Continue alternating NS and EW.
4. The normal baseline does not change its green duration based on queue length or density.
5. If `emergency_direction` is not `none`, the test version allows an explicit safety override.
6. Invalid inputs such as negative queues, density above 100 percent, or waiting time above the selected validation limit are rejected.

The baseline is deliberately simple so that later fuzzy and GA methods can be compared against a clearly defined reference.

### Baseline pseudocode

See:

`docs/baseline-pseudocode.md`

---

# Soft Computing Method for M1

The M1 Soft Computing method is a fuzzy controller for the two-phase junction.

The fuzzy controller uses traffic-state information to determine:

- phase priority
- green duration

It is compared with the fixed-time baseline using the project simulator and common traffic-arrival conditions.

---

# Advanced Method for M2

The M2 method uses a Genetic Algorithm to tune the fuzzy-controller parameters.

The M2 evaluation includes:

- controller-parameter optimization
- difficult traffic conditions
- heavy queues
- emergency conditions
- comparison against the fixed-time baseline
- comparison against the untuned fuzzy controller
- simulation-based performance evaluation
- Product V2/deployment work

The current repository contains the GA implementation and controller comparison experiments.

---

# Dataset and Scenario Sources

## Project-generated data

The traffic-state datasets used by this project are simulated/generated data.

They must not be described as real-world traffic measurements.

The repository contains:

- `data/sample_input.csv` — Step 1 starter data
- `data/generated_traffic.csv` — generated traffic scenarios
- `src/generate_data.py` — reproducible data-generation program

The generated data are used for algorithm development and simulation experiments.

## External references

### FHWA Signal Timing Manual

The Federal Highway Administration Signal Timing Manual provides guidance and reference material concerning traffic signal timing and timing-plan development.

Source:

https://ops.fhwa.dot.gov/publications/fhwahop08024/

This source is used as background/reference material for traffic-signal timing concepts. It is not treated as the source of the project's simulated traffic records.

### FHWA Traffic Signal Program Handbook

The FHWA Traffic Signal Program Handbook provides guidance on traffic-signal management, operations, and performance-oriented practices.

Source:

https://ops.fhwa.dot.gov/publications/fhwahop23041/fhwahop23041.pdf

This source is used as background reference material and not as a source of the project's generated traffic records.

### SUMO Documentation

SUMO documentation describes traffic simulation concepts and provides reference material for traffic simulation, traffic lights, and simulated traffic states.

Source:

https://eclipse.dev/sumo/docs/

The project currently uses its own Python simulation rather than claiming that the generated CSV data are SUMO observations.

## Assumptions

- Traffic states are simulated.
- Queue length represents the number of waiting vehicles.
- Density is represented as a percentage from 0 to 100.
- Waiting time is represented in seconds.
- Emergency direction is categorical.
- The two-phase junction is a simplified research/simulation model.
- Signal timing thresholds are temporary project assumptions unless explicitly supported by an external source.
- Results from the simulator should not be interpreted as deployment-ready traffic-control recommendations.

---

# Five Mandatory Test Cases

The following five cases are the required Step 1 starter cases.

| ID | queue_ns | queue_ew | density_ns_pct | density_ew_pct | max_wait_ns_sec | max_wait_ew_sec | emergency_direction | Expected baseline behavior |
|---|---:|---:|---:|---:|---:|---:|---|---|
| TRF-001 | 5 | 5 | 20 | 20 | 25 | 22 | none | Continue the fixed 30-second NS/EW cycle; no special override |
| TRF-002 | 30 | 6 | 85 | 25 | 120 | 30 | none | Baseline still follows the fixed 30-second cycle despite the heavier NS queue |
| TRF-003 | 4 | 28 | 15 | 80 | 20 | 115 | none | Baseline still follows the fixed 30-second cycle despite the heavier EW queue |
| TRF-004 | 8 | 12 | 30 | 40 | 190 | 65 | none | Baseline follows the fixed cycle; long waiting time is not directly used by the fixed-time rule |
| TRF-005 | 20 | 20 | 60 | 60 | 90 | 90 | EW | Test version allows an explicit EW emergency safety override |

These five cases are included in `data/sample_input.csv`.

---

# Starter Data Structure

The Step 1 starter dataset contains 20 valid rows:

- 5 mandatory cases
- 5 ordinary traffic rows
- 5 boundary-condition rows
- 5 difficult-condition rows

The deliberately invalid case is kept separately and is not mixed with the valid starter data.

The validator checks:

- required columns
- non-empty dataset
- missing values
- numeric values
- negative queues
- density range
- waiting-time range
- emergency-direction categories
- unique state identifiers

---

# Validation and Testing

Validation program:

`src/validate_data.py`

Automated tests:

`tests/test_validator.py`

The current test suite covers:

1. Valid input
2. Missing column
3. Negative queue
4. Invalid emergency direction
5. Empty dataset

All five tests must pass before submission.

Example command:

```bash
python -m pytest tests/test_validator.py -v