
def fixed_time_controller(current_phase):
    if current_phase == "NS":
        return "EW", 30
    else:
        return "NS", 30


if __name__ == "__main__":
    phase = "NS"

    for i in range(6):
        next_phase, duration = fixed_time_controller(phase)

        print(
            f"Current: {phase}, "
            f"Next: {next_phase}, "
            f"Duration: {duration} seconds"
        )

        phase = next_phase