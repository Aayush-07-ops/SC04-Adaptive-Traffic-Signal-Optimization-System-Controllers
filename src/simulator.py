
import random


def simulate_traffic(
    initial_queue_ns,
    initial_queue_ew,
    phase,
    green_duration,
    arrival_rate_ns=0.2,
    arrival_rate_ew=0.2,
    service_rate=0.5,
    simulation_time=300,
    seed=42
):
    random.seed(seed)

    queue_ns = initial_queue_ns
    queue_ew = initial_queue_ew

    total_wait_ns = 0
    total_wait_ew = 0

    total_served_ns = 0
    total_served_ew = 0

    max_queue_ns = queue_ns
    max_queue_ew = queue_ew

    phase_time = 0

    for t in range(simulation_time):

        # Generate new arriving vehicles
        if random.random() < arrival_rate_ns:
            queue_ns += 1

        if random.random() < arrival_rate_ew:
            queue_ew += 1

        # Serve vehicles in the active direction
        if phase == "NS":
            if queue_ns > 0:
                if random.random() < service_rate:
                    queue_ns -= 1
                    total_served_ns += 1
        else:
            if queue_ew > 0:
                if random.random() < service_rate:
                    queue_ew -= 1
                    total_served_ew += 1

        # Accumulate queue waiting time
        total_wait_ns += queue_ns
        total_wait_ew += queue_ew

        # Track maximum queues
        max_queue_ns = max(max_queue_ns, queue_ns)
        max_queue_ew = max(max_queue_ew, queue_ew)

        # Change phase when green duration expires
        phase_time += 1

        if phase_time >= green_duration:
            phase = "EW" if phase == "NS" else "NS"
            phase_time = 0

    return {
        "average_queue_ns": total_wait_ns / simulation_time,
        "average_queue_ew": total_wait_ew / simulation_time,
        "total_wait": total_wait_ns + total_wait_ew,
        "throughput": total_served_ns + total_served_ew,
        "max_queue_ns": max_queue_ns,
        "max_queue_ew": max_queue_ew
    }


if __name__ == "__main__":

    result = simulate_traffic(
        initial_queue_ns=20,
        initial_queue_ew=10,
        phase="NS",
        green_duration=30
    )

    print("Simulation Results")

    for key, value in result.items():
        print(key, ":", round(value, 2))