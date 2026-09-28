# Step 1 Project Contract

## Team and Responsibilities
- Member 1 — Team lead and integration
- Member 2 — Data preparation
- Member 3 — Baseline and testing
- Member 4 — Validation and UI

## One-Sentence Problem
Given queues, density, waiting time, and emergency direction, choose the next phase and green duration.

## User of the Product
A traffic operator studying one simple two-phase junction.

## Inputs and Units
North-South queue, East-West queue, density percentages, maximum waiting times, and emergency direction.

## Outputs
next_phase (NS/EW) and green_duration_sec.

## Baseline Method
Fixed-time signal: NS green for 30 seconds, followed by EW green for 30 seconds.

## Soft Computing Method for M1
Fuzzy controller for phase priority and green duration, compared with the fixed-time signal.

## Advanced Method for M2
Genetic Algorithm to tune controller parameters, difficult-case testing, and deployment.

## Dataset and Scenario Sources
Document the source URLs, licences, assumptions, and simulated data.

## Five Mandatory Test Cases
TRF-001 to TRF-005, with expected behavior.

## Product V1 Screen Sketch
Insert product-v1-sketch.png.

## Risks and Assumptions
State which traffic conditions and thresholds are simulated or temporary.

## Step 1 Completion Evidence
Add links to validation results, commits, and project files.