import streamlit as st
import pandas as pd
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "utils"))
from ui_helpers import inject_css, explain, kpi_card, hero_banner, next_step_card, ring_gauge, gauge_card
from etl import warehouse_exists, get_fact_with_dims

inject_css()

hero_banner(
    eyebrow="AI-powered fraud & risk platform",
    title="Clean data, catch fraud, know your risk.",
    subtitle=(
        "BankShield cleans transaction data, trains ML models to flag fraud, and groups customers "
        "into risk tiers — with interactive charts and downloadable reports. No coding or data "
        "science background needed."
    ),
)

if not warehouse_exists():
    st.warning(
        "No dataset has been loaded yet. Go to the **Dataset** page in the sidebar to "
        "upload your own file or try the built-in sample dataset."
    )
    st.markdown("### How this dashboard works")
    steps = [
        ("Dataset", "Upload your transaction file (or use our sample data)"),
        ("Preprocessing", "We clean the data automatically (missing values, duplicates)"),
        ("Data Exploration", "See summary charts and patterns"),
        ("Fraud Detection", "An AI model flags transactions that look fraudulent"),
        ("Customer Risk", "Customers are grouped into Low / Medium / High risk"),
        ("Reports", "Download a summary of everything"),
    ]
    cols = st.columns(3)
    for i, (title, caption) in enumerate(steps):
        with cols[i % 3]:
            next_step_card(f"{i+1}. {title}", caption)
            st.write("")
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
    c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 1.1])
    with c1:
        kpi_card("Total Customers", f"{n_customers:,}", icon="👥")
    with c2:
        kpi_card("Total Transactions", f"{n_txns:,}", icon="💳")
    with c3:
        kpi_card("Fraudulent Transactions", f"{n_fraud:,}", icon="🚨")
    with c4:
        kpi_card("High-Risk Customers", f"{high_risk:,}" if isinstance(high_risk, int) else high_risk, icon="⚠️")
    with c5:
        gauge_card(ring_gauge(fraud_rate, subtitle="Fraud Rate"), "Fraud Rate")

    st.markdown("---")
    st.markdown("### What's next?")
    colA, colB, colC = st.columns(3)
    with colA:
        next_step_card("🔎 Explore the data", "See charts of fraud patterns, customer trends, and correlations.")
        st.write("")
        st.page_link("pages/3_Exploration.py", label="Go to Data Exploration →")
    with colB:
        next_step_card("🤖 Detect fraud", "Train an AI model to flag suspicious transactions automatically.")
        st.write("")
        st.page_link("pages/4_Fraud_Detection.py", label="Go to Fraud Detection →")
    with colC:
        next_step_card("📊 Score customer risk", "Group customers into Low, Medium, and High risk segments.")
        st.write("")
        st.page_link("pages/5_Customer_Risk.py", label="Go to Customer Risk →")

st.markdown("---")
st.caption("BankShield v1.0 · Built with Streamlit · Data stays local in your own SQLite database")
