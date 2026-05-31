import os
import pandas as pd


def test_synthetic_maternal_csv_contains_expected_columns():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    csv_path = os.path.join(repo_root, "backend", "model", "data", "synthetic_maternal.csv")

    assert os.path.exists(csv_path), f"Expected synthetic data CSV at {csv_path}"

    df = pd.read_csv(csv_path)
    expected_columns = [
        "patient_id",
        "age",
        "parity",
        "gestational_age_weeks",
        "systolic_bp",
        "diastolic_bp",
        "pulse",
        "temperature",
        "bleeding",
        "fever",
        "convulsions",
        "reduced_fetal_movement",
        "anemia_signs",
        "referral_label",
    ]

    missing = [col for col in expected_columns if col not in df.columns]
    assert not missing, f"Missing expected synthetic maternal CSV columns: {missing}"

    assert df["age"].between(15, 48).all(), (
        "Synthetic maternal CSV contains unrealistic ages."
    )
    assert df["parity"].between(0, 8).all(), (
        "Synthetic maternal CSV contains unrealistic parity values."
    )
    assert df["systolic_bp"].notna().all(), "Synthetic maternal CSV contains missing systolic_bp values."
    assert df["diastolic_bp"].notna().all(), "Synthetic maternal CSV contains missing diastolic_bp values."
