
import json
from pathlib import Path

import pandas as pd

from benchmark import run_benchmark
from fuzzy_controller import DEFAULT_PARAMS


# ---------------------------------------
# LOAD GA PARAMETERS
# ---------------------------------------

params_file = Path("results/ga_best_params.json")

if not params_file.exists():
    raise FileNotFoundError(
        "Run genetic_algorithm.py first."
    )

with open(params_file, "r") as f:
    ga_data = json.load(f)

ga_params = ga_data["parameters"]

print("Loaded optimized GA parameters.")


# ---------------------------------------
# EXPERIMENT CONFIGURATION
# ---------------------------------------

SEEDS = [42, 123, 456, 789, 2026]

controllers = {
    "Fixed-Time": {
        "controller": "fixed",
        "params": None
    },

    "Fuzzy": {
        "controller": "fuzzy",
        "params": DEFAULT_PARAMS
    },

    "GA-Fuzzy": {
        "controller": "fuzzy",
        "params": ga_params
    }
}


# ---------------------------------------
# RUN COMPARISON
# ---------------------------------------

results = []

for name, config in controllers.items():

    print(f"\nRunning {name} controller...")

    for seed in SEEDS:

        result, history = run_benchmark(
            controller=config["controller"],
            duration=600,
            initial_ns=30,
            initial_ew=6,
            arrival_ns=0.20,
            arrival_ew=0.20,
            service_rate=0.50,
            seed=seed,
            fuzzy_params=config["params"]
        )

        result["controller_name"] = name
        result["seed"] = seed

        results.append(result)

        print(
            f"Seed {seed}: "
            f"Wait = {result['average_wait_sec']:.2f}s"
        )


# ---------------------------------------
# CREATE RESULTS TABLE
# ---------------------------------------

df = pd.DataFrame(results)

metrics = [
    "average_wait_sec",
    "total_served",
    "vehicles_remaining",
    "max_queue_ns",
    "max_queue_ew"
]

summary = df.groupby(
    "controller_name"
)[metrics].mean().round(2)

print("\n================================")
print("FINAL CONTROLLER COMPARISON")
print("================================")

print(summary.to_string())


# ---------------------------------------
# SAVE RESULTS
# ---------------------------------------

Path("results").mkdir(
    parents=True,
    exist_ok=True
)

df.to_csv(
    "results/ga_comparison_runs.csv",
    index=False
)

summary.to_csv(
    "results/ga_comparison_summary.csv"
)

print("\nComparison saved successfully.")