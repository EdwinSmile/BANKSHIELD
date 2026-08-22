import streamlit as st
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "utils"))
from ui_helpers import theme_picker

st.set_page_config(
    page_title="BankShield | Fraud Detection Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

home = st.Page("pages/0_Home.py", title="Home", default=True)
dataset = st.Page("pages/1_Dataset.py", title="Dataset")
preprocessing = st.Page("pages/2_Preprocessing.py", title="Preprocessing")
exploration = st.Page("pages/3_Exploration.py", title="Data Exploration")
fraud_detection = st.Page("pages/4_Fraud_Detection.py", title="Fraud Detection")
customer_risk = st.Page("pages/5_Customer_Risk.py", title="Customer Risk")
reports = st.Page("pages/6_Reports.py", title="Reports")

st.sidebar.markdown(
    "<div style='display:flex;align-items:center;gap:10px;padding:4px 0 2px 0;'>"
    "<div style='width:32px;height:32px;border-radius:9px;background:#22C55E;"
    "display:flex;align-items:center;justify-content:center;font-size:16px;'>🛡️</div>"
    "<div style='font-size:19px;font-weight:800;'>BankShield</div>"
    "</div>",
    unsafe_allow_html=True,
)
st.sidebar.caption("Banking Fraud Detection & Customer Risk Dashboard")
st.sidebar.markdown("---")

pg = st.navigation(
    [home, dataset, preprocessing, exploration, fraud_detection, customer_risk, reports],
    position="sidebar"
)

st.sidebar.markdown("---")
theme_picker()

# Each page injects the themed CSS itself (via inject_css), so the selected page
# below applies styling — no need to inject it a second time here.
pg.run()
