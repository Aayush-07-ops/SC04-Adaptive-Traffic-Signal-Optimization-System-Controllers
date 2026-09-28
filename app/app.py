
import sys
from pathlib import Path

import streamlit as st
import pandas as pd

# Import simulator from src folder
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from adaptive_simulator import run_adaptive_simulation


st.set_page_config(
    page_title="Adaptive Traffic Signal Optimization",
    page_icon="🚦",
    layout="wide"
)

st.title("🚦 Adaptive Traffic Signal Optimization")
st.caption("Fuzzy Logic Based Adaptive Traffic Signal Simulator")

st.divider()

# -----------------------------------
# SIDEBAR: SIMULATION CONFIGURATION
# -----------------------------------

st.sidebar.header("Simulation Settings")

simulation_time = st.sidebar.slider(
    "Simulation Duration (seconds)",
    min_value=60,
    max_value=1800,
    value=600,
    step=60
)

arrival_ns = st.sidebar.slider(
    "NS Arrival Probability",
    min_value=0.05,
    max_value=0.90,
    value=0.20,
    step=0.05
)

arrival_ew = st.sidebar.slider(
    "EW Arrival Probability",
    min_value=0.05,
    max_value=0.90,
    value=0.20,
    step=0.05
)

service_rate = st.sidebar.slider(
    "Vehicle Service Probability",
    min_value=0.10,
    max_value=1.00,
    value=0.50,
    step=0.05
)

seed = st.sidebar.number_input(
    "Random Seed",
    min_value=0,
    max_value=10000,
    value=42
)

# -----------------------------------
# TRAFFIC INPUTS
# -----------------------------------

st.subheader("Initial Traffic Conditions")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### North-South (NS)")

    queue_ns = st.number_input(
        "Initial NS Queue",
        min_value=0,
        max_value=100,
        value=30
    )

with col2:
    st.markdown("### East-West (EW)")

    queue_ew = st.number_input(
        "Initial EW Queue",
        min_value=0,
        max_value=100,
        value=6
    )

emergency = st.selectbox(
    "Emergency Vehicle Direction",
    ["none", "NS", "EW"]
)

st.divider()

# -----------------------------------
# RUN SIMULATION
# -----------------------------------

if st.button("Run Adaptive Simulation", type="primary"):

    with st.spinner("Simulating traffic..."):

        results, history = run_adaptive_simulation(
            initial_queue_ns=int(queue_ns),
            initial_queue_ew=int(queue_ew),
            emergency_direction=emergency,
            simulation_time=int(simulation_time),
            arrival_rate_ns=arrival_ns,
            arrival_rate_ew=arrival_ew,
            service_rate=service_rate,
            seed=int(seed)
        )

        history_df = pd.DataFrame(history)

        st.session_state["sim_results"] = results
        st.session_state["sim_history"] = history_df

# -----------------------------------
# DISPLAY RESULTS
# -----------------------------------

if "sim_results" in st.session_state:

    results = st.session_state["sim_results"]
    history_df = st.session_state["sim_history"]

    st.subheader("Simulation Performance")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Vehicles Served",
        results["total_served"]
    )

    c2.metric(
        "Average Queue Waiting",
        f'{results["average_wait_sec"]:.2f}'
    )

    c3.metric(
        "Vehicles Remaining",
        results["vehicles_remaining"]
    )

    c4, c5, c6 = st.columns(3)

    c4.metric(
        "Maximum NS Queue",
        results["max_queue_ns"]
    )

    c5.metric(
        "Maximum EW Queue",
        results["max_queue_ew"]
    )

    c6.metric(
        "Total Vehicles Arrived",
        results["total_arrivals"]
    )

    st.divider()

    # -----------------------------------
    # QUEUE GRAPH
    # -----------------------------------

    st.subheader("Traffic Queue Over Time")

    queue_data = history_df.set_index("time_sec")[
        ["queue_ns", "queue_ew"]
    ]

    st.line_chart(
        queue_data,
        x_label="Simulation Time (seconds)",
        y_label="Vehicles in Queue"
    )

    # -----------------------------------
    # SIGNAL PHASE
    # -----------------------------------

    st.subheader("Signal Phase Over Time")

    phase_data = history_df[
        ["time_sec", "phase"]
    ].copy()

    phase_data["phase_code"] = (
        phase_data["phase"].map({
            "NS": 1,
            "EW": 0
        })
    )

    st.line_chart(
        phase_data.set_index("time_sec")[
            ["phase_code"]
        ],
        y_label="NS = 1, EW = 0"
    )

    st.caption(
        "The phase chart uses NS = 1 and EW = 0 "
        "to represent the active simulated phase."
    )

    # -----------------------------------
    # DATA TABLE
    # -----------------------------------

    with st.expander("View Simulation Data"):

        st.dataframe(
            history_df,
            use_container_width=True
        )

    # -----------------------------------
    # DOWNLOAD RESULTS
    # -----------------------------------

    st.download_button(
        "Download Simulation Results",
        data=history_df.to_csv(index=False),
        file_name="adaptive_simulation.csv",
        mime="text/csv"
    )

    st.success("Simulation completed successfully.")