
import json
from pathlib import Path

import pandas as pd

from benchmark import run_benchmark
from fuzzy_controller import DEFAULT_PARAMS


# Load saved GA parameters
with open("results/ga_best_params.json", "r") as f:
    data = json.load(f)

ga_params = data["parameters"]

print("Saved GA fitness:", data["best_fitness"])


# Use the same five seeds for every controller
seeds = [42, 123, 456, 789, 2026]

controllers = {
    "Fuzzy": DEFAULT_PARAMS,
    "GA-Fuzzy": ga_params
}

results = []

for name, params in controllers.items():

    print(f"\nEvaluating {name}")

    for seed in seeds:

        result, history = run_benchmark(
            controller="fuzzy",
            duration=600,
            initial_ns=30,
            initial_ew=6,
            arrival_ns=0.20,
            arrival_ew=0.20,
            service_rate=0.50,
            seed=seed,
            fuzzy_params=params
        )

        result["controller_name"] = name
        result["seed"] = seed

        results.append(result)

        print(
            f"Seed {seed}: "
            f"Wait={result['average_wait_sec']}, "
            f"Served={result['total_served']}, "
            f"Remaining={result['vehicles_remaining']}"
        )


# Summarize results
df = pd.DataFrame(results)

metrics = [
    "average_wait_sec",
    "total_served",
    "vehicles_remaining",
    "max_queue_ns",
    "max_queue_ew"
]

summary = df.groupby("controller_name")[metrics].mean()

print("\nFINAL GA VALIDATION")
print(summary.round(2).to_string())

Path("results").mkdir(exist_ok=True)

df.to_csv(
    "results/ga_validation_runs.csv",
    index=False
)

summary.to_csv(
    "results/ga_validation_summary.csv"
)

print("\nSaved GA validation results.")