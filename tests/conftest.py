"""Shared pytest fixtures + a synthetic-data helper for the BankShield tests."""
import os
import sys

import numpy as np
import pandas as pd
import pytest

# Make the utils/ modules importable the same way the Streamlit pages do.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "utils"))


def make_raw_transactions(n_customers=12, n_txns=80, seed=0):
    """A schema-complete raw transactions frame with a few injected missing
    values and one duplicate row — mirrors what the Dataset page would load."""
    rng = np.random.default_rng(seed)
    cust_ids = [f"CUST{i:03d}" for i in range(1, n_customers + 1)]
    genders = ["Male", "Female"]
    occs = ["Salaried", "Student", "Retired"]
    ttypes = ["Deposit", "Withdrawal", "Transfer", "Payment"]
    locs = ["New York", "Chicago", "Offshore-X"]
    devices = ["Known Device", "New Device", "Mobile App"]

    # one stable profile per customer
    profile = {
        c: dict(
            Age=int(rng.integers(18, 80)),
            Gender=str(rng.choice(genders)),
            Occupation=str(rng.choice(occs)),
            Income=float(round(rng.uniform(8000, 90000), 2)),
            CreditScore=int(rng.integers(300, 850)),
            PreviousFraudHistory=int(rng.integers(0, 2)),
        )
        for c in cust_ids
    }

    rows = []
    for i in range(n_txns):
        c = str(rng.choice(cust_ids))
        p = profile[c]
        ts = pd.Timestamp("2025-01-01") + pd.Timedelta(hours=int(rng.integers(0, 8000)))
        rows.append({
            "TransactionID": f"TXN{i:05d}",
            "CustomerID": c,
            "Age": p["Age"],
            "Gender": p["Gender"],
            "Occupation": p["Occupation"],
            "Income": p["Income"],
            "AccountBalance": float(round(rng.uniform(0, 20000), 2)),
            "TransactionAmount": float(round(rng.uniform(5, 5000), 2)),
            "TransactionType": str(rng.choice(ttypes)),
            "Timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "Location": str(rng.choice(locs)),
            "DeviceUsed": str(rng.choice(devices)),
            "CreditScore": p["CreditScore"],
            "PreviousFraudHistory": p["PreviousFraudHistory"],
            "DailyTransactionCount": int(rng.integers(1, 10)),
            "Fraud": "Yes" if rng.random() < 0.25 else "No",
        })
    df = pd.DataFrame(rows)
    # inject missing values + a duplicate row so cleaning has something to do
    df.loc[0, "Income"] = np.nan
    df.loc[1, "CreditScore"] = np.nan
    df = pd.concat([df, df.iloc[[2]]], ignore_index=True)
    return df


@pytest.fixture
def raw_df():
    return make_raw_transactions()


@pytest.fixture
def etl_module(tmp_path, monkeypatch):
    """The etl module with DB_PATH pointed at a throwaway db and its cache cleared."""
    import etl
    monkeypatch.setattr(etl, "DB_PATH", str(tmp_path / "test_warehouse.db"))
    etl.get_fact_with_dims.clear()
    yield etl
    etl.get_fact_with_dims.clear()
