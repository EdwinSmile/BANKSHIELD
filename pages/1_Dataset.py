import streamlit as st
import pandas as pd
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "utils"))
from ui_helpers import inject_css, explain, validate_columns, ensure_optional_columns, REQUIRED_COLUMNS, kpi_card
from pdf_extract import extract_tables_from_pdf, auto_map_columns

inject_css()

st.title("Dataset")
explain(
    "Upload your bank's transaction data here (CSV, Excel, or PDF). Not sure what to use? Click "
    "<b>'Use Sample Dataset'</b> below to try the dashboard instantly with realistic example data."
)

col1, col2 = st.columns([2, 1])

with col1:
    uploaded_file = st.file_uploader(
        "Upload a CSV, Excel, or PDF file",
        type=["csv", "xlsx", "xls", "pdf"],
        help="Your file should have one row per transaction, with columns like CustomerID, Age, "
             "TransactionAmount, Fraud, etc. PDF statements with a transaction table are also supported."
    )

with col2:
    st.write("")
    st.write("")
    use_sample = st.button("Use Sample Dataset", width="stretch", type="primary")

with st.expander("What columns does my file need?"):
    st.markdown("Your file should ideally contain these columns (we'll guide you if anything's off):")
    st.code(", ".join(REQUIRED_COLUMNS))
    st.caption(
        "Optional but useful: TransactionID, DeviceUsed, PreviousFraudHistory, DailyTransactionCount. "
        "If these are missing, we'll fill in sensible defaults automatically. For PDF files, we look "
        "for a table on each page and try to match its column headers to this list automatically."
    )

raw_df = None

if use_sample:
    sample_path = os.path.join(os.path.dirname(__file__), "..", "data", "sample_banking_transactions.csv")
    raw_df = pd.read_csv(sample_path)
    st.session_state["dataset_source"] = "Sample Dataset"
elif uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".csv"):
            raw_df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(".pdf"):
            file_bytes = uploaded_file.read()
            extracted_df, pdf_info = extract_tables_from_pdf(file_bytes)
            if extracted_df is None:
                st.error(
                    "We couldn't find a data table in that PDF. PDF support works best with "
                    "statements that contain a clear transaction table (rows and columns), not "
                    "scanned images of text."
                )
            else:
                raw_df = auto_map_columns(extracted_df)
                # Columns from a PDF table are extracted as text; convert numeric-looking ones.
                for col in raw_df.columns:
                    converted = pd.to_numeric(raw_df[col], errors="coerce")
                    if converted.notna().mean() > 0.8:
                        raw_df[col] = converted
                st.info(
                    f"Extracted {pdf_info['rows_extracted']:,} rows from {pdf_info['pages']} "
                    f"page(s) of the PDF."
                )
        else:
            raw_df = pd.read_excel(uploaded_file)
        if raw_df is not None:
            st.session_state["dataset_source"] = uploaded_file.name
    except Exception as e:
        st.error(f"We couldn't read that file. Details: {e}")

if raw_df is not None:
    is_valid, missing = validate_columns(raw_df)
    if not is_valid:
        st.error(
            f"Your file is missing these required columns: **{', '.join(missing)}**. "
            "Please check your file and try again, or use the sample dataset instead."
        )
    else:
        raw_df = ensure_optional_columns(raw_df)
        st.session_state["raw_df"] = raw_df
        st.success(f"Loaded **{st.session_state['dataset_source']}** successfully.")

if "raw_df" in st.session_state:
    df = st.session_state["raw_df"]

    st.markdown("---")
    st.markdown("### Dataset Overview")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        kpi_card("Rows", f"{df.shape[0]:,}", icon="📄")
    with m2:
        kpi_card("Columns", f"{df.shape[1]:,}", icon="🗂️")
    with m3:
        kpi_card("Missing values", f"{int(df.isna().sum().sum()):,}", icon="❓")
    with m4:
        kpi_card("Duplicate rows", f"{int(df.duplicated().sum()):,}", icon="🧬")

    st.markdown("### Preview (first 10 rows)")
    st.dataframe(df.head(10), width="stretch")

    with st.expander("Column details (data types)"):
        col_info = pd.DataFrame({
            "Column": df.columns,
            "Data Type": df.dtypes.astype(str).values,
            "Missing Values": df.isna().sum().values,
            "Unique Values": [df[c].nunique() for c in df.columns]
        })
        st.dataframe(col_info, width="stretch", hide_index=True)

    st.markdown("---")
    st.info("Your data is loaded. Head to the **Preprocessing** page next to clean it up.")
    st.page_link("pages/2_Preprocessing.py", label="Continue to Preprocessing")
else:
    st.info("No dataset loaded yet. Upload a file above or click 'Use Sample Dataset' to get started.")
