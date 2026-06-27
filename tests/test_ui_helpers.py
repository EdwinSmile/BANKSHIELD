"""Tests for the pure (non-Streamlit-runtime) helpers in ui_helpers."""
import pandas as pd

import ui_helpers


def test_validate_columns_detects_missing():
    df = pd.DataFrame({"CustomerID": [1], "Age": [2]})
    ok, missing = ui_helpers.validate_columns(df)
    assert ok is False
    assert "Fraud" in missing


def test_validate_columns_passes_full_schema():
    df = pd.DataFrame({c: [0] for c in ui_helpers.REQUIRED_COLUMNS})
    ok, missing = ui_helpers.validate_columns(df)
    assert ok is True
    assert missing == []


def test_ensure_optional_columns_fills_defaults():
    df = pd.DataFrame({"CustomerID": ["a", "b"]})
    out = ui_helpers.ensure_optional_columns(df)
    for c in ui_helpers.OPTIONAL_COLUMNS:
        assert c in out.columns
    assert out["TransactionID"].nunique() == 2          # generated ids are unique


def test_risk_badge_maps_levels_to_classes():
    assert "risk-high" in ui_helpers.risk_badge("High Risk")
    assert "risk-medium" in ui_helpers.risk_badge("Medium Risk")
    assert "risk-low" in ui_helpers.risk_badge("Low Risk")
