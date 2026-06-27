import streamlit as st
import pandas as pd
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "utils"))
from ui_helpers import inject_css, explain
from etl import build_warehouse

inject_css()

st.title("Data Preprocessing")
explain(
    "Real-world data is messy — missing numbers, duplicate rows, inconsistent labels. "
    "This step cleans your data automatically so the AI models later get accurate results. "
    "You don't need to do anything technical here; just choose how you'd like missing values handled."
)

if "raw_df" not in st.session_state:
    st.warning("No dataset loaded yet. Please go to the **Dataset** page first.")
    st.page_link("pages/1_Dataset.py", label="Go to Dataset page")
    st.stop()

df = st.session_state["raw_df"]

st.markdown("### Step 1 — Choose how to fill in missing values")
col1, col2 = st.columns([1, 2])
with col1:
    strategy_label = st.radio(
        "Missing number fields will be filled using:",
        ["Median (middle value, recommended)", "Mean (average)", "Mode (most common value)"],
        index=0
    )
    strategy_map = {
        "Median (middle value, recommended)": "median",
        "Mean (average)": "mean",
        "Mode (most common value)": "mode",
    }
    strategy = strategy_map[strategy_label]

with col2:
    st.markdown("**Why this matters:**")
    st.caption(
        "- **Median** is safest when a few unusually large/small values (outliers) exist — common in banking amounts.\n"
        "- **Mean** works well when the data is fairly evenly distributed.\n"
        "- **Mode** is best for categories, not really numbers — included for completeness."
    )

missing_summary = df.isna().sum()
missing_summary = missing_summary[missing_summary > 0]

st.markdown("### Step 2 — Review what will be cleaned")
c1, c2 = st.columns(2)
with c1:
    st.markdown("**Missing values detected:**")
    if len(missing_summary) > 0:
        st.dataframe(missing_summary.rename("Missing Count"), use_container_width=True)
    else:
        st.success("No missing values found.")
with c2:
    st.markdown("**Duplicate transactions detected:**")
    n_dupes = int(df.duplicated().sum())
    if n_dupes > 0:
        st.warning(f"{n_dupes} duplicate rows will be removed.")
    else:
        st.success("No duplicate rows found.")

st.markdown("### Step 3 — Run the cleanup")
explain(
    "Clicking the button below will: fill missing values, remove duplicate transactions, "
    "standardize timestamps, and load everything into the data warehouse used by the rest "
    "of the dashboard."
)

if st.button("Clean & Build Data Warehouse", type="primary", use_container_width=True):
    with st.spinner("Cleaning data and building the warehouse... this takes a few seconds."):
        summary = build_warehouse(df, missing_strategy=strategy)
    st.session_state["warehouse_summary"] = summary
    st.success("Done. Your data has been cleaned and loaded.")

if "warehouse_summary" in st.session_state:
    summary = st.session_state["warehouse_summary"]
    report = summary["clean_report"]

    st.markdown("---")
    st.markdown("### Cleaning Summary")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Rows before", f"{report['rows_before']:,}")
    m2.metric("Duplicates removed", f"{report['duplicates_found']:,}")
    m3.metric("Rows after cleaning", f"{report['rows_after_dedup']:,}")
    m4.metric("Strategy used", report["strategy_used"].title())

    if report["missing_values_filled"]:
        st.markdown("**Missing values filled per column:**")
        fill_df = pd.DataFrame(
            list(report["missing_values_filled"].items()), columns=["Column", "Values Filled"]
        )
        st.dataframe(fill_df, use_container_width=True, hide_index=True)

    st.caption(
        "Text categories (like Gender or Transaction Type) are stored as-is in the warehouse "
        "and converted into a machine-readable form automatically when you train a model on "
        "the Fraud Detection page."
    )

    st.success(
        f"Warehouse built: **{summary['n_customers']:,}** customers, "
        f"**{summary['n_transactions']:,}** transactions, **{summary['n_fraud']:,}** flagged as fraud "
        f"({summary['fraud_rate']}%)."
    )

    st.markdown("---")
    st.page_link("pages/3_Exploration.py", label="Continue to Data Exploration")
