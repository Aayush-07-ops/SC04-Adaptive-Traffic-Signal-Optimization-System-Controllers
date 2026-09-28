
import pandas as pd

from adaptive_simulator import run_adaptive_simulation
from simulator import simulate_traffic


# Same traffic scenario for both controllers
initial_ns = 30
initial_ew = 6
duration = 600
seed = 42

# --------------------------------
# Fixed-time baseline
# --------------------------------

baseline = simulate_traffic(
    initial_queue_ns=initial_ns,
    initial_queue_ew=initial_ew,
    phase="NS",
    green_duration=30,
    simulation_time=duration,
    seed=seed
)

# --------------------------------
# Adaptive fuzzy controller
# --------------------------------

adaptive, history = run_adaptive_simulation(
    initial_queue_ns=initial_ns,
    initial_queue_ew=initial_ew,
    simulation_time=duration,
    seed=seed
)

# --------------------------------
# Display comparison
# --------------------------------

comparison = pd.DataFrame([
    {
        "Controller": "Fixed-Time",
        "Total Wait": baseline["total_wait"],
        "Throughput": baseline["throughput"],
        "Max NS Queue": baseline["max_queue_ns"],
        "Max EW Queue": baseline["max_queue_ew"]
    },
    {
        "Controller": "Adaptive Fuzzy",
        "Total Wait": adaptive["total_wait_vehicle_sec"],
        "Throughput": adaptive["total_served"],
        "Max NS Queue": adaptive["max_queue_ns"],
        "Max EW Queue": adaptive["max_queue_ew"]
    }
])

print("\nCONTROLLER COMPARISON")
print(comparison.to_string(index=False))

comparison.to_csv(
    "results/controller_comparison.csv",
    index=False
)

pd.DataFrame(history).to_csv(
    "results/adaptive_history.csv",
    index=False
)

print("\nResults saved successfully.")