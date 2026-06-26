import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "utils"))
from ui_helpers import (
    inject_css, explain, pbi_layout, get_theme, get_color_maps,
    get_heatmap_scale, chart_type_toggle
)
from etl import warehouse_exists, get_fact_with_dims

inject_css()
theme = get_theme()
RISK_COLOR_MAP, FRAUD_COLOR_MAP = get_color_maps()

st.title("Data Exploration")
explain(
    "Here you can visually explore patterns in your transaction data — no need to read raw numbers. "
    "Each chart below answers a simple question about your data. Use the buttons above a chart to "
    "switch how it's displayed."
)

if not warehouse_exists():
    st.warning("No cleaned dataset found. Please complete the **Preprocessing** step first.")
    st.page_link("pages/2_Preprocessing.py", label="Go to Preprocessing")
    st.stop()

df = get_fact_with_dims()
df["FraudLabel"] = df["FraudFlag"].map({1: "Fraudulent", 0: "Legitimate"})

# ---------------- Summary statistics ----------------
st.markdown("### Summary Statistics")
explain("These numbers describe your transaction amounts in plain terms — useful for spotting unusually large transactions.")

numeric_summary = df[["TransactionAmount", "AccountBalance", "Age", "CreditScore"]].agg(
    ["mean", "median", "max", "min", "std"]
).T
numeric_summary.columns = ["Mean", "Median", "Maximum", "Minimum", "Std. Deviation"]
numeric_summary = numeric_summary.round(2)
st.dataframe(numeric_summary, use_container_width=True)

st.markdown("---")

# ---------------- Frequency tables ----------------
st.markdown("### Frequency Tables")
f1, f2, f3 = st.columns(3)
with f1:
    st.markdown("**Transaction Type**")
    st.dataframe(df["TransactionType"].value_counts().rename("Count"), use_container_width=True)
with f2:
    st.markdown("**Fraud Status**")
    st.dataframe(df["FraudLabel"].value_counts().rename("Count"), use_container_width=True)
with f3:
    st.markdown("**Customer Occupation**")
    st.dataframe(df["Occupation"].value_counts().rename("Count"), use_container_width=True)

st.markdown("---")

# ---------------- Charts ----------------
st.markdown("### Visual Patterns")

c1, c2 = st.columns(2)

with c1:
    st.markdown("**Fraud Cases by Transaction Type**")
    view = chart_type_toggle("View as", ["Bar", "Pie"], key="fraud_by_type")
    fraud_by_type = df[df["FraudFlag"] == 1]["TransactionType"].value_counts().reset_index()
    fraud_by_type.columns = ["TransactionType", "Count"]
    if view == "Pie":
        fig = px.pie(fraud_by_type, names="TransactionType", values="Count", hole=0.45,
                     color_discrete_sequence=theme["palette"])
    else:
        fig = px.bar(fraud_by_type, x="TransactionType", y="Count", color="TransactionType",
                     color_discrete_sequence=theme["palette"])
        fig.update_layout(showlegend=False)
    pbi_layout(fig)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Shows which type of transaction (deposit, withdrawal, etc.) fraud happens most in.")

with c2:
    st.markdown("**Fraudulent vs Legitimate Transactions**")
    view = chart_type_toggle("View as", ["Pie", "Bar"], key="fraud_split")
    pie_data = df["FraudLabel"].value_counts().reset_index()
    pie_data.columns = ["Status", "Count"]
    if view == "Bar":
        fig = px.bar(pie_data, x="Status", y="Count", color="Status",
                     color_discrete_map=FRAUD_COLOR_MAP)
        fig.update_layout(showlegend=False)
    else:
        fig = px.pie(pie_data, names="Status", values="Count", hole=0.45,
                     color="Status", color_discrete_map=FRAUD_COLOR_MAP)
    pbi_layout(fig)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("The overall split between fraud and normal activity.")

c3, c4 = st.columns(2)

with c3:
    st.markdown("**Fraud Trend Over Time**")
    view = chart_type_toggle("View as", ["Line", "Area", "Bar"], key="fraud_trend")
    trend = df.groupby("Date")["FraudFlag"].sum().reset_index()
    trend["Date"] = pd.to_datetime(trend["Date"])
    trend = trend.sort_values("Date")
    if view == "Area":
        fig = px.area(trend, x="Date", y="FraudFlag")
        fig.update_traces(line_color=theme["red"], fillcolor=theme["red"])
    elif view == "Bar":
        fig = px.bar(trend, x="Date", y="FraudFlag")
        fig.update_traces(marker_color=theme["red"])
    else:
        fig = px.line(trend, x="Date", y="FraudFlag", markers=False)
        fig.update_traces(line_color=theme["red"])
    pbi_layout(fig)
    fig.update_layout(yaxis_title="Fraud Cases")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("How fraud cases have moved over time — spikes may indicate fraud waves or attacks.")

with c4:
    st.markdown("**Transaction Amount Distribution**")
    view = chart_type_toggle("View as", ["Histogram", "Box Plot"], key="amount_dist")
    if view == "Box Plot":
        fig = px.box(df, x="FraudLabel", y="TransactionAmount", color="FraudLabel",
                     color_discrete_map=FRAUD_COLOR_MAP)
        fig.update_layout(showlegend=False)
    else:
        fig = px.histogram(df, x="TransactionAmount", nbins=50, color="FraudLabel",
                            color_discrete_map=FRAUD_COLOR_MAP,
                            barmode="overlay", opacity=0.7)
    pbi_layout(fig)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Most transactions are small; fraud often appears at higher amounts.")

c5, c6 = st.columns(2)

with c5:
    st.markdown("**Customer Age vs Transaction Amount**")
    view = chart_type_toggle("View as", ["Scatter", "Density"], key="age_vs_amount")
    sample_df = df.sample(min(3000, len(df)), random_state=1)
    if view == "Density":
        fig = px.density_contour(sample_df, x="Age", y="TransactionAmount", color="FraudLabel",
                                  color_discrete_map=FRAUD_COLOR_MAP)
    else:
        fig = px.scatter(sample_df, x="Age", y="TransactionAmount", color="FraudLabel",
                          color_discrete_map=FRAUD_COLOR_MAP,
                          opacity=0.5)
    pbi_layout(fig)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Each colored point or line is a transaction — fraud is highlighted separately. Look for clusters in certain age groups.")

with c6:
    st.markdown("**Feature Correlation Heat Map**")
    corr_cols = ["TransactionAmount", "Age", "AccountBalance", "CreditScore", "DailyTransactionCount", "FraudFlag"]
    corr = df[corr_cols].corr().round(2)
    fig = go.Figure(data=go.Heatmap(
        z=corr.values, x=corr.columns, y=corr.columns,
        colorscale=get_heatmap_scale(), zmid=0,
        text=corr.values, texttemplate="%{text}",
        xgap=2, ygap=2
    ))
    pbi_layout(fig)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Shows how strongly different factors move together. Closer to 1 or -1 means a stronger relationship.")

st.markdown("---")
st.page_link("pages/4_Fraud_Detection.py", label="Continue to Fraud Detection")
