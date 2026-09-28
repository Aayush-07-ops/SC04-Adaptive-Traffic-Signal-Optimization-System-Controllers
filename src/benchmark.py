
import random

from fuzzy_controller import (
    calculate_priority,
    DEFAULT_PARAMS
)


def generate_traffic(
    duration=600,
    arrival_ns=0.20,
    arrival_ew=0.20,
    seed=42
):
    """Generate reproducible traffic arrivals."""

    rng = random.Random(seed)

    arrivals = []

    for t in range(duration):
        arrivals.append({
            "time": t,
            "ns": int(rng.random() < arrival_ns),
            "ew": int(rng.random() < arrival_ew)
        })

    return arrivals


def run_benchmark(
    controller="fixed",
    duration=600,
    initial_ns=30,
    initial_ew=6,
    arrival_ns=0.20,
    arrival_ew=0.20,
    service_rate=0.50,
    seed=42,
    fuzzy_params=None
):
    """Run one traffic controller."""

    arrivals = generate_traffic(
        duration=duration,
        arrival_ns=arrival_ns,
        arrival_ew=arrival_ew,
        seed=seed
    )

    # Same service random numbers for each controller
    service_rng = random.Random(seed + 10000)

    service_ns = [
        service_rng.random() < service_rate
        for _ in range(duration)
    ]

    service_ew = [
        service_rng.random() < service_rate
        for _ in range(duration)
    ]

    # Initialize queues with vehicle arrival times
    ns_queue = [0] * initial_ns
    ew_queue = [0] * initial_ew

    total_wait_ns = 0
    total_wait_ew = 0

    served_ns = 0
    served_ew = 0

    phase = "NS"
    phase_time = 0
    green_duration = 30

    history = []

    # Merge GA parameters with fuzzy defaults
    params = {
        **DEFAULT_PARAMS,
        **(fuzzy_params or {})
    }

    min_green = params["min_green"]
    max_green = params["max_green"]

    for t in range(duration):

        # 1. Add new vehicles
        ns_queue.extend([t] * arrivals[t]["ns"])
        ew_queue.extend([t] * arrivals[t]["ew"])

        # 2. Serve vehicles from active phase
        if phase == "NS" and ns_queue and service_ns[t]:

            arrival_time = ns_queue.pop(0)

            total_wait_ns += t - arrival_time
            served_ns += 1

        elif phase == "EW" and ew_queue and service_ew[t]:

            arrival_time = ew_queue.pop(0)

            total_wait_ew += t - arrival_time
            served_ew += 1

        # 3. Record queue state
        history.append({
            "time_sec": t,
            "queue_ns": len(ns_queue),
            "queue_ew": len(ew_queue),
            "phase": phase,
            "green_duration": green_duration
        })

        # 4. Update phase timer
        phase_time += 1

        if phase_time >= green_duration:

            if controller == "fixed":

                # Fixed-time controller
                phase = (
                    "EW" if phase == "NS"
                    else "NS"
                )

                green_duration = 30

            elif controller == "fuzzy":

                # Calculate waiting times
                wait_ns = (
                    t - ns_queue[0]
                    if ns_queue else 0
                )

                wait_ew = (
                    t - ew_queue[0]
                    if ew_queue else 0
                )

                # Calculate fuzzy priorities
                # IMPORTANT: Pass GA parameters
                priority_ns = calculate_priority(
                    min(len(ns_queue), 100),
                    min(wait_ns, 300),
                    params
                )

                priority_ew = calculate_priority(
                    min(len(ew_queue), 100),
                    min(wait_ew, 300),
                    params
                )

                # Select next phase
                phase = (
                    "NS"
                    if priority_ns >= priority_ew
                    else "EW"
                )

                priority = max(
                    priority_ns,
                    priority_ew
                )

                # Calculate green duration using parameters
                green_duration = round(
                    min_green
                    + (priority / 100)
                    * (max_green - min_green)
                )

                # Enforce minimum and maximum green
                green_duration = max(
                    min_green,
                    min(max_green, green_duration)
                )

            else:
                raise ValueError(
                    f"Unknown controller: {controller}"
                )

            phase_time = 0

    # 5. Calculate performance metrics
    total_served = served_ns + served_ew

    total_wait = total_wait_ns + total_wait_ew

    average_wait = (
        total_wait / total_served
        if total_served else 0
    )

    total_arrivals = (
        initial_ns
        + initial_ew
        + sum(x["ns"] for x in arrivals)
        + sum(x["ew"] for x in arrivals)
    )

    result = {
        "controller": controller,
        "total_arrivals": total_arrivals,
        "total_served": total_served,
        "vehicles_remaining": (
            len(ns_queue) + len(ew_queue)
        ),
        "average_wait_sec": round(
            average_wait, 2
        ),
        "max_queue_ns": max(
            x["queue_ns"] for x in history
        ),
        "max_queue_ew": max(
            x["queue_ew"] for x in history
        )
    }

    return result, history


if __name__ == "__main__":

    for controller in ["fixed", "fuzzy"]:

        result, history = run_benchmark(
            controller=controller,
            duration=600,
            seed=42
        )

        print("\n", controller.upper())
        print(result)