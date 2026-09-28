
import json
import os
import sys
import pandas as pd

from benchmark import run_benchmark, DEFAULT_PARAMS


# Project paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(BASE_DIR, "results")

os.makedirs(RESULTS_DIR, exist_ok=True)

GA_FILE = os.path.join(RESULTS_DIR, "best_ga_parameters.json")

# Use identical traffic scenarios for all controllers
SEEDS = [42, 123, 456, 789, 2026]

# Load best GA parameters
with open(GA_FILE, "r") as file:
    ga_data = json.load(file)

GA_PARAMS = ga_data["parameters"]

results = []

# Run all three controllers on the same seeds
for seed in SEEDS:

    print(f"\nRunning seed: {seed}")

    # 1. Fixed-Time
    fixed_result, _ = run_benchmark(
        controller="fixed",
        seed=seed
    )

    fixed_result["controller_name"] = "Fixed-Time"
    fixed_result["seed"] = seed
    results.append(fixed_result)

    # 2. Original Fuzzy
    fuzzy_result, _ = run_benchmark(
        controller="fuzzy",
        seed=seed,
        fuzzy_params=DEFAULT_PARAMS
    )

    fuzzy_result["controller_name"] = "Fuzzy"
    fuzzy_result["seed"] = seed
    results.append(fuzzy_result)

    # 3. GA-Optimized Fuzzy
    ga_result, _ = run_benchmark(
        controller="fuzzy",
        seed=seed,
        fuzzy_params=GA_PARAMS
    )

    ga_result["controller_name"] = "GA-Fuzzy"
    ga_result["seed"] = seed
    results.append(ga_result)


# Convert results to DataFrame
df = pd.DataFrame(results)

# Save individual run results
runs_path = os.path.join(
    RESULTS_DIR,
    "final_controller_runs.csv"
)

df.to_csv(runs_path, index=False)


# Calculate average performance across all seeds
metrics = [
    "average_wait_sec",
    "total_served",
    "vehicles_remaining",
    "max_queue_ns",
    "max_queue_ew"
]

summary = (
    df.groupby("controller_name")[metrics]
    .mean()
    .round(2)
)

summary_path = os.path.join(
    RESULTS_DIR,
    "final_controller_summary.csv"
)

summary.to_csv(summary_path)

print("\nFINAL CONTROLLER COMPARISON")
print(summary)

print("\nSaved results:")
print(runs_path)
print(summary_path)