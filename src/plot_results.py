
import os
import pandas as pd
import matplotlib.pyplot as plt

# Project paths
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

RESULTS_DIR = os.path.join(BASE_DIR, "results")

SUMMARY_FILE = os.path.join(
    RESULTS_DIR,
    "final_controller_summary.csv"
)

HISTORY_FILE = os.path.join(
    RESULTS_DIR,
    "adaptive_history.csv"
)

# --------------------------------
# 1. Controller comparison graphs
# --------------------------------

df = pd.read_csv(SUMMARY_FILE, index_col=0)

graphs = {
    "average_wait_sec": (
        "Average Vehicle Waiting Time",
        "Waiting Time (seconds)",
        "average_wait_comparison.png"
    ),
    "total_served": (
        "Total Vehicles Served",
        "Vehicles Served",
        "vehicles_served_comparison.png"
    ),
    "vehicles_remaining": (
        "Vehicles Remaining After Simulation",
        "Vehicles Remaining",
        "vehicles_remaining_comparison.png"
    )
}

for metric, (title, ylabel, filename) in graphs.items():

    plt.figure(figsize=(9, 6))

    ax = df[metric].plot(kind="bar", rot=0)

    plt.title(title, fontsize=14)
    plt.xlabel("Controller")
    plt.ylabel(ylabel)

    plt.grid(axis="y", linestyle="--", alpha=0.4)

    # Add values above bars
    for container in ax.containers:
        ax.bar_label(container, fmt="%.2f", padding=3)

    plt.tight_layout()

    output_path = os.path.join(
        RESULTS_DIR,
        filename
    )

    plt.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    print(f"Created: {filename}")


# --------------------------------
# 2. Existing adaptive queue graph
# --------------------------------

if os.path.exists(HISTORY_FILE):

    history = pd.read_csv(HISTORY_FILE)

    plt.figure(figsize=(10, 5))

    plt.plot(
        history["time_sec"],
        history["queue_ns"],
        label="North-South Queue"
    )

    plt.plot(
        history["time_sec"],
        history["queue_ew"],
        label="East-West Queue"
    )

    plt.xlabel("Simulation Time (seconds)")
    plt.ylabel("Vehicles in Queue")
    plt.title("Adaptive Traffic Queue Over Time")

    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    plt.savefig(
        os.path.join(
            RESULTS_DIR,
            "adaptive_queue.png"
        ),
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    print("Updated: adaptive_queue.png")

else:
    print("Queue history not found; skipping queue graph.")


print("\nAll available graphs generated!")