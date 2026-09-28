
import pandas as pd
import random

random.seed(42)

rows = []

for i in range(10000):
    q_ns = random.randint(0, 40)
    q_ew = random.randint(0, 40)

    d_ns = min(100, q_ns * 2)
    d_ew = min(100, q_ew * 2)

    w_ns = random.randint(0, 300)
    w_ew = random.randint(0, 300)

    emergency = random.choices(
        ["none", "NS", "EW"],
        weights=[90, 5, 5]
    )[0]

    rows.append({
        "state_id": f"TRF-{i+1:05d}",
        "queue_ns": q_ns,
        "queue_ew": q_ew,
        "density_ns_pct": d_ns,
        "density_ew_pct": d_ew,
        "max_wait_ns_sec": w_ns,
        "max_wait_ew_sec": w_ew,
        "emergency_direction": emergency
    })

df = pd.DataFrame(rows)

df.to_csv("data/generated_traffic.csv", index=False)

print("Generated:", len(df), "traffic states")