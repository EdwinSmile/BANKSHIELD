import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "utils"))
from ui_helpers import inject_css, explain, pbi_layout, get_color_maps
from etl import warehouse_exists, get_fact_with_dims

inject_css()
RISK_COLOR_MAP, FRAUD_COLOR_MAP = get_color_maps()

st.title("Reports")
explain(
    "A one-page summary of everything the dashboard found — great for sharing with managers or "
    "compliance teams. You can download the data below as a CSV file."
)

if not warehouse_exists():
    st.warning("No cleaned dataset found. Please complete the **Preprocessing** step first.")
    st.page_link("pages/2_Preprocessing.py", label="Go to Preprocessing")
    st.stop()

df = get_fact_with_dims()
n_customers = df["CustomerID"].nunique()
n_txns = len(df)
n_fraud = int(df["FraudFlag"].sum())
fraud_rate = (n_fraud / n_txns * 100) if n_txns else 0

has_risk = "RiskLevel" in df.columns and df["RiskLevel"].nunique() > 1
if has_risk:
    risk_counts = df.drop_duplicates("CustomerID")["RiskLevel"].value_counts()

st.markdown(f"**Report generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
st.markdown(f"**Dataset:** {st.session_state.get('dataset_source', 'Unknown')}")

st.markdown("---")
st.markdown("### Executive Summary")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Customers", f"{n_customers:,}")
m2.metric("Total Transactions", f"{n_txns:,}")
m3.metric("Fraudulent Transactions", f"{n_fraud:,}")
m4.metric("Fraud Rate", f"{fraud_rate:.2f}%")

if has_risk:
    st.markdown("### Customer Risk Breakdown")
    rc1, rc2 = st.columns([1, 2])
    with rc1:
        st.dataframe(risk_counts.rename("Customers"), width="stretch")
    with rc2:
        fig = px.bar(risk_counts.reset_index(), x="RiskLevel", y="count" if "count" in risk_counts.reset_index().columns else "RiskLevel",
                      color="RiskLevel",
                      color_discrete_map=RISK_COLOR_MAP)
        pbi_layout(fig, height=300)
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, width="stretch")
else:
    st.info("Run the **Customer Risk** page to include risk segmentation in this report.")

st.markdown("---")
st.markdown("### Fraud by Transaction Type")
fraud_by_type = df[df["FraudFlag"] == 1]["TransactionType"].value_counts().reset_index()
fraud_by_type.columns = ["TransactionType", "FraudCount"]
st.dataframe(fraud_by_type, width="stretch", hide_index=True)

st.markdown("---")
st.markdown("### Top Locations by Fraud")
fraud_by_loc = df[df["FraudFlag"] == 1]["Location"].value_counts().head(10).reset_index()
fraud_by_loc.columns = ["Location", "FraudCount"]
st.dataframe(fraud_by_loc, width="stretch", hide_index=True)

st.markdown("---")
st.markdown("### Download Data")

dl1, dl2, dl3 = st.columns(3)
with dl1:
    csv_full = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download Full Dataset (CSV)", csv_full, "bankshield_full_data.csv", "text/csv", width="stretch")
with dl2:
    fraud_only = df[df["FraudFlag"] == 1]
    csv_fraud = fraud_only.to_csv(index=False).encode("utf-8")
    st.download_button("Download Flagged Fraud (CSV)", csv_fraud, "bankshield_fraud_transactions.csv", "text/csv", width="stretch")
with dl3:
    if has_risk:
        risk_summary = df.drop_duplicates("CustomerID")[["CustomerID", "RiskLevel"]]
        csv_risk = risk_summary.to_csv(index=False).encode("utf-8")
        st.download_button("Download Customer Risk List (CSV)", csv_risk, "bankshield_customer_risk.csv", "text/csv", width="stretch")
    else:
        st.button("Customer Risk List (run Customer Risk page first)", disabled=True, width="stretch")

st.markdown("---")
st.caption("This report was generated automatically by BankShield. Figures reflect the currently loaded dataset.")
