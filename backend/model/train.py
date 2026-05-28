"""Generate synthetic maternal-health records and train a logistic-regression
risk-classification model.

The synthetic data mirrors realistic distributions of:
  • Maternal age  (15–48, skew toward 20–30)
  • Parity        (0–8)
  • Blood pressure (normal, moderate hypertension, severe pre-eclampsia)
  • Pulse          (60–140 bpm)
  • Danger signs   (bleeding 0/1/2, fever, convulsions, reduced FM, anemia)

Target classes:
  0 = low risk
  1 = intermediate risk
  2 = high risk

Usage:
    python -m backend.model.train          (from repo root)
    python train.py                        (from backend/model/)
"""

import os
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

SEED = 42
N_SAMPLES = 5_000
MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.joblib")

np.random.seed(SEED)


def _generate_synthetic_data(n: int = N_SAMPLES) -> pd.DataFrame:
    """Return a DataFrame of synthetic maternal health records."""
    age = np.random.normal(27, 6, n).clip(15, 48).astype(int)
    parity = np.random.poisson(1.5, n).clip(0, 8)

    # Blood pressure — bimodal: mostly normal, some hypertensive
    normal_mask = np.random.rand(n) > 0.25
    systolic_bp = np.where(
        normal_mask,
        np.random.normal(115, 10, n),
        np.random.normal(155, 15, n),
    ).clip(80, 200).astype(int)

    diastolic_bp = np.where(
        normal_mask,
        np.random.normal(75, 8, n),
        np.random.normal(100, 10, n),
    ).clip(50, 130).astype(int)

    pulse = np.random.normal(82, 15, n).clip(50, 150).astype(int)

    # Danger signs
    bleeding = np.random.choice([0, 1, 2], n, p=[0.80, 0.12, 0.08])
    fever = (np.random.rand(n) < 0.12).astype(int)
    convulsions = (np.random.rand(n) < 0.04).astype(int)
    reduced_fm = (np.random.rand(n) < 0.15).astype(int)
    anemia = (np.random.rand(n) < 0.20).astype(int)

    df = pd.DataFrame(
        {
            "age": age,
            "parity": parity,
            "systolic_bp": systolic_bp,
            "diastolic_bp": diastolic_bp,
            "pulse": pulse,
            "bleeding": bleeding,
            "fever": fever,
            "convulsions": convulsions,
            "reduced_fetal_movement": reduced_fm,
            "anemia": anemia,
        }
    )

    # ---- Label assignment (mirrors rule logic + some noise) ----
    labels = np.full(n, 0)  # default low

    # Intermediate conditions
    intermediate = (
        ((df.systolic_bp >= 140) & (df.systolic_bp < 160))
        | ((df.diastolic_bp >= 90) & (df.diastolic_bp < 110))
        | (df.bleeding == 1)
        | (df.reduced_fetal_movement == 1)
        | (df.anemia == 1)
        | (df.fever == 1)
        | ((df.age >= 35) & (df.parity >= 4))
    )
    labels[intermediate] = 1

    # High conditions (override intermediate)
    high = (
        (df.convulsions == 1)
        | (df.bleeding == 2)
        | (df.systolic_bp >= 160)
        | (df.diastolic_bp >= 110)
        | ((df.fever == 1) & (df.pulse >= 120))
    )
    labels[high] = 2

    # Add small random noise to make the model non-trivial
    noise_mask = np.random.rand(n) < 0.05
    labels[noise_mask] = np.random.choice([0, 1, 2], noise_mask.sum())

    df["risk_label"] = labels
    return df


def train():
    """Train the logistic-regression model and persist to disk."""
    print("Generating synthetic maternal health data …")
    df = _generate_synthetic_data()

    feature_cols = [
        "age", "parity", "systolic_bp", "diastolic_bp", "pulse",
        "bleeding", "fever", "convulsions", "reduced_fetal_movement", "anemia",
    ]

    X = df[feature_cols].values
    y = df["risk_label"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=SEED, stratify=y
    )

    model = LogisticRegression(
        max_iter=500,
        multi_class="multinomial",
        solver="lbfgs",
        random_state=SEED,
    )

    print("Training logistic regression model …")
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print("\n--- Classification Report ---")
    print(
        classification_report(
            y_test, y_pred, target_names=["low", "intermediate", "high"]
        )
    )

    joblib.dump(model, MODEL_PATH)
    print(f"\nModel saved to {MODEL_PATH}")


if __name__ == "__main__":
    train()
