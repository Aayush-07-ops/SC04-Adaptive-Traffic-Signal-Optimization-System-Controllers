
import pandas as pd
import pytest

from src.validate_data import validate_data

COLUMNS = [
    "state_id",
    "queue_ns",
    "queue_ew",
    "density_ns_pct",
    "density_ew_pct",
    "max_wait_ns_sec",
    "max_wait_ew_sec",
    "emergency_direction",
]


def make_data():
    return pd.DataFrame([{
        "state_id": 1,
        "queue_ns": 20,
        "queue_ew": 10,
        "density_ns_pct": 65,
        "density_ew_pct": 40,
        "max_wait_ns_sec": 45,
        "max_wait_ew_sec": 25,
        "emergency_direction": "none",
    }])


def test_valid_input(tmp_path):
    file = tmp_path / "valid.csv"
    make_data().to_csv(file, index=False)
    assert validate_data(file) is True


def test_missing_column(tmp_path):
    file = tmp_path / "missing.csv"
    make_data().drop(columns=["queue_ns"]).to_csv(file, index=False)
    assert validate_data(file) is False


def test_negative_queue(tmp_path):
    file = tmp_path / "negative.csv"
    df = make_data()
    df.loc[0, "queue_ns"] = -1
    df.to_csv(file, index=False)
    assert validate_data(file) is False


def test_invalid_emergency_direction(tmp_path):
    file = tmp_path / "emergency.csv"
    df = make_data()
    df.loc[0, "emergency_direction"] = "NORTH"
    df.to_csv(file, index=False)
    assert validate_data(file) is False


def test_empty_dataset(tmp_path):
    file = tmp_path / "empty.csv"
    pd.DataFrame(columns=COLUMNS).to_csv(file, index=False)
    assert validate_data(file) is False