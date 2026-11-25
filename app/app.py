"""SC04 Step 5 - Product V1 Streamlit Application.

Connects the interactive traffic-signal interface to the saved Step 3 Mamdani
Fuzzy Logic Controller (models/fuzzy_traffic_controller.pkl), validates all user
inputs without crashing, and displays human-readable signal plans,
explanations, batch CSV checks, and adaptive junction simulations.

Run from the repository root:
    streamlit run app/app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from adaptive_simulator import run_adaptive_simulation
from product_v1_service import (
    DEFAULT_MODEL_PATH,
    LIMITATIONS_TEXT,
    load_fuzzy_model,
    predict_single_state,
    validate_and_predict_csv,
)

st.set_page_config(
    page_title="SC04 Adaptive Traffic Signal — Product V1",
    page_icon="🚦",
    layout="wide",
)

PRESETS = {
    "Normal": {
        "state_id": "UI-NORMAL-01",
        "queue_ns": "18",
        "queue_ew": "6",
        "density_ns_pct": "45",
        "density_ew_pct": "20",
        "max_wait_ns_sec": "95",
        "max_wait_ew_sec": "30",
        "emergency_direction": "none",
    },
    "Boundary (Min/Max)": {
        "state_id": "UI-BOUNDARY-01",
        "queue_ns": "0",
        "queue_ew": "60",
        "density_ns_pct": "0",
        "density_ew_pct": "100",
        "max_wait_ns_sec": "0",
        "max_wait_ew_sec": "300",
        "emergency_direction": "none",
    },
    "Emergency Override": {
        "state_id": "UI-EMERG-01",
        "queue_ns": "4",
        "queue_ew": "35",
        "density_ns_pct": "15",
        "density_ew_pct": "85",
        "max_wait_ns_sec": "20",
        "max_wait_ew_sec": "210",
        "emergency_direction": "NS",
    },
    "Invalid (Test Validation)": {
        "state_id": "UI-INVALID-01",
        "queue_ns": "-5",
        "queue_ew": "abc",
        "density_ns_pct": "140",
        "density_ew_pct": "25",
        "max_wait_ns_sec": "450",
        "max_wait_ew_sec": "10",
        "emergency_direction": "BOTH",
    },
}


def _init_form_state() -> None:
    if "ui_inputs" not in st.session_state:
        st.session_state["ui_inputs"] = dict(PRESETS["Normal"])


_init_form_state()

# ---------------------------------------------------------------------------
# HEADER & SIDEBAR MODEL STATUS
# ---------------------------------------------------------------------------
st.title("🚦 SC04 — Adaptive Traffic Signal Optimization (Product V1)")
st.caption(
    "Mamdani Fuzzy Logic Controller connected to saved Step 3 model "
    "(`models/fuzzy_traffic_controller.pkl`) | Academic Prototype"
)

_, model_meta, model_err = load_fuzzy_model()

st.sidebar.header("Saved Controller Status")
if model_err:
    st.sidebar.error("Model Unavailable")
    st.sidebar.caption(model_err)
else:
    st.sidebar.success("Saved Fuzzy Model Loaded")
    st.sidebar.markdown(f"**Model file:** `{DEFAULT_MODEL_PATH.name}`")
    if model_meta:
        test_acc = model_meta.get("test_metrics", {}).get("accuracy")
        emerg_ok = model_meta.get("test_metrics", {}).get("emergency_compliance")
        if test_acc is not None:
            st.sidebar.metric("Test Split Accuracy", f"{float(test_acc):.4f}")
        if emerg_ok is not None:
            st.sidebar.metric("Emergency Compliance", f"{float(emerg_ok):.4f}")
    st.sidebar.caption("Green bounds: 10–60 s | Emergency override: enabled")

st.sidebar.divider()
st.sidebar.info(f"**Limitations:** {LIMITATIONS_TEXT}")

# ---------------------------------------------------------------------------
# TABS
# ---------------------------------------------------------------------------
tab_decision, tab_batch, tab_sim = st.tabs(
    [
        "1. Signal Plan (Saved Fuzzy Model)",
        "2. Batch CSV Validation & Inference",
        "3. Junction Time-Series Simulation",
    ]
)

# ===========================================================================
# TAB 1: SINGLE INTERSECTION STATE DECISION
# ===========================================================================
with tab_decision:
    st.subheader("Single Intersection State Decision")
    st.write(
        "Enter current North-South (NS) and East-West (EW) traffic metrics, "
        "or load a preset to test normal, boundary, emergency, and invalid inputs."
    )

    pcols = st.columns(len(PRESETS))
    for col, (label, values) in zip(pcols, PRESETS.items()):
        if col.button(f"Preset: {label}", use_container_width=True):
            st.session_state["ui_inputs"] = dict(values)
            st.session_state.pop("last_decision", None)
            st.rerun()

    inp = st.session_state["ui_inputs"]

    with st.form("single_state_form"):
        c_id, c_em = st.columns([2, 1])
        state_id = c_id.text_input("Scenario / State ID", value=inp["state_id"])
        emerg_options = ["none", "NS", "EW", "BOTH"]
        emerg_idx = (
            emerg_options.index(inp["emergency_direction"])
            if inp["emergency_direction"] in emerg_options
            else 0
        )
        emergency_direction = c_em.selectbox(
            "Emergency Vehicle Direction",
            options=emerg_options,
            index=emerg_idx,
            help="Allowed valid values: none, NS, EW. 'BOTH' is included to test invalid-category rejection.",
        )

        col_ns, col_ew = st.columns(2)
        with col_ns:
            st.markdown("#### North-South (NS)")
            queue_ns = st.text_input(
                "NS Queue Length (vehicles, 0–100)", value=inp["queue_ns"]
            )
            density_ns_pct = st.text_input(
                "NS Lane Density (%, 0–100)", value=inp["density_ns_pct"]
            )
            max_wait_ns_sec = st.text_input(
                "NS Max Wait Time (seconds, 0–300)", value=inp["max_wait_ns_sec"]
            )

        with col_ew:
            st.markdown("#### East-West (EW)")
            queue_ew = st.text_input(
                "EW Queue Length (vehicles, 0–100)", value=inp["queue_ew"]
            )
            density_ew_pct = st.text_input(
                "EW Lane Density (%, 0–100)", value=inp["density_ew_pct"]
            )
            max_wait_ew_sec = st.text_input(
                "EW Max Wait Time (seconds, 0–300)", value=inp["max_wait_ew_sec"]
            )

        submitted = st.form_submit_button(
            "Predict Signal Plan (Run Saved Fuzzy Model)", type="primary"
        )

    if submitted:
        raw_payload = {
            "state_id": state_id,
            "queue_ns": queue_ns,
            "queue_ew": queue_ew,
            "density_ns_pct": density_ns_pct,
            "density_ew_pct": density_ew_pct,
            "max_wait_ns_sec": max_wait_ns_sec,
            "max_wait_ew_sec": max_wait_ew_sec,
            "emergency_direction": emergency_direction,
        }
        st.session_state["ui_inputs"] = raw_payload
        st.session_state["last_decision"] = predict_single_state(raw_payload)

    decision = st.session_state.get("last_decision")
    if decision:
        st.divider()
        if decision["status"] == "validation_error":
            st.error("Input Validation Failed — Request Rejected Safely")
            for err in decision["errors"]:
                st.write(f"- {err}")
        elif decision["status"] == "model_error":
            st.error("Saved Model Error")
            for err in decision["errors"]:
                st.write(f"- {err}")
        else:
            st.success(f"Signal Plan Computed for `{decision['state_id']}`")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Next Green Phase", decision["next_phase"])
            m2.metric("Green Duration", f"{decision['green_duration_sec']:.2f} s")
            m3.metric("NS Fuzzy Urgency", f"{decision['urgency_ns']:.1f} / 100")
            m4.metric("EW Fuzzy Urgency", f"{decision['urgency_ew']:.1f} / 100")

            st.info(f"**Phase Action:** {decision['phase_meaning']}")
            st.write(f"**Decision Mode:** `{decision['decision_mode']}`")
            st.write(
                f"**Baseline Comparison:** Fixed-time baseline assigns "
                f"{decision['baseline_green_sec']:.0f} s regardless of traffic; "
                f"fuzzy controller adjusts by `{decision['green_delta_vs_baseline_sec']:+.2f} s`."
            )
            st.write(f"**Why this decision:** {decision['explanation']}")
            st.warning(f"**Limitations:** {decision['limitations']}")


# ===========================================================================
# TAB 2: BATCH CSV VALIDATION & INFERENCE
# ===========================================================================
with tab_batch:
    st.subheader("Batch CSV Validation & Fuzzy Inference")
    st.write(
        "Upload a traffic-state CSV or run one of the repository's sample/invalid "
        "datasets to verify row-level validation and batch fuzzy inference."
    )

    b1, b2 = st.columns(2)
    sample_path = ROOT / "data" / "sample_input.csv"
    invalid_path = ROOT / "data" / "generated" / "invalid_test_scenarios.csv"

    batch_df = None
    if b1.button("Run Mandatory Sample (data/sample_input.csv)"):
        if sample_path.exists():
            batch_df = pd.read_csv(sample_path)
        else:
            st.error(f"Sample file not found: {sample_path}")

    if b2.button("Run Invalid Test File (invalid_test_scenarios.csv)"):
        if invalid_path.exists():
            batch_df = pd.read_csv(invalid_path)
        else:
            st.error(f"Invalid test file not found: {invalid_path}")

    uploaded = st.file_uploader("Or upload a CSV file", type=["csv"])
    if uploaded is not None:
        try:
            batch_df = pd.read_csv(uploaded)
        except Exception as exc:
            st.error(f"Could not parse uploaded CSV: {exc}")

    if batch_df is not None:
        batch_res = validate_and_predict_csv(batch_df)
        if batch_res["status"] != "ok":
            for err in batch_res["errors"]:
                st.error(err)
        else:
            c_tot, c_val, c_rej = st.columns(3)
            c_tot.metric("Total Rows", batch_res["total_rows"])
            c_val.metric("Valid Rows Predicted", batch_res["valid_count"])
            c_rej.metric("Invalid Rows Rejected", batch_res["rejected_count"])

            if not batch_res["valid_predictions"].empty:
                st.markdown("#### Valid Predictions")
                st.dataframe(batch_res["valid_predictions"], use_container_width=True)
                st.download_button(
                    "Download Valid Predictions CSV",
                    data=batch_res["valid_predictions"].to_csv(index=False),
                    file_name="step5_batch_predictions.csv",
                    mime="text/csv",
                )

            if not batch_res["rejected_rows"].empty:
                st.markdown("#### Rejected Rows (Validation Errors)")
                st.dataframe(batch_res["rejected_rows"], use_container_width=True)


# ===========================================================================
# TAB 3: INTERACTIVE JUNCTION SIMULATION
# ===========================================================================
with tab_sim:
    st.subheader("Interactive Junction Time-Series Simulation")
    st.caption(
        "Simulates queue evolution over time using the Step 2 adaptive fuzzy "
        "priority loop (`src/adaptive_simulator.py`)."
    )

    s1, s2, s3 = st.columns(3)
    sim_time = s1.slider("Simulation Duration (seconds)", 60, 1800, 600, 60)
    arr_ns = s2.slider("NS Arrival Probability", 0.05, 0.90, 0.20, 0.05)
    arr_ew = s3.slider("EW Arrival Probability", 0.05, 0.90, 0.20, 0.05)

    s4, s5, s6 = st.columns(3)
    svc_rate = s4.slider("Vehicle Service Probability", 0.10, 1.00, 0.50, 0.05)
    sim_q_ns = s5.number_input("Initial NS Queue (vehicles)", 0, 100, 30)
    sim_q_ew = s6.number_input("Initial EW Queue (vehicles)", 0, 100, 6)

    sim_emerg = st.selectbox(
        "Simulation Emergency Direction", ["none", "NS", "EW"], key="sim_emerg"
    )
    sim_seed = st.number_input("Random Seed", 0, 10000, 42)

    if st.button("Run Adaptive Simulation", type="primary"):
        with st.spinner("Simulating traffic..."):
            results, history = run_adaptive_simulation(
                initial_queue_ns=int(sim_q_ns),
                initial_queue_ew=int(sim_q_ew),
                emergency_direction=sim_emerg,
                simulation_time=int(sim_time),
                arrival_rate_ns=arr_ns,
                arrival_rate_ew=arr_ew,
                service_rate=svc_rate,
                seed=int(sim_seed),
            )
            st.session_state["sim_results"] = results
            st.session_state["sim_history"] = pd.DataFrame(history)

    if "sim_results" in st.session_state:
        results = st.session_state["sim_results"]
        history_df = st.session_state["sim_history"]

        c1, c2, c3 = st.columns(3)
        c1.metric("Vehicles Served", results["total_served"])
        c2.metric("Average Queue Waiting", f"{results['average_wait_sec']:.2f} veh·s/tick")
        c3.metric("Vehicles Remaining", results["vehicles_remaining"])

        c4, c5, c6 = st.columns(3)
        c4.metric("Maximum NS Queue", results["max_queue_ns"])
        c5.metric("Maximum EW Queue", results["max_queue_ew"])
        c6.metric("Total Vehicles Arrived", results["total_arrivals"])

        st.subheader("Traffic Queue Over Time")
        st.line_chart(
            history_df.set_index("time_sec")[["queue_ns", "queue_ew"]],
            x_label="Simulation Time (seconds)",
            y_label="Vehicles in Queue",
        )

        st.subheader("Signal Phase Over Time")
        phase_data = history_df[["time_sec", "phase"]].copy()
        phase_data["phase_code"] = phase_data["phase"].map({"NS": 1, "EW": 0})
        st.line_chart(
            phase_data.set_index("time_sec")[["phase_code"]],
            y_label="NS = 1, EW = 0",
        )

        with st.expander("View Simulation Data"):
            st.dataframe(history_df, use_container_width=True)

        st.download_button(
            "Download Simulation Results",
            data=history_df.to_csv(index=False),
            file_name="adaptive_simulation.csv",
            mime="text/csv",
        )
        st.success("Simulation completed successfully.")
