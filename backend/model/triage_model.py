"""Maternal risk-scoring engine.

Combines **rule-based WHO danger-sign checks** with a lightweight
scikit-learn logistic regression model to produce a composite risk
classification (high / intermediate / low) and recommended action.

Rule-based tier always takes precedence for absolute danger signs
(convulsions, severe bleeding, severe pre-eclampsia).  The ML tier
refines intermediate vs. low when no absolute danger sign is present.
"""

import os
import numpy as np

_MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.joblib")
_ml_model = None  # lazy-loaded


def _load_ml_model():
    """Load the trained logistic-regression model from disk (if available)."""
    global _ml_model
    if _ml_model is not None:
        return _ml_model
    try:
        import joblib

        if os.path.exists(_MODEL_PATH):
            _ml_model = joblib.load(_MODEL_PATH)
    except Exception:
        _ml_model = None
    return _ml_model


# ---------------------------------------------------------------------------
# Rule-based tier  (WHO maternal danger signs)
# ---------------------------------------------------------------------------

def _rule_based_check(data: dict) -> tuple[str | None, str | None]:
    """Return (risk_level, action) if an absolute rule fires, else (None, None).

    WHO absolute danger signs that always → HIGH:
      • Convulsions / eclampsia
      • Severe vaginal bleeding (bleeding == 2)
      • Severe pre-eclampsia  (systolic ≥ 160 OR diastolic ≥ 110)
      • Very high fever (≥ 39 °C — encoded as fever=True + pulse ≥ 120)

    Intermediate triggers:
      • Moderate hypertension (systolic 140-159 OR diastolic 90-109)
      • Light bleeding (bleeding == 1)
      • Reduced foetal movement
      • Anemia symptoms
      • High maternal age (≥ 35) with parity ≥ 4
    """

    # --- HIGH risk absolute rules ---
    if data.get("convulsions"):
        return "high", "emergency_referral"

    if data.get("bleeding", 0) == 2:
        return "high", "emergency_referral"

    systolic = data.get("systolic_bp", 0)
    diastolic = data.get("diastolic_bp", 0)

    if systolic >= 160 or diastolic >= 110:
        return "high", "emergency_referral"

    pulse = data.get("pulse", 0)
    if data.get("fever") and pulse >= 120:
        return "high", "stabilize_and_refer"

    # --- INTERMEDIATE risk rules ---
    intermediate_flags = 0

    if 140 <= systolic < 160 or 90 <= diastolic < 110:
        intermediate_flags += 1

    if data.get("bleeding", 0) == 1:
        intermediate_flags += 1

    if data.get("reduced_fetal_movement"):
        intermediate_flags += 1

    if data.get("anemia"):
        intermediate_flags += 1

    if data.get("fever"):
        intermediate_flags += 1

    age = data.get("age", 25)
    parity = data.get("parity", 0)
    if age >= 35 and parity >= 4:
        intermediate_flags += 1

    if intermediate_flags >= 2:
        return "intermediate", "stabilize_and_monitor"

    if intermediate_flags == 1:
        return None, None  # defer to ML

    return None, None


# ---------------------------------------------------------------------------
# ML tier  (logistic regression)
# ---------------------------------------------------------------------------

def _ml_predict(data: dict) -> tuple[str, float]:
    """Run the logistic model and return (risk_level, probability).

    Features (same order as training):
      age, parity, systolic_bp, diastolic_bp, pulse,
      bleeding, fever, convulsions, reduced_fetal_movement, anemia
    """
    model = _load_ml_model()

    features = np.array(
        [
            [
                data.get("age", 25),
                data.get("parity", 0),
                data.get("systolic_bp", 120),
                data.get("diastolic_bp", 80),
                data.get("pulse", 75),
                data.get("bleeding", 0),
                int(data.get("fever", False)),
                int(data.get("convulsions", False)),
                int(data.get("reduced_fetal_movement", False)),
                int(data.get("anemia", False)),
            ]
        ]
    )

    if model is None:
        # Fallback heuristic when model file is unavailable
        risk_score = (
            (features[0][0] - 20) * 0.01   # age contribution
            + features[0][1] * 0.05         # parity
            + (features[0][2] - 120) * 0.02 # systolic delta
            + (features[0][3] - 80) * 0.02  # diastolic delta
            + features[0][5] * 0.15         # bleeding
            + features[0][6] * 0.10         # fever
            + features[0][8] * 0.10         # reduced FM
            + features[0][9] * 0.10         # anemia
        )
        prob = float(min(max(1 / (1 + np.exp(-risk_score)), 0.01), 0.99))
    else:
        proba = model.predict_proba(features)[0]
        # Class order: 0=low, 1=intermediate, 2=high
        prob = float(proba[2])  # probability of high risk

    if prob >= 0.6:
        return "high", prob
    elif prob >= 0.3:
        return "intermediate", prob
    else:
        return "low", prob


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_ACTION_MAP = {
    "high": "emergency_referral",
    "intermediate": "stabilize_and_monitor",
    "low": "routine_monitoring",
}


def evaluate_risk(data: dict) -> dict:
    """Evaluate maternal risk from intake data.

    Parameters
    ----------
    data : dict
        Keys: age, parity, systolic_bp, diastolic_bp, pulse,
              bleeding (0/1/2), fever (bool), convulsions (bool),
              reduced_fetal_movement (bool), anemia (bool).

    Returns
    -------
    dict
        {
            "risk_level": "high" | "intermediate" | "low",
            "recommended_action": str,
            "ml_probability": float | None,
            "rule_triggered": bool,
        }
    """
    rule_level, rule_action = _rule_based_check(data)

    if rule_level == "high":
        # Absolute danger sign — skip ML
        return {
            "risk_level": "high",
            "recommended_action": rule_action,
            "ml_probability": None,
            "rule_triggered": True,
        }

    ml_level, ml_prob = _ml_predict(data)

    if rule_level == "intermediate":
        # Rule already flagged intermediate — ML can only upgrade
        final_level = "high" if ml_level == "high" else "intermediate"
    else:
        final_level = ml_level

    return {
        "risk_level": final_level,
        "recommended_action": _ACTION_MAP.get(final_level, "routine_monitoring"),
        "ml_probability": ml_prob,
        "rule_triggered": rule_level is not None,
    }
