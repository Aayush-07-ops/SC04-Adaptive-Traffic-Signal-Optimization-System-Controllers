
import random
from fuzzy_controller import calculate_priority


def run_adaptive_simulation(
    initial_queue_ns=10,
    initial_queue_ew=10,
    emergency_direction="none",
    simulation_time=600,
    arrival_rate_ns=0.20,
    arrival_rate_ew=0.20,
    service_rate=0.50,
    seed=42
):
    random.seed(seed)

    # Initial traffic queues
    queue_ns = initial_queue_ns
    queue_ew = initial_queue_ew

    # Performance metrics
    total_wait_ns = 0
    total_wait_ew = 0

    total_arrivals_ns = initial_queue_ns
    total_arrivals_ew = initial_queue_ew

    total_served_ns = 0
    total_served_ew = 0

    max_queue_ns = queue_ns
    max_queue_ew = queue_ew

    phase = "NS"
    green_duration = 30
    phase_time = 0

    history = []

    for t in range(simulation_time):

        # ---------------------------------
        # 1. Generate new arriving vehicles
        # ---------------------------------

        if random.random() < arrival_rate_ns:
            queue_ns += 1
            total_arrivals_ns += 1

        if random.random() < arrival_rate_ew:
            queue_ew += 1
            total_arrivals_ew += 1

        # ---------------------------------
        # 2. Serve vehicles in green phase
        # ---------------------------------

        if phase == "NS":
            if queue_ns > 0:
                if random.random() < service_rate:
                    queue_ns -= 1
                    total_served_ns += 1

        elif phase == "EW":
            if queue_ew > 0:
                if random.random() < service_rate:
                    queue_ew -= 1
                    total_served_ew += 1

        # ---------------------------------
        # 3. Accumulate queue waiting time
        # ---------------------------------

        total_wait_ns += queue_ns
        total_wait_ew += queue_ew

        max_queue_ns = max(max_queue_ns, queue_ns)
        max_queue_ew = max(max_queue_ew, queue_ew)

        # ---------------------------------
        # 4. Check whether green phase ended
        # ---------------------------------

        phase_time += 1

        if phase_time >= green_duration:

            # Calculate fuzzy priorities using
            # current queue and accrued wait.

            wait_ns = min(
                300,
                total_wait_ns / max(total_arrivals_ns, 1)
            )

            wait_ew = min(
                300,
                total_wait_ew / max(total_arrivals_ew, 1)
            )

            priority_ns = calculate_priority(
                min(queue_ns, 100),
                wait_ns
            )

            priority_ew = calculate_priority(
                min(queue_ew, 100),
                wait_ew
            )

            # Emergency override in simulation
            if emergency_direction == "NS":
                next_phase = "NS"

            elif emergency_direction == "EW":
                next_phase = "EW"

            elif priority_ns >= priority_ew:
                next_phase = "NS"

            else:
                next_phase = "EW"

            # Calculate green duration
            selected_priority = (
                priority_ns
                if next_phase == "NS"
                else priority_ew
            )

            min_green = 15
            max_green = 60

            green_duration = round(
                min_green
                + (selected_priority / 100)
                * (max_green - min_green)
            )

            green_duration = max(
                min_green,
                min(max_green, green_duration)
            )

            phase = next_phase
            phase_time = 0

        # ---------------------------------
        # 5. Record traffic state
        # ---------------------------------

        history.append({
            "time_sec": t,
            "queue_ns": queue_ns,
            "queue_ew": queue_ew,
            "phase": phase,
            "green_duration": green_duration
        })

    # ---------------------------------
    # 6. Calculate final metrics
    # ---------------------------------

    total_arrivals = total_arrivals_ns + total_arrivals_ew
    total_served = total_served_ns + total_served_ew

    total_wait = total_wait_ns + total_wait_ew

    average_wait = (
        total_wait / total_arrivals
        if total_arrivals > 0
        else 0
    )

    results = {
        "simulation_time_sec": simulation_time,
        "total_arrivals": total_arrivals,
        "total_served": total_served,
        "vehicles_remaining": queue_ns + queue_ew,
        "average_wait_sec": round(average_wait, 2),
        "total_wait_vehicle_sec": total_wait,
        "max_queue_ns": max_queue_ns,
        "max_queue_ew": max_queue_ew,
        "final_queue_ns": queue_ns,
        "final_queue_ew": queue_ew
    }

    return results, history


if __name__ == "__main__":

    results, history = run_adaptive_simulation(
        initial_queue_ns=30,
        initial_queue_ew=6,
        simulation_time=600,
        seed=42
    )

    print("\nADAPTIVE SIMULATION RESULTS")

    for key, value in results.items():
        print(f"{key}: {value}")

    print("\nFirst five simulation records:")

    for record in history[:5]:
        print(record)