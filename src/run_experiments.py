
import pandas as pd
from benchmark import run_benchmark

results = []

seeds = [42, 123, 456, 789, 2026]

for seed in seeds:
    for controller in ["fixed", "fuzzy"]:

        result, history = run_benchmark(
            controller=controller,
            duration=600,
            initial_ns=30,
            initial_ew=6,
            arrival_ns=0.20,
            arrival_ew=0.20,
            service_rate=0.50,
            seed=seed
        )

        result["seed"] = seed
        results.append(result)

df = pd.DataFrame(results)

print("\nALL EXPERIMENTS")
print(df.to_string(index=False))

print("\nAVERAGE PERFORMANCE")

summary = df.groupby("controller")[
    [
        "average_wait_sec",
        "total_served",
        "vehicles_remaining",
        "max_queue_ns",
        "max_queue_ew"
    ]
].mean()

print(summary.round(2))

df.to_csv(
    "results/benchmark_results.csv",
    index=False
)

summary.to_csv(
    "results/benchmark_summary.csv"
)

print("\nResults saved successfully.")