import streamlit as st
import pandas as pd
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "utils"))
from ui_helpers import inject_css, explain, kpi_card
from etl import warehouse_exists, get_fact_with_dims

inject_css()

st.title("BankShield")
st.subheader("Banking Fraud Detection & Customer Risk Dashboard")

explain(
    "Welcome! This dashboard helps you spot suspicious banking transactions and "
    "understand which customers carry more risk — no coding or data science background needed. "
    "Start with the <b>Dataset</b> page in the sidebar to load your data, then move through the "
    "steps in order."
)

if not warehouse_exists():
    st.warning(
        "No dataset has been loaded yet. Go to the **Dataset** page in the sidebar to "
        "upload your own file or try the built-in sample dataset."
    )
    st.markdown("### How this dashboard works")
    st.markdown("""
    1. **Dataset** — Upload your transaction file (or use our sample data)
    2. **Preprocessing** — We clean the data automatically (missing values, duplicates)
    3. **Data Exploration** — See summary charts and patterns
    4. **Fraud Detection** — An AI model flags transactions that look fraudulent
    5. **Customer Risk** — Customers are grouped into Low / Medium / High risk
    6. **Reports** — Download a summary of everything
    """)
else:
    df = get_fact_with_dims()
    n_customers = df["CustomerID"].nunique()
    n_txns = len(df)
    n_fraud = int(df["FraudFlag"].sum())
    fraud_rate = (n_fraud / n_txns * 100) if n_txns else 0
    unique_cust = df.drop_duplicates("CustomerID")
    # RiskLevel always exists (defaults to 'Unscored'); only report a count once the
    # Customer Risk page has actually scored customers, otherwise say so.
    if "RiskLevel" in df.columns and (unique_cust["RiskLevel"] != "Unscored").any():
        high_risk = int((unique_cust["RiskLevel"] == "High Risk").sum())
    else:
        high_risk = "Not yet scored"

    st.markdown("### Key numbers at a glance")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        kpi_card("Total Customers", f"{n_customers:,}")
    with c2:
        kpi_card("Total Transactions", f"{n_txns:,}")
    with c3:
        kpi_card("Fraudulent Transactions", f"{n_fraud:,}")
    with c4:
        kpi_card("High-Risk Customers", f"{high_risk:,}" if isinstance(high_risk, int) else high_risk)
    with c5:
        kpi_card("Fraud Rate", f"{fraud_rate:.2f}%")

    st.markdown("---")
    st.markdown("### What's next?")
    colA, colB, colC = st.columns(3)
    with colA:
        st.markdown("**Explore the data**")
        st.caption("See charts of fraud patterns, customer trends, and correlations.")
        st.page_link("pages/3_Exploration.py", label="Go to Data Exploration")
    with colB:
        st.markdown("**Detect fraud**")
        st.caption("Train an AI model to flag suspicious transactions automatically.")
        st.page_link("pages/4_Fraud_Detection.py", label="Go to Fraud Detection")
    with colC:
        st.markdown("**Score customer risk**")
        st.caption("Group customers into Low, Medium, and High risk segments.")
        st.page_link("pages/5_Customer_Risk.py", label="Go to Customer Risk")

st.markdown("---")
st.caption("BankShield v1.0 · Built with Streamlit · Data stays local in your own SQLite database")
