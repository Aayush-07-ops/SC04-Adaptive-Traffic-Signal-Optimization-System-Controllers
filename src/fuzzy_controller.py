
import numpy as np
import skfuzzy as fuzz

from skfuzzy import control as ctrl
from functools import lru_cache


# ==================================================
# 1. DEFAULT PARAMETERS
# ==================================================

DEFAULT_PARAMS = {
    "q_low_end": 40,
    "q_med_left": 20,
    "q_med_peak": 50,
    "q_med_right": 80,
    "q_high_start": 60,

    "w_short_end": 150,
    "w_med_left": 60,
    "w_med_peak": 150,
    "w_med_right": 240,
    "w_long_start": 150,

    "min_green": 15,
    "max_green": 60
}

PARAM_KEYS = tuple(DEFAULT_PARAMS.keys())


# ==================================================
# 2. PARAMETER VALIDATION
# ==================================================

def normalize_params(params=None):
    """Combine custom parameters with default parameters."""

    p = DEFAULT_PARAMS.copy()

    if params:
        p.update(params)

    # Queue membership constraints
    p["q_low_end"] = int(np.clip(
        p["q_low_end"], 20, 60
    ))

    p["q_med_left"] = int(np.clip(
        p["q_med_left"], 5, 50
    ))

    p["q_med_peak"] = int(np.clip(
        p["q_med_peak"],
        p["q_med_left"] + 5,
        80
    ))

    p["q_med_right"] = int(np.clip(
        p["q_med_right"],
        p["q_med_peak"] + 5,
        100
    ))

    p["q_high_start"] = int(np.clip(
        p["q_high_start"], 40, 90
    ))

    # Waiting-time membership constraints
    p["w_short_end"] = int(np.clip(
        p["w_short_end"], 60, 200
    ))

    p["w_med_left"] = int(np.clip(
        p["w_med_left"], 10, 200
    ))

    p["w_med_peak"] = int(np.clip(
        p["w_med_peak"],
        p["w_med_left"] + 10,
        250
    ))

    p["w_med_right"] = int(np.clip(
        p["w_med_right"],
        p["w_med_peak"] + 10,
        300
    ))

    p["w_long_start"] = int(np.clip(
        p["w_long_start"], 80, 250
    ))

    # Green-time constraints
    p["min_green"] = int(np.clip(
        p["min_green"], 10, 30
    ))

    p["max_green"] = int(np.clip(
        p["max_green"],
        p["min_green"] + 10,
        70
    ))

    return p


# ==================================================
# 3. BUILD FUZZY CONTROLLER
# ==================================================

@lru_cache(maxsize=256)
def build_controller(param_values):
    """
    Build a fuzzy system for a unique set of parameters.

    Cached controllers avoid rebuilding the fuzzy system
    for every call using the same parameters.
    """

    p = dict(zip(PARAM_KEYS, param_values))

    # Input: queue length
    queue = ctrl.Antecedent(
        np.arange(0, 101, 1),
        "queue"
    )

    # Input: waiting time
    wait = ctrl.Antecedent(
        np.arange(0, 301, 1),
        "wait"
    )

    # Output: signal priority
    priority = ctrl.Consequent(
        np.arange(0, 101, 1),
        "priority"
    )

    # --------------------------------------------------
    # QUEUE MEMBERSHIP FUNCTIONS
    # --------------------------------------------------

    queue["low"] = fuzz.trimf(
        queue.universe,
        [0, 0, p["q_low_end"]]
    )

    queue["medium"] = fuzz.trimf(
        queue.universe,
        [
            p["q_med_left"],
            p["q_med_peak"],
            p["q_med_right"]
        ]
    )

    queue["high"] = fuzz.trimf(
        queue.universe,
        [p["q_high_start"], 100, 100]
    )

    # --------------------------------------------------
    # WAITING-TIME MEMBERSHIP FUNCTIONS
    # --------------------------------------------------

    wait["short"] = fuzz.trimf(
        wait.universe,
        [0, 0, p["w_short_end"]]
    )

    wait["medium"] = fuzz.trimf(
        wait.universe,
        [
            p["w_med_left"],
            p["w_med_peak"],
            p["w_med_right"]
        ]
    )

    wait["long"] = fuzz.trimf(
        wait.universe,
        [p["w_long_start"], 300, 300]
    )

    # --------------------------------------------------
    # PRIORITY MEMBERSHIP FUNCTIONS
    # Keep original output functions
    # --------------------------------------------------

    priority["low"] = fuzz.trimf(
        priority.universe,
        [0, 0, 50]
    )

    priority["medium"] = fuzz.trimf(
        priority.universe,
        [25, 50, 75]
    )

    priority["high"] = fuzz.trimf(
        priority.universe,
        [50, 100, 100]
    )

    # --------------------------------------------------
    # FUZZY RULES
    # Keep your original rules
    # --------------------------------------------------

    rule1 = ctrl.Rule(
        queue["high"] | wait["long"],
        priority["high"]
    )

    rule2 = ctrl.Rule(
        queue["medium"] | wait["medium"],
        priority["medium"]
    )

    rule3 = ctrl.Rule(
        queue["low"] & wait["short"],
        priority["low"]
    )

    # Build fuzzy control system
    system = ctrl.ControlSystem([
        rule1,
        rule2,
        rule3
    ])

    return system


# ==================================================
# 4. CALCULATE PRIORITY
# ==================================================

def calculate_priority(
    queue_value,
    wait_value,
    params=None
):
    """
    Calculate traffic priority.

    Supports the original call:
        calculate_priority(30, 120)

    Also supports GA parameters:
        calculate_priority(30, 120, params)
    """

    p = normalize_params(params)

    # Hashable parameter key for caching
    key = tuple(
        p[name] for name in PARAM_KEYS
    )

    system = build_controller(key)

    # Create a fresh simulation for each calculation
    simulation = ctrl.ControlSystemSimulation(
        system,
        cache=False
    )

    # Validate and clamp inputs
    queue_value = float(np.clip(
        queue_value, 0, 100
    ))

    wait_value = float(np.clip(
        wait_value, 0, 300
    ))

    simulation.input["queue"] = queue_value
    simulation.input["wait"] = wait_value

    # Run fuzzy inference
    simulation.compute()

    # Return priority
    return float(
        simulation.output["priority"]
    )


# ==================================================
# 5. GREEN-TIME CALCULATION
# ==================================================

def calculate_green_time(
    priority_value,
    params=None
):
    """
    Convert priority into green signal duration.
    """

    p = normalize_params(params)

    priority_value = float(np.clip(
        priority_value, 0, 100
    ))

    green_duration = (
        p["min_green"]
        + (priority_value / 100)
        * (
            p["max_green"]
            - p["min_green"]
        )
    )

    return int(round(green_duration))


# ==================================================
# 6. TEST
# ==================================================

if __name__ == "__main__":

    print("DEFAULT CONTROLLER TEST")

    result = calculate_priority(30, 120)

    green = calculate_green_time(result)

    print("Queue: 30")
    print("Wait: 120 seconds")
    print("Priority:", round(result, 2))
    print("Green time:", green, "seconds")

    print("\nCUSTOM PARAMETER TEST")

    test_params = DEFAULT_PARAMS.copy()

    test_params["q_low_end"] = 35
    test_params["min_green"] = 20
    test_params["max_green"] = 55

    result = calculate_priority(
        30,
        120,
        test_params
    )

    green = calculate_green_time(
        result,
        test_params
    )

    print("Priority:", round(result, 2))
    print("Green time:", green, "seconds")

    print("\nAll tests completed.")