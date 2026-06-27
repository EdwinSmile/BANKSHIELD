"""Tests for the fraud-classification and customer-clustering models."""
import numpy as np
import pandas as pd
import pytest

import ml_models


def make_fact_like(n=120, fraud_frac=0.25, n_customers=15, seed=1):
    """A frame shaped like the denormalized view get_fact_with_dims() returns."""
    rng = np.random.default_rng(seed)
    cust = [f"CUST{i:03d}" for i in range(n_customers)]
    return pd.DataFrame({
        "TransactionID": [f"TXN{i:05d}" for i in range(n)],
        "CustomerID": rng.choice(cust, n),
        "Age": rng.integers(18, 80, n),
        "AccountBalance": rng.uniform(0, 20000, n),
        "TransactionAmount": rng.uniform(5, 5000, n),
        "CreditScore": rng.integers(300, 850, n).astype(float),
        "PreviousFraudHistory": rng.integers(0, 2, n),
        "DailyTransactionCount": rng.integers(1, 10, n),
        "Gender": rng.choice(["Male", "Female"], n),
        "TransactionType": rng.choice(["Deposit", "Withdrawal", "Transfer"], n),
        "DeviceUsed": rng.choice(["Known Device", "New Device"], n),
        "Hour": rng.integers(0, 24, n),
        "FraudFlag": (rng.random(n) < fraud_frac).astype(int),
    })


def test_train_fraud_model_returns_metrics_and_test_flag():
    res = ml_models.train_fraud_model(make_fact_like(), algorithm="Random Forest")
    m = res["metrics"]
    for k in ["accuracy", "precision", "recall", "f1", "confusion_matrix"]:
        assert k in m
    assert 0.0 <= m["accuracy"] <= 1.0

    preds = res["predictions"]
    assert "InTestSet" in preds.columns
    assert preds["InTestSet"].sum() > 0
    # roughly the default test_size (0.25) was held out
    assert preds["InTestSet"].mean() == pytest.approx(0.25, abs=0.1)


def test_train_fraud_model_handles_single_positive_without_error():
    # Only one fraud row -> stratify must be disabled, and it must not raise. (#10)
    df = make_fact_like(n=40)
    df["FraudFlag"] = 0
    df.loc[df.index[0], "FraudFlag"] = 1
    res = ml_models.train_fraud_model(df, algorithm="Decision Tree")
    assert "metrics" in res


def test_decision_tree_algorithm_is_honored():
    res = ml_models.train_fraud_model(make_fact_like(), algorithm="Decision Tree")
    assert res["algorithm"] == "Decision Tree"
    assert res["feature_importance"] is not None


def test_run_customer_clustering_labels_three_tiers():
    df = make_fact_like(n=240, n_customers=30)
    res = ml_models.run_customer_clustering(df, n_clusters=3)
    clusters = res["customer_clusters"]
    assert set(clusters["RiskLevel"].unique()).issubset({"Low Risk", "Medium Risk", "High Risk"})
    assert clusters["RiskLevel"].notna().all()
    assert len(clusters) == df["CustomerID"].nunique()
