"""Tests for the triage / risk-scoring model."""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from model.triage_model import evaluate_risk


class TestRuleBasedHighRisk:
    """WHO absolute danger signs must always yield HIGH risk."""

    def test_convulsions(self):
        result = evaluate_risk({
            "age": 25, "parity": 1,
            "systolic_bp": 115, "diastolic_bp": 75, "pulse": 80,
            "bleeding": 0, "fever": False, "convulsions": True,
            "reduced_fetal_movement": False, "anemia": False,
        })
        assert result["risk_level"] == "high"
        assert result["rule_triggered"] is True

    def test_severe_bleeding(self):
        result = evaluate_risk({
            "age": 30, "parity": 2,
            "systolic_bp": 120, "diastolic_bp": 78, "pulse": 85,
            "bleeding": 2, "fever": False, "convulsions": False,
            "reduced_fetal_movement": False, "anemia": False,
        })
        assert result["risk_level"] == "high"

    def test_severe_preeclampsia_systolic(self):
        result = evaluate_risk({
            "age": 28, "parity": 0,
            "systolic_bp": 170, "diastolic_bp": 95, "pulse": 90,
            "bleeding": 0, "fever": False, "convulsions": False,
            "reduced_fetal_movement": False, "anemia": False,
        })
        assert result["risk_level"] == "high"

    def test_severe_preeclampsia_diastolic(self):
        result = evaluate_risk({
            "age": 28, "parity": 0,
            "systolic_bp": 140, "diastolic_bp": 115, "pulse": 90,
            "bleeding": 0, "fever": False, "convulsions": False,
            "reduced_fetal_movement": False, "anemia": False,
        })
        assert result["risk_level"] == "high"

    def test_high_fever_with_tachycardia(self):
        result = evaluate_risk({
            "age": 22, "parity": 1,
            "systolic_bp": 110, "diastolic_bp": 70, "pulse": 125,
            "bleeding": 0, "fever": True, "convulsions": False,
            "reduced_fetal_movement": False, "anemia": False,
        })
        assert result["risk_level"] == "high"


class TestLowRisk:
    """Normal values should yield LOW risk."""

    def test_healthy_baseline(self):
        result = evaluate_risk({
            "age": 26, "parity": 1,
            "systolic_bp": 115, "diastolic_bp": 74, "pulse": 76,
            "bleeding": 0, "fever": False, "convulsions": False,
            "reduced_fetal_movement": False, "anemia": False,
        })
        assert result["risk_level"] == "low"


class TestIntermediateRisk:
    """Multiple soft flags should yield INTERMEDIATE."""

    def test_moderate_hypertension_plus_anemia(self):
        result = evaluate_risk({
            "age": 32, "parity": 3,
            "systolic_bp": 145, "diastolic_bp": 95, "pulse": 88,
            "bleeding": 0, "fever": False, "convulsions": False,
            "reduced_fetal_movement": False, "anemia": True,
        })
        assert result["risk_level"] in ("intermediate", "high")


class TestReturnStructure:
    """Ensure the returned dict always has the expected keys."""

    def test_keys_present(self):
        result = evaluate_risk({
            "age": 25, "parity": 0,
            "systolic_bp": 110, "diastolic_bp": 70, "pulse": 72,
            "bleeding": 0, "fever": False, "convulsions": False,
            "reduced_fetal_movement": False, "anemia": False,
        })
        assert "risk_level" in result
        assert "recommended_action" in result
        assert "ml_probability" in result
        assert "rule_triggered" in result
        assert result["risk_level"] in ("high", "intermediate", "low")
