"""
ETL + Data Warehouse module for BankShield.
Builds a star-schema SQLite warehouse from a raw transactions dataframe:

                DimTime
                   |
DimCustomer --- FactTransactions --- DimLocation
                   |
          DimTransactionType

All functions are written to be safe to re-run (idempotent) so the
Streamlit app can rebuild the warehouse whenever a new dataset is uploaded.
"""
import sqlite3
import pandas as pd
import numpy as np
import os
from contextlib import closing
import streamlit as st

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "db", "bankshield.db")
DB_PATH = os.path.abspath(DB_PATH)


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)


# ---------------------------------------------------------------------
# CLEANING / PREPROCESSING
# ---------------------------------------------------------------------
def clean_data(df: pd.DataFrame, missing_strategy: str = "median") -> tuple[pd.DataFrame, dict]:
    """Cleans the raw dataframe and returns (clean_df, report dict)."""
    report = {}
    df = df.copy()

    report["rows_before"] = len(df)
    report["duplicates_found"] = int(df.duplicated().sum())
    df = df.drop_duplicates().reset_index(drop=True)
    report["rows_after_dedup"] = len(df)

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    missing_report = {}
    for col in numeric_cols:
        n_missing = int(df[col].isna().sum())
        if n_missing > 0:
            missing_report[col] = n_missing
            if missing_strategy == "mean":
                fill_val = df[col].mean()
            elif missing_strategy == "mode":
                fill_val = df[col].mode().iloc[0] if not df[col].mode().empty else 0
            else:
                fill_val = df[col].median()
            df[col] = df[col].fillna(fill_val)

    cat_cols = df.select_dtypes(include=["object"]).columns.tolist()
    for col in cat_cols:
        n_missing = int(df[col].isna().sum())
        if n_missing > 0:
            missing_report[col] = n_missing
            mode_val = df[col].mode().iloc[0] if not df[col].mode().empty else "Unknown"
            df[col] = df[col].fillna(mode_val)

    report["missing_values_filled"] = missing_report
    report["strategy_used"] = missing_strategy
    return df, report


# ---------------------------------------------------------------------
# STAR SCHEMA BUILD (ETL: Extract -> Transform -> Load)
# ---------------------------------------------------------------------
def build_warehouse(df: pd.DataFrame, missing_strategy: str = "median") -> dict:
    """
    Takes a cleaned/raw transactions dataframe with columns matching the
    BankShield schema and loads it into a SQLite star schema.
    Returns a summary dict for display in the UI.
    """
    df, clean_report = clean_data(df, missing_strategy)

    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
    df = df.dropna(subset=["Timestamp"]).reset_index(drop=True)

    with closing(get_connection()) as conn, closing(conn.cursor()) as cur:
        # --- Drop & recreate schema (idempotent rebuild) ---
        for tbl in ["FactTransactions", "DimCustomer", "DimTime", "DimLocation", "DimTransactionType"]:
            cur.execute(f"DROP TABLE IF EXISTS {tbl}")

        cur.execute("""
            CREATE TABLE DimCustomer (
                CustomerKey INTEGER PRIMARY KEY AUTOINCREMENT,
                CustomerID TEXT UNIQUE,
                Age INTEGER,
                Gender TEXT,
                Occupation TEXT,
                Income REAL,
                CreditScore REAL,
                PreviousFraudHistory INTEGER,
                RiskLevel TEXT DEFAULT 'Unscored'
            )
        """)
        cur.execute("""
            CREATE TABLE DimTime (
                TimeKey INTEGER PRIMARY KEY AUTOINCREMENT,
                FullTimestamp TEXT UNIQUE,
                Date TEXT, Month INTEGER, Quarter INTEGER, Year INTEGER, Hour INTEGER
            )
        """)
        cur.execute("""
            CREATE TABLE DimLocation (
                LocationKey INTEGER PRIMARY KEY AUTOINCREMENT,
                City TEXT UNIQUE
            )
        """)
        cur.execute("""
            CREATE TABLE DimTransactionType (
                TransactionTypeKey INTEGER PRIMARY KEY AUTOINCREMENT,
                TransactionType TEXT UNIQUE
            )
        """)
        cur.execute("""
            CREATE TABLE FactTransactions (
                TransactionID TEXT PRIMARY KEY,
                CustomerKey INTEGER,
                TimeKey INTEGER,
                LocationKey INTEGER,
                TransactionTypeKey INTEGER,
                AccountBalance REAL,
                TransactionAmount REAL,
                DeviceUsed TEXT,
                DailyTransactionCount INTEGER,
                FraudFlag INTEGER,
                FOREIGN KEY (CustomerKey) REFERENCES DimCustomer(CustomerKey),
                FOREIGN KEY (TimeKey) REFERENCES DimTime(TimeKey),
                FOREIGN KEY (LocationKey) REFERENCES DimLocation(LocationKey),
                FOREIGN KEY (TransactionTypeKey) REFERENCES DimTransactionType(TransactionTypeKey)
            )
        """)
        conn.commit()

        # --- DimCustomer ---
        cust_cols = ["CustomerID", "Age", "Gender", "Occupation", "Income", "CreditScore", "PreviousFraudHistory"]
        cust_cols = [c for c in cust_cols if c in df.columns]
        dim_customer = df[cust_cols].drop_duplicates(subset=["CustomerID"]).reset_index(drop=True)
        dim_customer.to_sql("DimCustomer", conn, if_exists="append", index=False)

        # --- DimTime ---
        df["Date"] = df["Timestamp"].dt.date.astype(str)
        df["Month"] = df["Timestamp"].dt.month
        df["Quarter"] = df["Timestamp"].dt.quarter
        df["Year"] = df["Timestamp"].dt.year
        df["Hour"] = df["Timestamp"].dt.hour
        df["FullTimestamp"] = df["Timestamp"].astype(str)
        dim_time = df[["FullTimestamp", "Date", "Month", "Quarter", "Year", "Hour"]].drop_duplicates(
            subset=["FullTimestamp"]).reset_index(drop=True)
        dim_time.to_sql("DimTime", conn, if_exists="append", index=False)

        # --- DimLocation ---
        dim_location = pd.DataFrame({"City": df["Location"].dropna().unique()})
        dim_location.to_sql("DimLocation", conn, if_exists="append", index=False)

        # --- DimTransactionType ---
        dim_ttype = pd.DataFrame({"TransactionType": df["TransactionType"].dropna().unique()})
        dim_ttype.to_sql("DimTransactionType", conn, if_exists="append", index=False)

        # --- lookups for fact table ---
        cust_map = pd.read_sql("SELECT CustomerKey, CustomerID FROM DimCustomer", conn).set_index("CustomerID")["CustomerKey"]
        time_map = pd.read_sql("SELECT TimeKey, FullTimestamp FROM DimTime", conn).set_index("FullTimestamp")["TimeKey"]
        loc_map = pd.read_sql("SELECT LocationKey, City FROM DimLocation", conn).set_index("City")["LocationKey"]
        type_map = pd.read_sql("SELECT TransactionTypeKey, TransactionType FROM DimTransactionType", conn).set_index("TransactionType")["TransactionTypeKey"]

        fact = pd.DataFrame()
        fact["TransactionID"] = df["TransactionID"]
        fact["CustomerKey"] = df["CustomerID"].map(cust_map)
        fact["TimeKey"] = df["FullTimestamp"].map(time_map)
        fact["LocationKey"] = df["Location"].map(loc_map)
        fact["TransactionTypeKey"] = df["TransactionType"].map(type_map)
        fact["AccountBalance"] = df.get("AccountBalance")
        fact["TransactionAmount"] = df["TransactionAmount"]
        fact["DeviceUsed"] = df.get("DeviceUsed")
        fact["DailyTransactionCount"] = df.get("DailyTransactionCount")
        fact["FraudFlag"] = (df["Fraud"].astype(str).str.strip().str.lower() == "yes").astype(int)

        fact = fact.drop_duplicates(subset=["TransactionID"])
        fact.to_sql("FactTransactions", conn, if_exists="append", index=False)
        conn.commit()

    # The warehouse was just rebuilt — drop any cached denormalized view.
    get_fact_with_dims.clear()

    summary = {
        "clean_report": clean_report,
        "n_customers": len(dim_customer),
        "n_transactions": len(fact),
        "n_locations": len(dim_location),
        "n_txn_types": len(dim_ttype),
        "n_fraud": int(fact["FraudFlag"].sum()),
        "fraud_rate": round(fact["FraudFlag"].mean() * 100, 2) if len(fact) else 0,
    }
    return summary


def update_customer_risk(risk_map: dict):
    """risk_map: {CustomerID: RiskLevel string}"""
    with closing(get_connection()) as conn, closing(conn.cursor()) as cur:
        for cust_id, risk in risk_map.items():
            cur.execute("UPDATE DimCustomer SET RiskLevel = ? WHERE CustomerID = ?", (risk, cust_id))
        conn.commit()
    # RiskLevel changed — invalidate the cached denormalized view.
    get_fact_with_dims.clear()


@st.cache_data(show_spinner=False)
def get_fact_with_dims() -> pd.DataFrame:
    """Convenience: returns a denormalized view joining fact + all dims, for analytics/plotting.

    Cached so repeated Streamlit reruns don't re-run the join on every interaction;
    the cache is cleared by build_warehouse() and update_customer_risk() when the data changes.
    """
    query = """
        SELECT f.TransactionID, f.TransactionAmount, f.AccountBalance, f.DeviceUsed,
               f.DailyTransactionCount, f.FraudFlag,
               c.CustomerID, c.Age, c.Gender, c.Occupation, c.Income, c.CreditScore,
               c.PreviousFraudHistory, c.RiskLevel,
               t.Date, t.Month, t.Quarter, t.Year, t.Hour, t.FullTimestamp,
               l.City AS Location,
               tt.TransactionType
        FROM FactTransactions f
        LEFT JOIN DimCustomer c ON f.CustomerKey = c.CustomerKey
        LEFT JOIN DimTime t ON f.TimeKey = t.TimeKey
        LEFT JOIN DimLocation l ON f.LocationKey = l.LocationKey
        LEFT JOIN DimTransactionType tt ON f.TransactionTypeKey = tt.TransactionTypeKey
    """
    with closing(get_connection()) as conn:
        return pd.read_sql(query, conn)


def warehouse_exists() -> bool:
    if not os.path.exists(DB_PATH):
        return False
    with closing(get_connection()) as conn, closing(conn.cursor()) as cur:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='FactTransactions'")
        exists = cur.fetchone() is not None
        if exists:
            cur.execute("SELECT COUNT(*) FROM FactTransactions")
            exists = cur.fetchone()[0] > 0
    return exists
