# SC04 Adaptive Traffic Signal Optimization System

An adaptive traffic signal optimization system using fuzzy logic and
genetic algorithms to improve traffic signal decisions based on
traffic conditions.

## Project Overview

The system studies a simple two-phase traffic junction:

- North-South (NS)
- East-West (EW)

The system uses traffic state information such as:

- Queue length
- Traffic density
- Maximum waiting time
- Emergency direction

The objective is to choose the next traffic phase and an appropriate
green duration while respecting defined safety limits.

## Problem Statement

Given queues, density, waiting time, and emergency direction, choose
the next phase and green duration.

## User

The Product V1 is designed for a traffic operator studying one simple
two-phase junction.

## Project Approach

### Baseline

A fixed-time controller is used as the baseline:

- NS green for 30 seconds
- EW green for 30 seconds
- Continue alternating between the two phases
- Apply an explicit safety override for emergency cases

### M1 — Fuzzy Controller

A fuzzy-logic controller uses traffic conditions to determine phase
priority and green duration.

The fuzzy controller is compared with the fixed-time baseline.

### M2 — Genetic Algorithm

A Genetic Algorithm is used to tune controller parameters.

M2 also includes:

- Difficult-case testing
- Parameter experiments
- Controller comparison
- Deployment of the final system

## Input Data

The main traffic-state fields are:

| Field | Meaning |
|---|---|
| `state_id` | Unique traffic state identifier |
| `queue_ns` | North-South queue length in vehicles |
| `queue_ew` | East-West queue length in vehicles |
| `density_ns_pct` | North-South traffic density percentage |
| `density_ew_pct` | East-West traffic density percentage |
| `max_wait_ns_sec` | Maximum North-South waiting time in seconds |
| `max_wait_ew_sec` | Maximum East-West waiting time in seconds |
| `emergency_direction` | Emergency direction: `none`, `NS`, or `EW` |

See `data/README.md` for the complete field definitions,
validation rules, sources, and assumptions.

## Outputs

The controller produces:

- `next_phase` — `NS` or `EW`
- `green_duration_sec` — selected green duration in seconds

Safety limits and temporary Step 1 assumptions are documented in
`docs/STEP-1.md`.

## Repository Structure

```text
.
├── app/
│   └── app.py
├── data/
│   ├── README.md
│   └── sample_input.csv
├── docs/
│   ├── STEP-1.md
│   ├── baseline-pseudocode.md
│   └── product-v1-sketch.png
├── notebooks/
├── report/
├── results/
├── src/
│   ├── validate_data.py
│   ├── baseline.py
│   ├── fuzzy_controller.py
│   ├── genetic_algorithm.py
│   └── ...
├── tests/
├── requirements.txt
└── README.md