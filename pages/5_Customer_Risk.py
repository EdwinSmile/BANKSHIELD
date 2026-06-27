import streamlit as st
import pandas as pd
import plotly.express as px
import html
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "utils"))
from ui_helpers import inject_css, explain, risk_badge, pbi_layout, get_color_maps, chart_type_toggle
from etl import warehouse_exists, get_fact_with_dims, update_customer_risk
from ml_models import run_customer_clustering

inject_css()
RISK_COLOR_MAP, FRAUD_COLOR_MAP = get_color_maps()

st.title("Customer Risk Segmentation")
explain(
    "Instead of looking at one transaction at a time, this page groups <b>customers</b> into risk "
    "tiers — Low, Medium, and High — based on their overall behavior. This helps risk officers "
    "prioritize who to monitor closely."
)

if not warehouse_exists():
    st.warning("No cleaned dataset found. Please complete the **Preprocessing** step first.")
    st.page_link("pages/2_Preprocessing.py", label="Go to Preprocessing")
    st.stop()

df = get_fact_with_dims()

st.markdown("### Step 1 — Choose number of risk groups")
n_clusters = st.slider(
    "Number of customer groups (clusters)", min_value=2, max_value=5, value=3,
    help="3 groups (Low/Medium/High) is the standard banking convention."
)

if st.button("Run Customer Risk Clustering", type="primary", use_container_width=True):
    with st.spinner("Grouping customers by behavior..."):
        result = run_customer_clustering(df, n_clusters=n_clusters)
        update_customer_risk(dict(zip(
            result["customer_clusters"]["CustomerID"], result["customer_clusters"]["RiskLevel"]
        )))
    st.session_state["cluster_result"] = result
    st.success("Customers grouped successfully.")

if "cluster_result" in st.session_state:
    result = st.session_state["cluster_result"]
    clusters = result["customer_clusters"]
    profile = result["cluster_profile"]

    st.markdown("---")
    st.markdown("### Risk Group Summary")
    cols = st.columns(len(profile))
    for i, (_, row) in enumerate(profile.iterrows()):
        with cols[i]:
            st.markdown(f"#### {risk_badge(row['RiskLevel'])}", unsafe_allow_html=True)
            st.metric("Customers", f"{int(row['Count']):,}")
            st.caption(f"Avg. transaction: ${row['AvgAmount']:,.0f}")
            st.caption(f"Avg. fraud cases: {row['AvgFraudCount']:.2f}")
            st.caption(f"Avg. credit score: {row['AvgCreditScore']:.0f}")

    st.markdown("---")
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("**Customer Distribution by Risk Level**")
        view = chart_type_toggle("View as", ["Pie", "Bar"], key="risk_distribution")
        dist = clusters["RiskLevel"].value_counts().reset_index()
        dist.columns = ["RiskLevel", "Count"]
        if view == "Bar":
            fig = px.bar(dist, x="RiskLevel", y="Count", color="RiskLevel",
                         color_discrete_map=RISK_COLOR_MAP)
            fig.update_layout(showlegend=False)
        else:
            fig = px.pie(dist, names="RiskLevel", values="Count", hole=0.45,
                         color="RiskLevel", color_discrete_map=RISK_COLOR_MAP)
        pbi_layout(fig)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("**Risk Groups: Spending vs Balance**")
        view = chart_type_toggle("View as", ["Scatter", "Box Plot"], key="risk_spend_balance")
        if view == "Box Plot":
            fig = px.box(clusters, x="RiskLevel", y="TransactionAmount", color="RiskLevel",
                         color_discrete_map=RISK_COLOR_MAP)
            fig.update_layout(showlegend=False)
        else:
            fig = px.scatter(
                clusters, x="AccountBalance", y="TransactionAmount", color="RiskLevel",
                color_discrete_map=RISK_COLOR_MAP,
                opacity=0.6, hover_data=["CustomerID"]
            )
        pbi_layout(fig)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Each dot is a customer. High-risk customers often show large transactions relative to balance.")

    st.markdown("---")
    st.markdown("### What does each risk group mean?")
    for _, row in profile.iterrows():
        level = row["RiskLevel"]
        with st.expander(f"{level} — {int(row['Count'])} customers"):
            if "Low" in level:
                st.markdown("""
                - Stable account balances
                - Low/typical transaction amounts
                - No or minimal fraud history
                - **Recommended action:** Standard monitoring
                """)
            elif "Medium" in level:
                st.markdown("""
                - Moderate spending levels
                - Occasional unusual activity
                - Average balances
                - **Recommended action:** Periodic review
                """)
            else:
                st.markdown("""
                - Large transaction amounts relative to balance
                - Frequent transfers
                - Previous fraud history present
                - **Recommended action:** Priority review by a fraud analyst
                """)

    st.markdown("---")
    st.markdown("### Customer-Level Detail")
    display_clusters = clusters[["CustomerID", "RiskLevel", "TransactionAmount",
                                 "AccountBalance", "CreditScore", "FraudFlag"]].copy()
    # We render this table with escape=False so the colored risk badge (trusted HTML
    # built from fixed risk-tier labels) shows. That means every other cell is rendered
    # as raw HTML too — so escape the user-supplied CustomerID first, otherwise a crafted
    # value (e.g. from an uploaded CSV/PDF) could inject HTML/JS into the dashboard.
    display_clusters["CustomerID"] = display_clusters["CustomerID"].astype(str).map(html.escape)
    display_clusters["RiskLevel"] = display_clusters["RiskLevel"].apply(risk_badge)
    st.write(
        display_clusters
        .rename(columns={"FraudFlag": "FraudCasesFound"})
        .head(200)
        .to_html(escape=False, index=False),
        unsafe_allow_html=True
    )

    st.markdown("---")
    st.page_link("pages/6_Reports.py", label="Continue to Reports")
