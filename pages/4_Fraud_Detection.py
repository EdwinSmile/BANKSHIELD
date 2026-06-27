import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "utils"))
from ui_helpers import inject_css, explain, pbi_layout, get_theme, chart_type_toggle
from etl import warehouse_exists, get_fact_with_dims
from ml_models import train_fraud_model

inject_css()
theme = get_theme()

st.title("Fraud Detection")
explain(
    "This page trains an AI model that learns from past transactions to predict whether a "
    "new transaction is likely fraudulent. Think of it as a smart assistant that flags suspicious "
    "activity for a human to review."
)

if not warehouse_exists():
    st.warning("No cleaned dataset found. Please complete the **Preprocessing** step first.")
    st.page_link("pages/2_Preprocessing.py", label="Go to Preprocessing")
    st.stop()

df = get_fact_with_dims()

st.markdown("### Step 1 — Choose a model")
col1, col2 = st.columns([1, 2])
with col1:
    algorithm = st.radio(
        "Which algorithm should we use?",
        ["Random Forest", "Decision Tree"],
        index=0,
        help="Random Forest is usually more accurate. Decision Tree is simpler and easier to explain."
    )
with col2:
    if algorithm == "Random Forest":
        st.caption(
            "**Random Forest** combines many decision trees and 'votes' on the answer. "
            "Pros: high accuracy, resistant to overfitting. Best for production use."
        )
    else:
        st.caption(
            "**Decision Tree** asks a series of yes/no questions (e.g. 'Is the amount over $1,000?'). "
            "Pros: easy to interpret and explain to others, very fast."
        )

if st.button("Train Fraud Detection Model", type="primary", use_container_width=True):
    with st.spinner("Training the model... this may take a few seconds."):
        result = train_fraud_model(df, algorithm=algorithm)
    st.session_state["fraud_model_result"] = result
    st.success("Model trained successfully.")

if "fraud_model_result" in st.session_state:
    result = st.session_state["fraud_model_result"]
    metrics = result["metrics"]

    st.markdown("---")
    st.markdown(f"### Results — {result['algorithm']}")
    explain(
        "<b>Accuracy</b> = overall correctness. <b>Precision</b> = of the transactions we flagged as "
        "fraud, how many really were. <b>Recall</b> = of all the real fraud cases, how many we caught. "
        "<b>F1 Score</b> balances precision and recall into one number."
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Accuracy", f"{metrics['accuracy']*100:.1f}%")
    m2.metric("Precision", f"{metrics['precision']*100:.1f}%")
    m3.metric("Recall", f"{metrics['recall']*100:.1f}%")
    m4.metric("F1 Score", f"{metrics['f1']*100:.1f}%")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Confusion Matrix**")
        st.caption("How predictions compare to what actually happened, on a held-out test set.")
        cm = metrics["confusion_matrix"]
        fig = go.Figure(data=go.Heatmap(
            z=cm,
            x=["Predicted: Legitimate", "Predicted: Fraud"],
            y=["Actual: Legitimate", "Actual: Fraud"],
            colorscale=[[0, "#FFFFFF"], [1, theme["accent"]]],
            text=cm, texttemplate="%{text}", showscale=False,
            xgap=2, ygap=2
        ))
        pbi_layout(fig, height=350)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        if "roc_fpr" in metrics:
            st.markdown("**ROC Curve**")
            st.caption(f"Measures how well the model separates fraud from non-fraud. AUC = {metrics['auc']:.3f} (closer to 1.0 is better).")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=metrics["roc_fpr"], y=metrics["roc_tpr"], mode="lines",
                                      line=dict(color=theme["accent"], width=3), name="Model"))
            fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines",
                                      line=dict(color=theme["subtext"], dash="dash"), name="Random guess"))
            pbi_layout(fig, height=350)
            fig.update_layout(xaxis_title="False Positive Rate", yaxis_title="True Positive Rate")
            st.plotly_chart(fig, use_container_width=True)

    if result["feature_importance"] is not None:
        st.markdown("**What factors matter most for predicting fraud?**")
        view = chart_type_toggle("View as", ["Horizontal Bar", "Vertical Bar"], key="feature_importance")
        fi = result["feature_importance"].head(8)
        if view == "Vertical Bar":
            fig = px.bar(fi, x="Feature", y="Importance", color_discrete_sequence=[theme["accent"]])
            fig.update_layout(xaxis={"categoryorder": "total descending"}, showlegend=False)
        else:
            fig = px.bar(fi, x="Importance", y="Feature", orientation="h",
                          color_discrete_sequence=[theme["accent"]])
            fig.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
        pbi_layout(fig, height=350)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Longer bars mean the model relies on that factor more heavily when spotting fraud.")

    st.markdown("---")
    st.markdown("### Transactions Flagged as Fraud")
    preds = result["predictions"]
    flagged = preds[preds["PredictedFraud"] == 1].sort_values("FraudProbability", ascending=False)
    explain(f"The model flagged **{len(flagged):,}** transactions as likely fraud, out of {len(preds):,} total.")
    if "InTestSet" in preds.columns:
        n_test_flagged = int(flagged["InTestSet"].sum())
        st.caption(
            "This list covers **all** transactions, including the ~75% the model trained on, "
            "so it looks more accurate here than it would on brand-new data. "
            f"{n_test_flagged:,} of these flags come from the held-out test set the model never "
            "saw — the Accuracy / Precision / Recall figures above are measured only on that "
            "held-out set, so those are the honest numbers to judge it by."
        )
    display_flagged = flagged.copy()
    display_flagged["FraudProbability"] = (display_flagged["FraudProbability"] * 100).round(1).astype(str) + "%"
    display_flagged["ActualFraud"] = display_flagged["ActualFraud"].map({1: "Yes", 0: "No"})
    st.dataframe(
        display_flagged[["TransactionID", "CustomerID", "FraudProbability", "ActualFraud"]].head(200),
        use_container_width=True, hide_index=True
    )

    st.markdown("---")
    st.page_link("pages/5_Customer_Risk.py", label="Continue to Customer Risk")
